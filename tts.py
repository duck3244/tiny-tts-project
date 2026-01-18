#!/usr/bin/env python3
"""
Tiny TTS Text-to-Speech Application
Ubuntu 22.04 + RTX 4060 8GB 환경용
Matthijs/mms-tts-kor 모델 사용
"""

import torch
import torchaudio
from transformers import VitsModel, VitsTokenizer
import soundfile as sf
import argparse
import os
from pathlib import Path

# uroman 사용 가능 여부 확인
try:
    from uroman import Uroman
    UROMAN_AVAILABLE = True
except ImportError:
    UROMAN_AVAILABLE = False
    print("경고: uroman 패키지가 설치되지 않았습니다.")
    print("한국어 텍스트 처리를 위해 uroman 설치를 권장합니다:")
    print("  pip install uroman")


class TinyTTS:
    def __init__(self, model_name="Matthijs/mms-tts-kor", device=None):
        """
        Tiny TTS 초기화
        
        Args:
            model_name: 사용할 TTS 모델 (기본값: Matthijs/mms-tts-kor)
            device: 사용할 디바이스 (None이면 자동 선택)
        """
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"디바이스 사용: {self.device}")
        
        # CUDA 사용 시 메모리 정보 출력
        if self.device == "cuda":
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"사용 가능한 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        
        print(f"모델 로딩 중: {model_name}")
        self.model = VitsModel.from_pretrained(model_name)
        self.tokenizer = VitsTokenizer.from_pretrained(model_name)
        self.model.to(self.device)
        
        # uroman 초기화
        if UROMAN_AVAILABLE:
            self.uroman = Uroman()
            print("✅ uroman 초기화 완료")
        else:
            self.uroman = None
            print("⚠️ uroman 없이 실행 (한국어 처리 제한적)")
        
        print("모델 로딩 완료!")
    
    def text_to_speech(self, text, output_path="output.wav", sample_rate=16000):
        """
        텍스트를 음성으로 변환
        
        Args:
            text: 변환할 텍스트 (한국어 텍스트 입력 가능)
            output_path: 저장할 파일 경로
            sample_rate: 샘플링 레이트
        
        Note:
            Matthijs/mms-tts-kor 모델은 uroman을 통한 romanization이 필요합니다.
        """
        print(f"\n텍스트 변환 중: '{text}'")
        
        # 한국어 텍스트를 로마자로 변환
        if self.uroman:
            romanized_text = self.uroman.romanize_string(text)
            print(f"Romanized: '{romanized_text}'")
        else:
            # uroman이 없으면 원본 텍스트 사용 (영어 등)
            romanized_text = text
            print("⚠️ uroman 없음 - 원본 텍스트 사용")
        
        # 텍스트 토큰화
        inputs = self.tokenizer(romanized_text, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # 음성 생성
        with torch.no_grad():
            output = self.model(**inputs).waveform
        
        # CPU로 이동하고 numpy 배열로 변환
        waveform = output.squeeze().cpu().numpy()
        
        # 파일로 저장
        sf.write(output_path, waveform, sample_rate)
        print(f"음성 파일 저장 완료: {output_path}")
        
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Tiny TTS - Text to Speech Converter (Korean)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  python tts.py "안녕하세요, 반갑습니다."
  python tts.py "테스트 음성입니다" --output test.wav
  python tts.py "한국어 텍스트 음성 변환" --model Matthijs/mms-tts-kor
        """
    )
    
    parser.add_argument(
        "text",
        type=str,
        help="변환할 텍스트"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output.wav",
        help="출력 파일 경로 (기본값: output.wav)"
    )
    
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="Matthijs/mms-tts-kor",
        help="사용할 TTS 모델 (기본값: Matthijs/mms-tts-kor)"
    )
    
    parser.add_argument(
        "-s", "--sample-rate",
        type=int,
        default=16000,
        help="샘플링 레이트 (기본값: 16000)"
    )
    
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="CPU 모드 강제 사용"
    )
    
    args = parser.parse_args()
    
    # 디바이스 설정
    device = "cpu" if args.cpu else None
    
    # TTS 초기화
    tts = TinyTTS(model_name=args.model, device=device)
    
    # 텍스트를 음성으로 변환
    tts.text_to_speech(
        text=args.text,
        output_path=args.output,
        sample_rate=args.sample_rate
    )
    
    print("\n변환 완료!")


if __name__ == "__main__":
    main()
