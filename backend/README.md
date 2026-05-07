# Speacher Backend

FastAPI 기반 AI 발표 코칭 API 서버.

## 기술 스택

- **Python 3.11**, FastAPI 0.115, Uvicorn
- **DB**: MySQL 8.0, SQLAlchemy 2.0 (async, aiomysql), Alembic
- **인증**: JWT (python-jose), bcrypt (passlib)
- **비동기 작업**: Celery 5.4 + Redis 7
- **AI**: OpenAI GPT, Whisper (음성 인식)
- **로깅·기타**: loguru, slowapi

## 빠른 시작

### 1. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 주요 항목:

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DB_HOST` / `DB_PORT` | MySQL 주소 | `localhost` / `3306` |
| `DB_USER` / `DB_PASSWORD` | DB 계정 | `speacher_user` / `speacher_password` |
| `JWT_SECRET_KEY` | JWT 서명 키 | (반드시 변경) |
| `OPENAI_API_KEY` | OpenAI API 키 | - |
| `MAX_FILE_SIZE_MB` | 업로드 최대 크기 | `500` |
| `ALLOWED_ORIGINS` | CORS 허용 출처 | `http://localhost:5173,...` |

> ⚠️ **포트 주의**: `docker-compose.yml`은 MySQL을 호스트 포트 **3307**에 노출합니다. 호스트에서 직접 연결한다면 `.env`의 `DB_PORT`를 `3307`로 바꾸세요. (도커 내부 통신은 3306 그대로)

### 2. DB·Redis 기동

```bash
docker compose up -d
```

기동되는 서비스:
- `speacher_db` (MySQL 8.0, 호스트 포트 3307)
- `speacher_redis` (Redis 7, 호스트 포트 6379)

### 3. 의존성 설치 & 마이그레이션

```bash
pip install -r requirements.txt
alembic upgrade head
```

새 마이그레이션 생성:

```bash
alembic revision --autogenerate -m "add_xxx_table"
alembic upgrade head
```

### 4. 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

- API 문서 (Swagger): http://localhost:8000/docs
- API 문서 (ReDoc): http://localhost:8000/redoc
- 헬스체크: http://localhost:8000/health

> `APP_DEBUG=false`인 경우 `/docs`, `/redoc`은 비활성화됩니다.

### 5. Celery 워커 (Phase 5 이후)

```bash
celery -A app.tasks.celery_app.celery_app worker -l info
```

현재 `app/tasks/analysis_task.py`는 stub 상태입니다.

## 디렉토리 구조

```
backend/
├── app/
│   ├── api/v1/         # 라우터 (auth, analysis)
│   ├── services/       # 비즈니스 로직 (auth_service, analysis_service)
│   ├── crud/           # DB 접근 계층
│   ├── models/         # SQLAlchemy 모델
│   ├── schemas/        # Pydantic 요청·응답 스키마
│   ├── core/           # 보안, 도메인 예외
│   ├── middleware/     # 에러 핸들러, Rate Limit
│   ├── utils/          # JWT, 비밀번호, 파일, 의존성
│   ├── db/             # DB 세션, Base
│   ├── tasks/          # Celery 태스크
│   ├── config.py       # 환경 변수 (pydantic-settings)
│   └── main.py         # FastAPI 진입점
├── alembic/            # DB 마이그레이션
├── docker/             # MySQL 초기화 스크립트
├── tests/              # pytest (현재 비어 있음)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## 아키텍처 핵심

### 계층 구조

```
Router (api/v1)  →  Service (services)  →  CRUD (crud)  →  Model (models)
```

- **Router**: 요청 검증, 인증, 응답 직렬화만. DB 쿼리 X.
- **Service**: 비즈니스 로직. `auth_service`, `analysis_service` 싱글톤 인스턴스.
- **CRUD**: 순수 DB 읽기·쓰기 헬퍼. `db: AsyncSession` 인자.
- **Model**: SQLAlchemy 2.0 `Mapped[...]` 타입.

### 응답 형식

성공 응답은 `SuccessResponse`로 래핑됩니다 (`app/schemas/common.py`):

```json
{ "success": true, "data": { ... }, "message": "..." }
```

에러 응답은 `app/middleware/error_handler.py`가 통일해서 반환합니다:

```json
{
  "success": false,
  "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] }
}
```

### 인증 흐름

1. `POST /api/v1/auth/register` 또는 `/login` → Access Token + Refresh Token 발급
2. 클라이언트가 `Authorization: Bearer <access_token>` 헤더로 요청
3. `get_current_user` 의존성(`app/utils/dependencies.py`)이 토큰 검증 + 사용자 조회
4. Access Token 만료 시 `POST /api/v1/auth/refresh`로 갱신

### 분석 도메인

세 모델이 FK로 연결되어 있고 `cascade="all, delete-orphan"`로 동기화됩니다:

- **AnalysisJob**: 업로드당 1건. 상태(`PENDING`/`PROCESSING`/`COMPLETED`/`FAILED`), 진행 단계(1–7), Celery 태스크 ID 추적.
- **AnalysisResult**: 점수 7개 + 채널 점수 4개 + GPT 피드백 (1:1).
- **TimelineEvent**: 타임라인 이벤트(시선 이탈, 필러워드 등) (1:N).

7단계 파이프라인과 점수 가중치(`SCORE_*`)는 `app/config.py`에 정의되어 있고, 프론트엔드(`frontend/src/constants/index.js`)와 **반드시 일치**해야 합니다.

## 주요 API

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/v1/auth/register` | 회원가입 |
| POST | `/api/v1/auth/login` | 로그인 |
| POST | `/api/v1/auth/refresh` | 토큰 갱신 |
| GET  | `/api/v1/auth/me` | 내 프로필 |
| POST | `/api/v1/analysis/validate` | 파일 사전 검증 |
| POST | `/api/v1/analysis` | 영상 업로드 + 분석 시작 |
| GET  | `/api/v1/analysis/{job_id}/status` | 진행 상태 |
| GET  | `/api/v1/analysis/{job_id}/result` | 분석 결과 |
| GET  | `/api/v1/analysis/{job_id}/timeline` | 타임라인 |
| GET  | `/api/v1/analysis/{job_id}/feedback` | GPT 피드백 |
| GET  | `/api/v1/analysis/history` | 분석 이력 |
| GET  | `/api/v1/analysis/stats` | 대시보드 통계 |

## 테스트

```bash
pytest
pytest tests/path/to/test_file.py::test_name
```

(현재 `tests/` 디렉토리는 비어 있습니다.)
