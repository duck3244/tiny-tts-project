#!/usr/bin/env python3
"""
Web Interface for Tiny TTS
Flask 기반 웹 인터페이스
Matthijs/mms-tts-kor 모델 사용
"""

from flask import Flask, render_template, request, send_file, jsonify, abort
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import tempfile
import threading
from tts_engine import TTSEngine

app = Flask(__name__)

engine = None
engine_lock = threading.Lock()


def initialize_engine(model_name="Matthijs/mms-tts-kor"):
    """TTS 엔진 초기화"""
    global engine
    engine = TTSEngine(model_name=model_name)
    info = engine.get_device_info()
    print(f"디바이스: {info['device']}")
    if "gpu_name" in info:
        print(f"GPU: {info['gpu_name']}")
    if info["uroman"]:
        print("✅ uroman 초기화 완료")
    else:
        print("⚠️ uroman 미설치")
    print("모델 로딩 완료!")


@app.route('/')
def index():
    """메인 페이지"""
    info = engine.get_device_info() if engine else {}
    return render_template(
        'index.html',
        device=info.get('device', 'N/A'),
        model_name=info.get('model_name', 'N/A'),
    )


@app.route('/generate', methods=['POST'])
def generate():
    """음성 생성 API"""
    global engine

    try:
        data = request.json
        text = data.get('text', '')
        language = data.get('language', 'Matthijs/mms-tts-kor')

        if not text:
            return jsonify({'success': False, 'error': '텍스트가 비어있습니다.'})

        with engine_lock:
            if engine.model_name != language:
                print(f"모델 변경: {language}")
                initialize_engine(language)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{timestamp}.wav"
            filepath = os.path.join(tempfile.gettempdir(), filename)

            engine.generate(text, output_path=filepath)

        return jsonify({'success': True, 'filename': filename})

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/download/<filename>')
def download(filename):
    """생성된 음성 파일 다운로드"""
    filename = secure_filename(filename)
    if not filename or not filename.endswith('.wav'):
        abort(400)
    filepath = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.isfile(filepath):
        abort(404)
    return send_file(filepath, mimetype='audio/wav')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Tiny TTS Web Interface (Korean)")
    parser.add_argument('-p', '--port', type=int, default=5000, help='포트 번호')
    parser.add_argument('-m', '--model', type=str, default='Matthijs/mms-tts-kor', help='초기 모델')
    args = parser.parse_args()

    initialize_engine(args.model)

    print(f"\n웹 서버 시작: http://localhost:{args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=False)
