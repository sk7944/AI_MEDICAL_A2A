# AI Medical A2A Consultation System

AI 기반 의료 상담 시스템 - DR_BLADDER와 DR_PROSTATE 전문 에이전트가 협력하여 종합적인 의료 상담을 제공합니다.

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐
│   Flask Web     │    │  DR_BLADDER     │
│   Interface     │    │   API :8001     │
│   :8000         │    └─────────────────┘
└─────────────────┘              │
          │                      │
          ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│  Orchestrator   │◄──►│  DR_PROSTATE    │
│   API :8003     │    │   API :8002     │
└─────────────────┘    └─────────────────┘
```

## 📋 프로젝트 개요

EAU (European Association of Urology) 가이드라인을 기반으로 한 전문 AI 의료 상담 시스템:
- **DR_BLADDER**: 방광암 전문 AI 에이전트  
- **DR_PROSTATE**: 전립선암 전문 AI 에이전트
- **Orchestrator**: 두 에이전트의 의견을 종합하는 조율 시스템

각 에이전트는 최신 의료 가이드라인을 RAG (Retrieval-Augmented Generation) 방식으로 학습하여 근거 기반 답변을 제공합니다.

## 🚀 빠른 시작

### 1. 시스템 시작
```bash
./start_servers.sh
```

### 2. 웹 인터페이스 접속
브라우저에서 [http://localhost:8000](http://localhost:8000) 접속

### 3. 의료 상담 시작
- 상담 페이지에서 질문 입력
- DR_BLADDER와 DR_PROSTATE가 병렬로 분석
- 종합 의견과 개별 전문가 의견 확인

## 📋 관리 명령어

### 서버 관리
```bash
./start_servers.sh    # 전체 시스템 시작
./stop_servers.sh     # 전체 시스템 중지  
./restart_servers.sh  # 전체 시스템 재시작
./status_servers.sh   # 시스템 상태 확인
```

### 독립 CLI 도구
```bash
# DR_BLADDER CLI
cd python && ./dr-bladder.sh query "BCG 치료 부작용은?"

# DR_PROSTATE CLI
cd python && ./dr-prostate.sh query "PSA 수치는 언제 검사하나요?"
```

## 🌐 서비스 엔드포인트

### 웹 인터페이스
- **메인 페이지**: http://localhost:8000
- **의료 상담**: http://localhost:8000/consult
- **시스템 상태**: http://localhost:8000/health
- **소개**: http://localhost:8000/about

### API 서비스
- **DR_BLADDER API**: http://localhost:8001
- **DR_PROSTATE API**: http://localhost:8002  
- **Orchestrator API**: http://localhost:8003

## 📊 로그 확인

### 실시간 로그 모니터링
```bash
# 전체 로그
tail -f logs/*.log

# 개별 서비스 로그
tail -f logs/bladder.log        # DR_BLADDER
tail -f logs/prostate.log       # DR_PROSTATE  
tail -f logs/orchestrator.log   # Orchestrator
tail -f logs/web.log           # Flask Web
```

### Flask 웹 서버 상세 로그
```bash
tail -f web/flask_app.log
```

## 📦 시스템 요구사항

- **운영체제**: Linux, macOS, Windows
- **Python**: 3.8 이상
- **메모리**: 8GB 이상 권장
- **디스크 공간**: 10GB 이상 여유 공간
- **Ollama**: 필수 (AI 모델 실행용)
- **GPU (선택사항)**: 
  - NVIDIA GPU (CUDA 지원)
  - 4GB VRAM 이상 권장

## 🛠️ 설치 방법

### 1단계: 저장소 클론
```bash
git clone https://github.com/sk7944/AI_MEDICAL_A2A.git
cd AI_MEDICAL_A2A
```

### 2단계: Python 가상환경 설정
```bash
python -m venv env
source env/bin/activate  # Linux/macOS
# 또는
env\Scripts\activate  # Windows
```

### 3단계: 의존성 설치
```bash
pip install fastapi uvicorn ollama langchain chromadb sentence-transformers pypdf2
```

### 4단계: Ollama 설치 및 모델 다운로드
```bash
# Ollama 설치
curl -fsSL https://ollama.ai/install.sh | sh  # Linux/macOS
# Windows는 https://ollama.ai/download 에서 설치

# Gemma3:4b 모델 다운로드
ollama pull gemma3:4b
```

### 5단계: 벡터 데이터베이스 구축
```bash
python agents/shared/setup_vector_db.py
```

## 🎯 사용 방법

### API 서버 실행

**DR_BLADDER 에이전트 실행 (포트 8001):**
```bash
cd agents/bladder
./run_bladder.sh
# 또는
python main_bladder.py
```

**DR_PROSTATE 에이전트 실행 (포트 8002):**
```bash
cd agents/prostate
./run_prostate.sh
# 또는
python main_prostate.py
```

### API 엔드포인트

각 에이전트는 다음 엔드포인트를 제공합니다:

#### 건강 상태 확인
```bash
curl http://localhost:8001/health  # DR_BLADDER
curl http://localhost:8002/health  # DR_PROSTATE
```

#### 질문하기
```bash
# DR_BLADDER에게 질문
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "BCG 치료의 부작용은 무엇인가요?"}'

# DR_PROSTATE에게 질문
curl -X POST http://localhost:8002/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "PSA 검사에 대해 설명해주세요"}'
```

### 예제 질문들

**방광암 관련 (DR_BLADDER):**
- "BCG 치료의 부작용은 무엇인가요?"
- "방광암의 재발 위험 요인에 대해 알려주세요"
- "TURBT 수술 후 관리 방법은?"
- "What are the indications for BCG therapy?"

**전립선암 관련 (DR_PROSTATE):**
- "PSA 검사의 정상 수치는?"
- "전립선암의 글리슨 점수에 대해 설명해주세요"
- "전립선 생검은 언제 필요한가요?"
- "What are the treatment options for localized prostate cancer?"

## 📁 프로젝트 구조

```
AI_MEDICAL_A2A/
├── agents/
│   ├── bladder/              # DR_BLADDER API
│   │   ├── bladder_logic.py  # 핵심 로직
│   │   ├── main_bladder.py   # FastAPI 서버
│   │   └── run_bladder.sh    # 실행 스크립트
│   ├── prostate/             # DR_PROSTATE API  
│   │   ├── prostate_logic.py # 핵심 로직
│   │   ├── main_prostate.py  # FastAPI 서버
│   │   └── run_prostate.sh   # 실행 스크립트
│   └── shared/               # 공유 모듈
│       ├── vector_db.py      # 벡터 DB 관리
│       └── setup_vector_db.py # DB 초기화 스크립트
├── files/                    # 의료 가이드라인 PDF
│   ├── EAU-Guidelines-on-Non-muscle-invasive-Bladder-Cancer-2025.pdf
│   └── EAU-EANM-ESTRO-ESUR-ISUP-SIOG-Guidelines-on-Prostate-Cancer-2025_updated.pdf
├── chroma_db/               # ChromaDB 벡터 데이터베이스
├── n8n/workflows/           # n8n 워크플로우 (개발 예정)
├── tests/                   # 테스트 코드
└── README.md
```

## 🔧 기술 스택

### 핵심 기술
- **Ollama + Gemma3:4b**: 로컬 LLM 실행 환경
- **FastAPI**: 고성능 REST API 프레임워크
- **ChromaDB**: 벡터 데이터베이스
- **LangChain**: LLM 애플리케이션 개발 프레임워크
- **RAG**: 검색 증강 생성 기법

### AI/ML 라이브러리
- **Sentence Transformers**: 다국어 텍스트 임베딩
- **PyPDF2**: PDF 문서 처리
- **NumPy**: 벡터 연산

### 개발 도구
- **Python 3.8+**: 백엔드 개발
- **Uvicorn**: ASGI 서버
- **n8n**: 워크플로우 자동화 (예정)

## 🚀 향후 개발 계획

### Phase 3: n8n 워크플로우 통합
- [ ] n8n 워크플로우 템플릿 개발
- [ ] 에이전트 간 자동 라우팅 로직
- [ ] 복합 질문 처리 시스템
- [ ] 협진 결과 통합 API

### 추가 개선 사항
- [ ] 더 많은 의료 분야 에이전트 추가
- [ ] 웹 UI 인터페이스 개발
- [ ] Docker 컨테이너화
- [ ] Kubernetes 배포 지원
- [ ] 모니터링 및 로깅 시스템

## ⚠️ 면책 조항

**중요**: 이 시스템은 **정보 제공 목적**으로만 사용되어야 하며, **실제 의료 상담을 대체할 수 없습니다**.

- 모든 의료 결정은 반드시 **자격을 갖춘 의료 전문가**와 상의해야 합니다
- 이 시스템의 답변은 참고용이며, 진단이나 치료 권고가 아닙니다
- 응급 상황 시에는 즉시 의료기관을 방문하거나 응급 전화를 이용하세요

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

프로젝트 개선을 위한 기여를 환영합니다!

1. 저장소를 Fork 하세요
2. 기능 브랜치를 생성하세요 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋하세요 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시하세요 (`git push origin feature/AmazingFeature`)
5. Pull Request를 열어주세요

## 📞 지원 및 문의

문제가 발생하거나 질문이 있으시면:

1. **GitHub Issues**: 버그 리포트 및 기능 제안
2. **이메일**: [프로젝트 관리자에게 문의]
3. **문서**: 프로젝트 위키 참조

---

**AI Medical A2A** - AI 기술을 통한 더 나은 의료 정보 접근성을 위하여