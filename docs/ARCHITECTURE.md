# Tiny TTS — 아키텍처 문서

## 1. 개요

Tiny TTS는 Meta의 MMS(Massively Multilingual Speech) VITS 모델을 사용해
텍스트를 음성으로 변환하는 다국어 TTS 애플리케이션이다.

- **백엔드**: FastAPI 기반 REST API + TTS 추론 엔진
- **프론트엔드**: Vue 3 SPA (Vite + Tailwind CSS)
- **레거시**: 단일 파일 CLI / 대화형 / Flask 웹 스크립트 (현재는 보존용)
- **대상 환경**: Ubuntu 22.04 + NVIDIA RTX 4060 8GB (CUDA), CPU 폴백 지원

## 2. 전체 구성도

```
┌─────────────────────────────────────────────────────────────┐
│                          브라우저                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Vue 3 SPA (frontend/)                                │  │
│  │   App.vue ── TtsForm.vue ── HistoryList.vue           │  │
│  │      │           │                 │                  │  │
│  │      └───────── api.js ─────────────┘                  │  │
│  └───────────────────────┬───────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────┘
                           │  HTTP /api/*
                           │  (개발: Vite proxy :5173 → :8000)
                           │  (운영: dist/ 정적 서빙)
┌──────────────────────────▼──────────────────────────────────┐
│                  FastAPI 백엔드 (backend/app.py)             │
│   GET  /api/status        ── 디바이스·모델·언어 상태          │
│   POST /api/generate      ── 텍스트 → wav 생성               │
│   GET  /api/audio/{file}  ── 생성된 wav 반환                 │
│                           │                                  │
│                  ┌────────▼─────────┐                        │
│                  │  TTSEngine        │  (backend/tts_engine.py)│
│                  │   - 모델 로딩      │                        │
│                  │   - uroman 로마자  │                        │
│                  │   - 음성 합성      │                        │
│                  └────────┬─────────┘                        │
└───────────────────────────┼──────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
  HuggingFace Hub      PyTorch / CUDA      backend/outputs/
  (VITS 체크포인트)     (추론 실행)          (wav 파일 저장)
```

## 3. 계층 구조

### 3.1 프론트엔드 (`frontend/`)

| 파일 | 책임 |
|------|------|
| `index.html` | SPA 진입 HTML, `#app` 마운트 지점 |
| `src/main.js` | Vue 앱 부트스트랩 (`createApp(App).mount`) |
| `src/App.vue` | 루트 컴포넌트. 상태 조회, 생성 요청 오케스트레이션, 이력 관리 |
| `src/components/TtsForm.vue` | 언어 선택 + 텍스트 입력 폼, 입력 검증(최대 500자) |
| `src/components/HistoryList.vue` | 생성 이력 표시, 오디오 재생/다운로드 |
| `src/api.js` | 백엔드 호출 래퍼 (`fetchStatus`, `generateSpeech`, `audioUrl`) |
| `src/style.css` | Tailwind 디렉티브 |
| `vite.config.js` | Vite 설정, `/api` → `:8000` 개발 프록시 |

데이터 흐름은 단방향이다: `TtsForm`이 `generate` 이벤트를 emit → `App.vue`가
`api.js`를 통해 백엔드 호출 → 응답을 `history` 배열에 unshift → `HistoryList`가
props로 렌더링.

### 3.2 백엔드 (`backend/`)

| 파일 | 책임 |
|------|------|
| `app.py` | FastAPI 앱. 라우팅, 요청 검증, 엔진 수명주기, 파일 정리, 정적 서빙 |
| `tts_engine.py` | `TTSEngine` 클래스. 모델/토크나이저 로딩, 로마자 변환, 음성 합성 |
| `outputs/` | 생성된 wav 저장 디렉토리 (최대 `MAX_KEPT_FILES`=20개 유지) |
| `templates/index.html` | 레거시 Flask용 템플릿 |

#### app.py 의 주요 책임

- **모델 화이트리스트** (`ALLOWED_MODELS`): HF Hub에 존재가 검증된 모델만 허용.
  한국어/영어/스페인어/프랑스어 4종.
- **엔진 수명주기** (`lifespan`): 서버 기동 시 기본 모델(`Matthijs/mms-tts-kor`)
  사전 로딩.
- **동시성 제어** (`engine_lock`): TTS 추론은 `threading.Lock`으로 직렬화.
  단일 사용자 MVP 가정.
- **모델 전환** (`_load_engine`): 요청 언어가 현재 모델과 다르면 재로딩하고
  이전 모델 VRAM을 `torch.cuda.empty_cache()`로 회수.
- **출력 정리** (`_prune_outputs`): 생성 후 오래된 wav를 20개까지만 보존.
- **경로 탐색 방지** (`get_audio`): `os.path.basename` + `.wav` 확장자 검사.
- **정적 서빙**: `frontend/dist`가 존재하면 SPA를 루트에 마운트(운영 모드).

### 3.3 레거시 스크립트 (보존용)

| 파일 | 용도 |
|------|------|
| `backend/tts.py` | 단일 텍스트 → wav 변환 CLI |
| `backend/interactive_tts.py` | 대화형 REPL TTS |
| `backend/web_tts.py` | 구버전 Flask 웹 인터페이스 (현재 FastAPI `app.py`로 대체됨) |

## 4. API 명세

| 메서드 | 경로 | 요청 | 응답 |
|--------|------|------|------|
| `GET` | `/api/status` | — | `{ ready, device, model_name, sample_rate, uroman, needs_uroman, languages, gpu_name?, vram_gb? }` |
| `POST` | `/api/generate` | `{ text: str(1~500), language: str }` | `{ filename: str }` / `400` 검증 실패 |
| `GET` | `/api/audio/{filename}` | — | `audio/wav` 파일 / `404` 없음 |

## 5. 핵심 처리 흐름

### 5.1 음성 생성 (`POST /api/generate`)

1. Pydantic이 `text` 길이(1~500자)를 1차 검증.
2. `language`가 `ALLOWED_MODELS`에 있는지 확인 (없으면 400).
3. `engine_lock` 획득 — 추론 직렬화.
4. 현재 로딩된 모델과 요청 언어가 다르면 `_load_engine`으로 모델 교체.
5. 타임스탬프 기반 파일명 생성 (`tts_YYYYMMDD_HHMMSS_ffffff.wav`).
6. `TTSEngine.generate()` 호출:
   - 텍스트 공백/길이 재검증
   - uroman 필요 모델이면 로마자 변환
   - 토크나이즈 → 디바이스 이동 → `model()` 추론 → waveform 추출
   - `soundfile.write`로 wav 저장
7. `_prune_outputs`로 오래된 파일 정리.
8. `{ filename }` 반환.

### 5.2 로마자 변환 (uroman)

`Matthijs/mms-tts-kor` 등 일부 MMS 체크포인트는 토크나이저의 `is_uroman`
플래그가 누락돼 있다. `TTSEngine`은 토크나이저 플래그를 우선 보고, 누락 시
`UROMAN_REQUIRED_MODELS` 명시 목록으로 보완해 한국어 입력을 로마자로 변환한다.
`uroman` 패키지가 설치돼 있지 않으면 변환 없이 원문을 그대로 전달한다.

## 6. 실행 환경

### 개발 모드

```bash
# 백엔드 (터미널 1)
cd backend && uvicorn app:app --reload --port 8000

# 프론트엔드 (터미널 2)
cd frontend && npm run dev          # http://localhost:5173
```

Vite가 `/api` 요청을 `:8000`으로 프록시하므로 same-origin이 되어 CORS 불필요.
(`app.py`는 `localhost:5173` 직접 호출도 CORS로 추가 허용)

### 운영 모드

```bash
cd frontend && npm run build        # → frontend/dist/
cd backend && python app.py         # dist/ 를 루트에서 정적 서빙
```

## 7. 기술 스택

| 영역 | 기술 |
|------|------|
| 백엔드 프레임워크 | FastAPI, Uvicorn |
| ML 런타임 | PyTorch, Transformers (VITS), CUDA 11.8+ |
| 음성 모델 | Meta MMS-TTS (VITS 아키텍처) |
| 오디오 I/O | soundfile, scipy |
| 텍스트 전처리 | uroman (로마자 변환) |
| 프론트엔드 | Vue 3 (Composition API), Vite, Tailwind CSS |

## 8. 설계상의 가정 및 제약

- **단일 사용자 MVP**: 추론을 `Lock`으로 직렬화하므로 동시 요청은 대기한다.
- **이력 비영속**: 생성 이력은 브라우저 메모리(`App.vue`의 `history`)에만
  존재하며 새로고침 시 사라진다. wav 파일 자체는 서버에 20개까지 보존.
- **모델 화이트리스트**: 임의 HF 모델 로딩을 막아 검증된 4개 언어만 노출.
- **VRAM 관리**: 모델 전환 시에만 캐시를 비우며, 동시에 1개 모델만 메모리 상주.
