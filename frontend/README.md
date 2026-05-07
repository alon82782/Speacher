# Speacher Frontend

Speacher AI 발표 코칭 시스템의 React 프론트엔드.

## 기술 스택

- **React 19** + **Vite 8**
- **TailwindCSS 3** (스타일링)
- **Zustand** (인증 등 클라이언트 상태)
- **TanStack Query 5** (서버 상태·캐싱)
- **React Router 7** (라우팅)
- **Axios** (HTTP 클라이언트)
- **Chart.js** (점수 시각화)

## 빠른 시작

```bash
npm install
npm run dev          # 개발 서버 (http://localhost:5173)
npm run build        # 프로덕션 빌드
npm run lint         # ESLint
npm run preview      # 빌드 결과 미리보기
```

### 환경 변수

`.env`:

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

미설정 시 기본값(`http://localhost:8000/api/v1`)이 사용됩니다 (`src/constants/index.js`).

## 디렉토리 구조

```
frontend/
├── src/
│   ├── api/            # axios 인스턴스 + API 모듈 (authApi, analysisApi)
│   ├── components/     # 재사용 컴포넌트 (common, layout)
│   ├── constants/      # API URL, 점수표, 상태 상수 등
│   ├── hooks/          # useAuth, useAnalysis (TanStack Query 래퍼)
│   ├── pages/          # 페이지 컴포넌트
│   ├── stores/         # Zustand 스토어 (authStore, analysisStore)
│   ├── utils/          # formatters, validators
│   ├── App.jsx         # 라우팅 + 인증 가드
│   ├── main.jsx        # 진입점 + QueryClient 설정
│   └── index.css       # Tailwind directives
├── public/
├── index.html
├── vite.config.js
├── tailwind.config.js
├── eslint.config.js
└── package.json
```

## 페이지 구성

| 경로 | 컴포넌트 | 설명 |
|------|----------|------|
| `/` | `AuthPage` | 로그인 / 회원가입 |
| `/dashboard` | `Dashboard` | 메인 대시보드, 통계 |
| `/upload` | `UploadPage` | 영상 업로드 |
| `/analyzing/:jobId` | `AnalyzingPage` | 분석 진행 상태 (폴링) |
| `/result/:jobId` | `ResultPage` | 분석 결과 요약 |
| `/result/:jobId/detail` | `ResultDetailPage` | 상세 결과 (타임라인 등) |
| `/history` | `HistoryPage` | 분석 이력 |
| `/mypage` | `MyPage` | 프로필 / 비밀번호 / 회원탈퇴 |

`App.jsx`의 `PrivateRoute`/`PublicRoute`가 `isAuthenticated` 기준으로 접근을 제어합니다.

## 인증 흐름

1. 로그인 성공 시 `authStore.setAuth({ user, access_token, refresh_token })` 호출
2. Access/Refresh Token은 `localStorage`에 저장 (`speacher_access_token`, `speacher_refresh_token`)
3. `axiosInstance.js`의 요청 인터셉터가 모든 요청에 `Authorization: Bearer ...` 자동 첨부
4. 401 응답 시 응답 인터셉터가 자동으로 `/auth/refresh`를 호출해 토큰 갱신 후 원 요청 재시도
5. 갱신 실패 시 토큰을 모두 제거하고 `/`로 이동

> Zustand의 persist에는 `user`와 `isAuthenticated`만 저장되고, 토큰 자체는 별도로 `localStorage`에 관리됩니다.

## 분석 진행 상태 폴링

`AnalyzingPage`는 `POLLING_INTERVAL_MS`(기본 2초) 주기로 `GET /analysis/{job_id}/status`를 호출해 단계(1–7)와 진행률을 표시합니다. 상태가 `COMPLETED` 또는 `FAILED`가 되면 결과 페이지로 이동합니다.

7단계 정의(`ANALYSIS_STEPS`)와 점수 가중치(`SCORE_WEIGHTS`)는 `src/constants/index.js`에 있으며, 백엔드(`backend/app/config.py`)와 **반드시 동일**해야 합니다.

## TanStack Query 설정

`main.jsx`의 기본 옵션:

- `retry: 1` — 실패 시 1회 재시도
- `refetchOnWindowFocus: false`
- `staleTime: 60000` (1분)
- `mutations.retry: 0`

쿼리는 `src/hooks/useAuth.js`, `src/hooks/useAnalysis.js`로 래핑되어 있으니 컴포넌트에서는 훅만 사용하세요.
