#!/usr/bin/env python3
"""
Tiny TTS Text-to-Speech Application
Ubuntu 22.04 + RTX 4060 8GB 환경용
Matthijs/mms-tts-kor 모델 사용
"""

import argparse
from tts_engine import TTSEngine


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
        "--cpu",
        action="store_true",
        help="CPU 모드 강제 사용"
    )

    args = parser.parse_args()

    device = "cpu" if args.cpu else None

    print(f"모델 로딩 중: {args.model}")
    engine = TTSEngine(model_name=args.model, device=device)

    info = engine.get_device_info()
    print(f"디바이스 사용: {info['device']}")
    if "gpu_name" in info:
        print(f"GPU: {info['gpu_name']}")
        print(f"사용 가능한 VRAM: {info['vram_gb']} GB")
    if info["uroman"]:
        print("✅ uroman 초기화 완료")
    else:
        print("⚠️ uroman 없이 실행 (한국어 처리 제한적)")
    print("모델 로딩 완료!")

    print(f"\n텍스트 변환 중: '{args.text}'")
    if engine.uroman:
        print(f"Romanized: '{engine.romanize(args.text)}'")
    engine.generate(args.text, output_path=args.output)
    print(f"음성 파일 저장 완료: {args.output}")

    print("\n변환 완료!")


if __name__ == "__main__":
    main()
