# Tiny TTS Project

Ubuntu 22.04 + RTX 4060 8GB 환경에서 사용하는 Text-to-Speech 프로젝트입니다.

**기본 모델**: `Matthijs/mms-tts-kor` (한국어 TTS)

## 🚀 빠른 시작

```bash
# 1. 패키지 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers>=4.33.0 soundfile scipy flask uroman

# 2. 기본 사용 (CLI)
python tts.py "안녕하세요, 반갑습니다."

# 3. 웹 인터페이스
python web_tts.py
# 브라우저에서 http://localhost:5000 접속
```
## 🎯 RTX 4060 8GB 호환성

✅ **완벽하게 동작 가능**

- **모델 크기**: ~200-400MB (VITS 아키텍처)
- **예상 VRAM 사용량**: 1-2GB
- **RTX 4060 8GB**: 충분한 여유 공간 (6-7GB 남음)
- **추론 속도**: 실시간보다 빠름

## 시스템 요구사항

- Ubuntu 22.04
- NVIDIA RTX 4060 8GB (CUDA 지원)
- Python 3.8 이상
- CUDA Toolkit 11.8 이상 (GPU 사용 시)

## 설치 방법

### 1. Python 가상환경 생성 (권장)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. 의존성 패키지 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. PyTorch CUDA 버전 설치 (GPU 사용 시)

```bash
# CUDA 11.8용
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 또는 CUDA 12.1용
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 4. uroman 설치 (한국어 처리 필수!)

```bash
pip install uroman
```

**중요**: `Matthijs/mms-tts-kor` 모델은 한국어를 로마자로 변환하기 위해 uroman이 필요합니다.

## 사용 방법

### 1. 기본 사용법 (단일 텍스트 변환)

```bash
python tts.py "안녕하세요, 반갑습니다."
```

출력 파일: `output.wav`

### 2. 출력 파일명 지정

```bash
python tts.py "한국어 음성 변환 테스트입니다." -o greeting.wav
```

### 3. 다른 언어 모델 사용

```bash
# 영어 모델
python tts.py "Hello, how are you?" --model facebook/mms-tts-eng

# 일본어 모델
python tts.py "こんにちは" --model facebook/mms-tts-jpn

# 중국어 모델
python tts.py "你好" --model facebook/mms-tts-cmn
```

### 4. 대화형 모드

```bash
python interactive_tts.py
```

대화형 모드에서는 텍스트를 입력하면 실시간으로 음성 파일이 생성됩니다.
생성된 파일은 `outputs/` 디렉토리에 저장됩니다.

### 5. 웹 인터페이스 모드 🌐

```bash
python web_tts.py
```

웹 브라우저에서 사용할 수 있는 인터페이스를 제공합니다.

**접속 방법:**
```
http://localhost:5000
```

**기능:**
- 브라우저에서 직접 텍스트 입력
- 여러 언어 모델 간 쉬운 전환
- 즉시 재생 가능한 오디오 플레이어
- 다운로드 기능

**포트 변경:**
```bash
python web_tts.py --port 8080
```

**다른 모델로 시작:**
```bash
python web_tts.py --model facebook/mms-tts-eng
```

**외부 접속 (같은 네트워크):**

서버는 기본적으로 모든 네트워크 인터페이스에서 실행되므로, 같은 네트워크의 다른 기기에서도 접속 가능합니다:

1. 서버 IP 확인:
   ```bash
   hostname -I
   ```

2. 다른 기기에서 접속:
   ```
   http://192.168.x.x:5000
   ```

### 6. CPU 모드 강제 사용

```bash
python tts.py "Test text" --cpu
```

## 지원 언어 모델

Meta의 MMS (Massively Multilingual Speech) 모델을 사용합니다:

- **한국어**: `Matthijs/mms-tts-kor` (기본값)
- **영어**: `facebook/mms-tts-eng`
- **일본어**: `facebook/mms-tts-jpn`
- **중국어**: `facebook/mms-tts-cmn`
- **스페인어**: `facebook/mms-tts-spa`
- **프랑스어**: `facebook/mms-tts-fra`
- **독일어**: `facebook/mms-tts-deu`

전체 지원 언어 목록: https://huggingface.co/facebook/mms-tts

## 파일 구조

```
tiny-tts-project/
├── requirements.txt            # Python 패키지 의존성
├── tts.py                      # 메인 TTS 스크립트 (CLI)
├── interactive_tts.py          # 대화형 TTS 스크립트
├── web_tts.py                  # 웹 인터페이스 TTS 스크립트
├── README.md                   # 이 파일
├── TROUBLESHOOTING.md          # 문제 해결 가이드
├── RTX_4060_COMPATIBILITY.md   # RTX 4060 호환성 상세 분석
└── outputs/                    # 생성된 음성 파일 저장 (자동 생성)
```

## GPU 메모리 사용량

- 모델 로딩: 약 400-500 MB
- 추론 시: 약 1-2 GB
- RTX 4060 8GB에서 여유롭게 실행 가능

## 문제 해결

### CUDA 오류 발생 시

```bash
# CUDA 버전 확인
nvidia-smi

# PyTorch CUDA 확인
python -c "import torch; print(torch.cuda.is_available())"
```

### 모델 다운로드 오류 시

모델은 처음 실행 시 자동으로 다운로드됩니다. 
네트워크 문제가 있다면 Hugging Face 계정으로 로그인:

```bash
pip install huggingface-hub
huggingface-cli login
```

### 메모리 부족 오류 시

CPU 모드로 전환:

```bash
python tts.py "Your text" --cpu
```

### 웹 인터페이스 문제 해결

**포트가 이미 사용 중인 경우:**
```bash
# 다른 포트 사용
python web_tts.py --port 8080
```

**브라우저 연결 안 될 때:**
```bash
# 방화벽 포트 열기 (Ubuntu)
sudo ufw allow 5000

# 서버 실행 확인
ps aux | grep web_tts.py
```

**음성 생성 실패 시:**
- 브라우저 개발자 도구(F12) → Console 탭 확인
- 서버 터미널에서 오류 메시지 확인
- uroman이 설치되어 있는지 확인: `pip list | grep uroman`

### uroman 관련 오류

한국어 텍스트 처리 시 오류 발생:

```bash
# uroman 설치
pip install uroman

# 설치 확인
python -c "from uroman import Uroman; print('OK')"
```

더 자세한 문제 해결은 `TROUBLESHOOTING.md` 파일을 참고하세요.

## 예제

### 커맨드 라인 (CLI)

```bash
# 한국어 텍스트 변환
python tts.py "안녕하세요. 텍스트 음성 변환 프로젝트입니다." -o welcome.wav

# 긴 문장 변환
python tts.py "인공지능 기술의 발전으로 음성 합성 기술이 크게 향상되었습니다." -o korean_test.wav

# 대화형 모드로 여러 문장 변환
python interactive_tts.py
```

### 웹 인터페이스

```bash
# 웹 서버 시작
python web_tts.py

# 브라우저에서 http://localhost:5000 접속 후:
# 1. 텍스트 입력: "안녕하세요, 반갑습니다."
# 2. "🎵 음성 생성" 버튼 클릭
# 3. 오디오 플레이어에서 즉시 재생
```

### 다양한 언어 테스트

```bash
# 영어
python tts.py "Hello, how are you today?" --model facebook/mms-tts-eng -o english.wav

# 일본어
python tts.py "こんにちは、元気ですか。" --model facebook/mms-tts-jpn -o japanese.wav

# 중국어
python tts.py "你好，很高兴见到你。" --model facebook/mms-tts-cmn -o chinese.wav
```

## 사용 팁

### 웹 인터페이스 활용

1. **여러 언어 실험**: 드롭다운에서 언어를 바꿔가며 같은 문장을 다른 언어로 변환
2. **긴 텍스트**: 여러 문단도 한 번에 처리 가능
3. **즉시 재생**: 생성된 오디오를 바로 들어볼 수 있어 반복 테스트에 유용

### 백그라운드 실행 (서버)

```bash
# nohup으로 백그라운드 실행
nohup python web_tts.py > tts.log 2>&1 &

# 로그 확인
tail -f tts.log

# 프로세스 종료
pkill -f web_tts.py
```

### GPU 사용률 모니터링

```bash
# 실시간 GPU 모니터링 (다른 터미널에서)
watch -n 1 nvidia-smi
```

## 라이선스

이 프로젝트는 교육 및 개인 용도로 자유롭게 사용할 수 있습니다.
사용된 모델(MMS-TTS)은 Meta AI의 라이선스를 따릅니다.

## 참고 자료

- [MMS-TTS 모델](https://huggingface.co/facebook/mms-tts)
- [Transformers 문서](https://huggingface.co/docs/transformers)
- [PyTorch 설치 가이드](https://pytorch.org/get-started/locally/)