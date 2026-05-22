# Tiny TTS — UML 다이어그램

본 문서의 다이어그램은 [Mermaid](https://mermaid.js.org/) 문법으로 작성되었으며,
GitHub·VS Code(Markdown Preview Mermaid) 등에서 바로 렌더링된다.

## 1. 클래스 다이어그램

백엔드 핵심 클래스와 프론트엔드 컴포넌트의 정적 구조.

```mermaid
classDiagram
    class TTSEngine {
        +str device
        +str model_name
        +VitsModel model
        +VitsTokenizer tokenizer
        +int sample_rate
        +bool needs_uroman
        +Uroman uroman
        +__init__(model_name, device)
        +romanize(text) str
        +generate(text, output_path) ndarray
        +get_device_info() dict
    }

    class FastAPIApp {
        <<module: app.py>>
        +TTSEngine engine
        +Lock engine_lock
        +dict ALLOWED_MODELS
        +str DEFAULT_MODEL
        +_load_engine(model_name)
        +_prune_outputs()
        +lifespan(app)
        +status() dict
        +generate(req) dict
        +get_audio(filename) FileResponse
    }

    class GenerateRequest {
        <<pydantic BaseModel>>
        +str text
        +str language
    }

    class VitsModel {
        <<transformers>>
    }
    class VitsTokenizer {
        <<transformers>>
    }
    class Uroman {
        <<uroman>>
        +romanize_string(text) str
    }

    FastAPIApp --> TTSEngine : engine 생성·소유
    FastAPIApp ..> GenerateRequest : 요청 검증
    TTSEngine --> VitsModel : 로딩·추론
    TTSEngine --> VitsTokenizer : 토크나이즈
    TTSEngine --> Uroman : 로마자 변환 선택적
```

```mermaid
classDiagram
    class App {
        <<App.vue>>
        +ref status
        +ref statusError
        +ref generating
        +ref errorMsg
        +ref history
        +onMounted()
        +handleGenerate(payload)
    }

    class TtsForm {
        <<TtsForm.vue>>
        +prop languages
        +prop disabled
        +ref text
        +ref language
        +computed remaining
        +computed canSubmit
        +submit()
        +emit_generate()
    }

    class HistoryList {
        <<HistoryList.vue>>
        +prop items
        +formatTime(d) str
    }

    class api {
        <<api.js>>
        +fetchStatus() Promise
        +generateSpeech(text, language) Promise
        +audioUrl(filename) str
    }

    App --> TtsForm : 렌더 + generate 이벤트 수신
    App --> HistoryList : 렌더 items 전달
    App ..> api : fetchStatus generateSpeech
    HistoryList ..> api : audioUrl
```

## 2. 컴포넌트 다이어그램

시스템 구성 요소 간의 의존 관계.

```mermaid
flowchart TB
    subgraph Browser["브라우저"]
        SPA["Vue 3 SPA<br/>App / TtsForm / HistoryList"]
        API_JS["api.js"]
        SPA --> API_JS
    end

    subgraph Server["FastAPI 서버 (:8000)"]
        ROUTES["라우터<br/>/api/status<br/>/api/generate<br/>/api/audio"]
        ENGINE["TTSEngine"]
        STATIC["StaticFiles<br/>(dist 정적 서빙)"]
        ROUTES --> ENGINE
    end

    subgraph External["외부 리소스"]
        HF["HuggingFace Hub<br/>(VITS 체크포인트)"]
        TORCH["PyTorch / CUDA"]
        FS["backend/outputs/<br/>(wav 파일)"]
    end

    API_JS -->|HTTP /api/*| ROUTES
    SPA -.->|운영 모드| STATIC
    ENGINE -->|모델 다운로드| HF
    ENGINE -->|추론 실행| TORCH
    ROUTES -->|wav 저장/조회| FS
```

## 3. 시퀀스 다이어그램 — 음성 생성

사용자가 텍스트를 입력하고 음성을 생성하는 전체 흐름.

```mermaid
sequenceDiagram
    actor User as 사용자
    participant Form as TtsForm.vue
    participant App as App.vue
    participant Api as api.js
    participant BE as FastAPI (app.py)
    participant Eng as TTSEngine
    participant FS as outputs/

    User->>Form: 언어 선택 + 텍스트 입력
    User->>Form: "음성 생성" 클릭
    Form->>Form: canSubmit 검증 (공백/disabled)
    Form-->>App: emit generate({text, language})

    App->>App: generating = true
    App->>Api: generateSpeech(text, language)
    Api->>BE: POST /api/generate

    BE->>BE: Pydantic 검증 (1~500자)
    BE->>BE: language ∈ ALLOWED_MODELS ?
    alt 미허용 언어
        BE-->>Api: 400 "지원하지 않는 언어"
    end

    BE->>BE: engine_lock 획득
    alt 모델 전환 필요
        BE->>Eng: _load_engine(language)
        Eng->>Eng: 이전 모델 해제 + VRAM 회수
    end

    BE->>Eng: generate(text, output_path)
    Eng->>Eng: 텍스트 재검증
    opt uroman 필요 모델
        Eng->>Eng: romanize(text)
    end
    Eng->>Eng: tokenize → model() 추론
    Eng->>FS: soundfile.write(wav)
    Eng-->>BE: waveform

    BE->>FS: _prune_outputs() (20개 초과 정리)
    BE->>BE: engine_lock 해제
    BE-->>Api: 200 {filename}
    Api-->>App: {filename}

    App->>App: history.unshift(항목)
    App->>Api: fetchStatus() (모델 상태 갱신)
    App->>App: generating = false
    App-->>User: HistoryList에 오디오 표시
```

## 4. 시퀀스 다이어그램 — 앱 초기화 및 상태 조회

```mermaid
sequenceDiagram
    participant Boot as Uvicorn
    participant BE as FastAPI (lifespan)
    participant Eng as TTSEngine
    participant App as App.vue
    participant Api as api.js

    Note over Boot,Eng: 서버 기동
    Boot->>BE: lifespan 시작
    BE->>Eng: _load_engine(DEFAULT_MODEL)
    Eng->>Eng: VitsModel / Tokenizer 로딩
    Eng-->>BE: engine 준비 완료
    BE->>BE: 디바이스·모델 정보 출력

    Note over App,Api: SPA 마운트
    App->>App: onMounted()
    App->>Api: fetchStatus()
    Api->>BE: GET /api/status
    BE->>Eng: get_device_info()
    Eng-->>BE: {device, model_name, sample_rate, ...}
    BE-->>Api: 200 {ready, languages, ...}
    Api-->>App: status
    alt 연결 실패
        Api-->>App: throw
        App->>App: statusError 표시
    end
    App-->>App: TtsForm 렌더 (languages 전달)
```

## 5. 상태 다이어그램 — 백엔드 TTS 엔진

```mermaid
stateDiagram-v2
    [*] --> 미로딩
    미로딩 --> 로딩중 : 서버 기동 (lifespan)
    로딩중 --> 대기 : 기본 모델 로딩 완료
    대기 --> 추론중 : POST /api/generate (lock 획득)
    추론중 --> 대기 : wav 생성 완료
    대기 --> 모델전환중 : 요청 언어 ≠ 현재 모델
    모델전환중 --> 추론중 : 새 모델 로딩 + VRAM 회수
    추론중 --> 대기 : ValueError → 400 응답
```

## 6. 상태 다이어그램 — 프론트엔드 생성 흐름

```mermaid
stateDiagram-v2
    [*] --> 초기화중
    초기화중 --> 준비완료 : fetchStatus 성공
    초기화중 --> 연결오류 : fetchStatus 실패
    준비완료 --> 생성중 : handleGenerate (generating=true)
    생성중 --> 준비완료 : 성공 → history 추가
    생성중 --> 오류표시 : 실패 → errorMsg 설정
    오류표시 --> 생성중 : 재시도
    연결오류 --> [*]
```
