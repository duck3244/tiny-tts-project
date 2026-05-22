#!/usr/bin/env python3
"""
TTS Engine - 공통 음성 합성 엔진 모듈
모델 로딩, 로마자 변환, 음성 생성 로직을 통합 관리
"""

import torch
from transformers import VitsModel, VitsTokenizer
import soundfile as sf

try:
    from uroman import Uroman
    UROMAN_AVAILABLE = True
except ImportError:
    UROMAN_AVAILABLE = False

MAX_TEXT_LENGTH = 500

# uroman 로마자 변환이 필요한 모델 (tokenizer.is_uroman 플래그가
# 설정돼 있지 않은 체크포인트를 보완하기 위한 명시 목록)
UROMAN_REQUIRED_MODELS = {
    "Matthijs/mms-tts-kor",
    "facebook/mms-tts-kor",
}


class TTSEngine:
    """TTS 음성 합성 엔진"""

    def __init__(self, model_name="Matthijs/mms-tts-kor", device=None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model_name = model_name
        self.model = VitsModel.from_pretrained(model_name)
        self.tokenizer = VitsTokenizer.from_pretrained(model_name)
        self.model.to(self.device)
        self.sample_rate = self.model.config.sampling_rate

        # 이 모델이 uroman 로마자 변환을 필요로 하는지 판단
        # (tokenizer 플래그 우선, 누락 시 명시 목록으로 보완)
        self.needs_uroman = bool(
            getattr(self.tokenizer, "is_uroman", False)
        ) or model_name in UROMAN_REQUIRED_MODELS

        if UROMAN_AVAILABLE and self.needs_uroman:
            self.uroman = Uroman()
        else:
            self.uroman = None

    def romanize(self, text):
        """텍스트를 로마자로 변환 (필요한 모델에 한해 적용)"""
        if self.uroman:
            return self.uroman.romanize_string(text)
        return text

    def generate(self, text, output_path=None):
        """
        텍스트를 음성으로 변환

        Args:
            text: 변환할 텍스트
            output_path: 저장할 파일 경로 (None이면 저장하지 않음)

        Returns:
            numpy array of waveform data

        Raises:
            ValueError: 텍스트가 비어있거나 너무 긴 경우
        """
        if not text or not text.strip():
            raise ValueError("텍스트가 비어있습니다.")

        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(f"텍스트가 너무 깁니다 (최대 {MAX_TEXT_LENGTH}자).")

        romanized = self.romanize(text)

        inputs = self.tokenizer(romanized, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            output = self.model(**inputs).waveform

        waveform = output.squeeze().cpu().numpy()

        if output_path:
            sf.write(output_path, waveform, self.sample_rate)

        return waveform

    def get_device_info(self):
        """디바이스 및 엔진 상태 정보 반환"""
        info = {
            "device": self.device,
            "model_name": self.model_name,
            "sample_rate": self.sample_rate,
            "uroman": self.uroman is not None,
            "needs_uroman": self.needs_uroman,
        }
        if self.device == "cuda":
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["vram_gb"] = f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}"
        return info
