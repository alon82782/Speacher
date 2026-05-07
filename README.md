# Speacher

AI 발표 코칭 시스템. 사용자가 발표 영상을 업로드하면 7단계 분석 파이프라인을 통해 시선·자세·발화 속도·볼륨·필러워드·발음·시간 준수도를 평가하고, GPT 기반 피드백을 제공합니다.

## 프로젝트 구성

```
Speacher/
├── backend/    # FastAPI + MySQL + Celery + OpenAI
└── frontend/   # React 19 + Vite + TailwindCSS
```

각 디렉토리는 독립적으로 동작하며, 자세한 설치·실행 방법은 해당 디렉토리의 README를 참고하세요.

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)

## 주요 기능

- **회원 인증**: JWT(Access + Refresh Token) 기반 로그인/회원가입/프로필 관리
- **영상 업로드**: 최대 500MB, mp4/mov/avi/webm 지원
- **7단계 분석 파이프라인**:
  1. 영상 업로드
  2. 캘리브레이션 추출
  3. 시선·자세 분석
  4. 음성 추출
  5. 발화 속도·볼륨 분석
  6. 필러워드·발음 분석
  7. AI 피드백 생성
- **점수 체계 (총 100점)**:
  - 시선 처리율 25점 / 자세 안정성 10점 / 발화 속도 20점 / 볼륨·피치 15점 / 필러워드 15점 / 발음 정확성 10점 / 시간 준수 5점
- **분석 결과**: 채널별(시각/음성/어휘/전달) 점수, 타임라인 이벤트, GPT 피드백
- **이력 관리**: 과거 분석 기록 조회, 재분석, 삭제

## 기술 스택

**Backend**
- Python 3.11, FastAPI, SQLAlchemy 2.0 (async)
- MySQL 8.0, Redis 7
- Celery (분석 워커)
- OpenAI (GPT 피드백), Whisper (음성 인식)
- Alembic (DB 마이그레이션), JWT

**Frontend**
- React 19, Vite 8
- TailwindCSS 3
- Zustand (인증 상태), TanStack Query (서버 상태)
- React Router 7, Axios, Chart.js

## 빠른 시작

### 1. 백엔드 (DB·Redis 포함)

```bash
cd backend
docker compose up -d              # MySQL, Redis 컨테이너 기동
cp .env.example .env              # 환경 변수 설정 (DB_PORT=3307 주의)
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API 문서: http://localhost:8000/docs

### 2. 프론트엔드

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

## 개발 단계 (Phase)

현재 Phase 4까지 완료된 상태입니다.

- ✅ Phase 1–3: 인프라, 인증, 기본 모델
- ✅ Phase 4: 분석 API 라우터 (`POST /analysis`, `GET /analysis/{job_id}/...`)
- ⏳ Phase 5: Celery 분석 파이프라인 구현 (`app/tasks/analysis_task.py` 현재 stub)

## 라이선스

내부 프로젝트 (캡스톤).
