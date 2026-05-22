#!/usr/bin/env python3
"""
Interactive Tiny TTS Application
실시간 텍스트 입력을 받아 음성으로 변환
Matthijs/mms-tts-kor 모델 사용
"""

import os
import argparse
from datetime import datetime
from tts_engine import TTSEngine


class InteractiveTTS:
    def __init__(self, model_name="Matthijs/mms-tts-kor"):
        """대화형 TTS 초기화"""
        print("=" * 60)
        print("Interactive Tiny TTS (Korean)")
        print("=" * 60)

        print(f"\n모델 로딩 중: {model_name}")
        self.engine = TTSEngine(model_name=model_name)

        info = self.engine.get_device_info()
        print(f"디바이스: {info['device']}")
        if "gpu_name" in info:
            print(f"GPU: {info['gpu_name']}")
            print(f"VRAM: {info['vram_gb']} GB")
        if info["uroman"]:
            print("✅ uroman 초기화 완료")
        elif info["needs_uroman"]:
            print("⚠️ uroman 미설치 - 'pip install uroman' 실행 필요")
        else:
            print("ℹ️ 이 모델은 uroman 로마자 변환이 필요하지 않습니다")

        self.output_dir = "outputs"
        os.makedirs(self.output_dir, exist_ok=True)

        print("모델 로딩 완료!\n")

    def generate_speech(self, text, custom_filename=None):
        """텍스트를 음성으로 변환하고 저장"""
        if not text.strip():
            print("텍스트가 비어있습니다.")
            return None

        if custom_filename:
            filename = custom_filename if custom_filename.endswith('.wav') else f"{custom_filename}.wav"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{timestamp}.wav"

        output_path = os.path.join(self.output_dir, filename)

        print(f"\n🎤 변환 중: '{text}'")
        if self.engine.uroman:
            print(f"   Romanized: '{self.engine.romanize(text)}'")

        self.engine.generate(text, output_path=output_path)
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

                self.generate_speech(text)

            except KeyboardInterrupt:
                print("\n\n프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                continue


def main():
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
