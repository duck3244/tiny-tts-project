#!/usr/bin/env python3
"""
Web Interface for Tiny TTS
Flask 기반 웹 인터페이스
Matthijs/mms-tts-kor 모델 사용
"""

from flask import Flask, render_template_string, request, send_file, jsonify
import torch
from transformers import VitsModel, VitsTokenizer
import soundfile as sf
import os
from datetime import datetime
import tempfile

# uroman 사용 가능 여부 확인
try:
    from uroman import Uroman
    UROMAN_AVAILABLE = True
except ImportError:
    UROMAN_AVAILABLE = False

app = Flask(__name__)

# TTS 모델 전역 변수
tts_model = None
tts_tokenizer = None
device = None
uroman_instance = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tiny TTS Web Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 32px;
        }
        
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .info-box {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        
        .info-box p {
            margin: 5px 0;
            color: #555;
            font-size: 14px;
        }
        
        label {
            display: block;
            margin-bottom: 10px;
            color: #555;
            font-weight: 600;
        }
        
        select, textarea {
            width: 100%;
            padding: 12px;
            margin-bottom: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea {
            resize: vertical;
            min-height: 120px;
            font-family: inherit;
        }
        
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        #result {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        
        #result.show {
            display: block;
        }
        
        .success {
            color: #28a745;
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        .error {
            color: #dc3545;
            font-weight: 600;
        }
        
        audio {
            width: 100%;
            margin-top: 10px;
        }
        
        .loading {
            text-align: center;
            color: #667eea;
            font-weight: 600;
            display: none;
        }
        
        .loading.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Tiny TTS</h1>
        <p class="subtitle">Text-to-Speech Web Interface</p>
        
        <div class="info-box">
            <p><strong>디바이스:</strong> {{ device }}</p>
            <p><strong>모델:</strong> {{ model_name }}</p>
        </div>
        
        <form id="ttsForm">
            <label for="language">언어 선택:</label>
            <select id="language" name="language">
                <option value="Matthijs/mms-tts-kor" selected>한국어 (Korean)</option>
                <option value="facebook/mms-tts-eng">영어 (English)</option>
                <option value="facebook/mms-tts-jpn">일본어 (Japanese)</option>
                <option value="facebook/mms-tts-cmn">중국어 (Chinese)</option>
                <option value="facebook/mms-tts-spa">스페인어 (Spanish)</option>
                <option value="facebook/mms-tts-fra">프랑스어 (French)</option>
            </select>
            
            <label for="text">변환할 텍스트:</label>
            <textarea id="text" name="text" placeholder="여기에 텍스트를 입력하세요..." required></textarea>
            
            <button type="submit" id="submitBtn">🎵 음성 생성</button>
        </form>
        
        <div class="loading" id="loading">
            <p>음성 생성 중... ⏳</p>
        </div>
        
        <div id="result"></div>
    </div>
    
    <script>
        document.getElementById('ttsForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const text = document.getElementById('text').value;
            const language = document.getElementById('language').value;
            const submitBtn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            
            // UI 업데이트
            submitBtn.disabled = true;
            loading.classList.add('show');
            result.classList.remove('show');
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text, language })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    result.innerHTML = `
                        <p class="success">✅ 음성 생성 완료!</p>
                        <audio controls autoplay>
                            <source src="/download/${data.filename}" type="audio/wav">
                            Your browser does not support the audio element.
                        </audio>
                    `;
                    result.classList.add('show');
                } else {
                    result.innerHTML = `<p class="error">❌ 오류: ${data.error}</p>`;
                    result.classList.add('show');
                }
            } catch (error) {
                result.innerHTML = `<p class="error">❌ 오류: ${error.message}</p>`;
                result.classList.add('show');
            } finally {
                submitBtn.disabled = false;
                loading.classList.remove('show');
            }
        });
    </script>
</body>
</html>
"""

def initialize_model(model_name="Matthijs/mms-tts-kor"):
    """TTS 모델 초기화"""
    global tts_model, tts_tokenizer, device, uroman_instance
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"디바이스: {device}")
    
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    
    print(f"모델 로딩: {model_name}")
    tts_model = VitsModel.from_pretrained(model_name)
    tts_tokenizer = VitsTokenizer.from_pretrained(model_name)
    tts_model.to(device)
    
    # uroman 초기화
    if UROMAN_AVAILABLE:
        uroman_instance = Uroman()
        print("✅ uroman 초기화 완료")
    else:
        uroman_instance = None
        print("⚠️ uroman 미설치")
    
    print("모델 로딩 완료!")

@app.route('/')
def index():
    """메인 페이지"""
    model_name = "Matthijs/mms-tts-kor" if tts_model is None else "Loaded"
    return render_template_string(HTML_TEMPLATE, device=device, model_name=model_name)

@app.route('/generate', methods=['POST'])
def generate():
    """음성 생성 API"""
    global tts_model, tts_tokenizer, device, uroman_instance
    
    try:
        data = request.json
        text = data.get('text', '')
        language = data.get('language', 'Matthijs/mms-tts-kor')
        
        if not text:
            return jsonify({'success': False, 'error': '텍스트가 비어있습니다.'})
        
        # 모델이 변경되었으면 다시 로드
        current_model = getattr(tts_model, 'name_or_path', None)
        if current_model != language:
            print(f"모델 변경: {language}")
            initialize_model(language)
        
        # 한국어 텍스트를 로마자로 변환
        if uroman_instance:
            romanized_text = uroman_instance.romanize_string(text)
            print(f"Romanized: {romanized_text}")
        else:
            romanized_text = text
        
        # 토큰화
        inputs = tts_tokenizer(romanized_text, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # 음성 생성
        with torch.no_grad():
            output = tts_model(**inputs).waveform
        
        # 임시 파일로 저장
        waveform = output.squeeze().cpu().numpy()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tts_{timestamp}.wav"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        
        sf.write(filepath, waveform, 16000)
        
        return jsonify({'success': True, 'filename': filename})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download(filename):
    """생성된 음성 파일 다운로드"""
    filepath = os.path.join(tempfile.gettempdir(), filename)
    return send_file(filepath, mimetype='audio/wav')

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Tiny TTS Web Interface (Korean)")
    parser.add_argument('-p', '--port', type=int, default=5000, help='포트 번호')
    parser.add_argument('-m', '--model', type=str, default='Matthijs/mms-tts-kor', help='초기 모델')
    args = parser.parse_args()
    
    # 모델 초기화
    initialize_model(args.model)
    
    print(f"\n웹 서버 시작: http://localhost:{args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=False)
