#!/usr/bin/env python3
"""
Interactive Tiny TTS Application
실시간 텍스트 입력을 받아 음성으로 변환
Matthijs/mms-tts-kor 모델 사용
"""

import torch
import torchaudio
from transformers import VitsModel, VitsTokenizer
import soundfile as sf
import os
from datetime import datetime

# uroman 사용 가능 여부 확인
try:
    from uroman import Uroman
    UROMAN_AVAILABLE = True
except ImportError:
    UROMAN_AVAILABLE = False


class InteractiveTTS:
    def __init__(self, model_name="Matthijs/mms-tts-kor"):
        """대화형 TTS 초기화"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print("=" * 60)
        print("Interactive Tiny TTS (Korean)")
        print("=" * 60)
        print(f"디바이스: {self.device}")
        
        if self.device == "cuda":
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        
        print(f"\n모델 로딩 중: {model_name}")
        self.model = VitsModel.from_pretrained(model_name)
        self.tokenizer = VitsTokenizer.from_pretrained(model_name)
        self.model.to(self.device)
        
        # uroman 초기화
        if UROMAN_AVAILABLE:
            self.uroman = Uroman()
            print("✅ uroman 초기화 완료")
        else:
            self.uroman = None
            print("⚠️ uroman 미설치 - 'pip install uroman' 실행 필요")
        
        # 출력 디렉토리 생성
        self.output_dir = "outputs"
        os.makedirs(self.output_dir, exist_ok=True)
        
        print("모델 로딩 완료!\n")
    
    def generate_speech(self, text, custom_filename=None):
        """텍스트를 음성으로 변환하고 저장"""
        if not text.strip():
            print("텍스트가 비어있습니다.")
            return None
        
        # 파일명 생성
        if custom_filename:
            filename = custom_filename if custom_filename.endswith('.wav') else f"{custom_filename}.wav"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{timestamp}.wav"
        
        output_path = os.path.join(self.output_dir, filename)
        
        print(f"\n🎤 변환 중: '{text}'")
        
        # 한국어 텍스트를 로마자로 변환
        if self.uroman:
            romanized_text = self.uroman.romanize_string(text)
            print(f"   Romanized: '{romanized_text}'")
        else:
            romanized_text = text
        
        # 토큰화
        inputs = self.tokenizer(romanized_text, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # 음성 생성
        with torch.no_grad():
            output = self.model(**inputs).waveform
        
        # 저장
        waveform = output.squeeze().cpu().numpy()
        sf.write(output_path, waveform, 16000)
        
        print(f"✅ 저장 완료: {output_path}")
        return output_path
    
    def run(self):
        """대화형 모드 실행"""
        print("=" * 60)
        print("명령어:")
        print("  - 텍스트 입력 후 Enter: 음성 생성")
        print("  - 'quit' 또는 'exit': 종료")
        print("  - 'help': 도움말 표시")
        print("=" * 60)
        print()
        
        while True:
            try:
                text = input("텍스트 입력 > ").strip()
                
                if not text:
                    continue
                
                # 명령어 처리
                if text.lower() in ['quit', 'exit', 'q']:
                    print("\n프로그램을 종료합니다.")
                    break
                
                elif text.lower() == 'help':
                    print("\n도움말:")
                    print("  1. 변환할 텍스트를 입력하세요")
                    print("  2. Enter를 누르면 음성이 생성됩니다")
                    print("  3. 생성된 파일은 'outputs' 폴더에 저장됩니다")
                    print("  4. 'quit' 또는 'exit'를 입력하면 종료됩니다\n")
                    continue
                
                # 음성 생성
                self.generate_speech(text)
                
            except KeyboardInterrupt:
                print("\n\n프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                continue


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive Tiny TTS (Korean)")
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="Matthijs/mms-tts-kor",
        help="사용할 TTS 모델 (기본값: Matthijs/mms-tts-kor)"
    )
    
    args = parser.parse_args()
    
    tts = InteractiveTTS(model_name=args.model)
    tts.run()


if __name__ == "__main__":
    main()
