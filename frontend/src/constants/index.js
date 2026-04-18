// ── API ───────────────────────────────────────────────────────────────────────
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

// ── 로컬스토리지 키 ───────────────────────────────────────────────────────────
export const TOKEN_KEY = "speacher_access_token";
export const REFRESH_TOKEN_KEY = "speacher_refresh_token";

// ── 분석 Job 상태 ─────────────────────────────────────────────────────────────
export const JOB_STATUS = {
  PENDING:    "pending",
  PROCESSING: "processing",
  COMPLETED:  "completed",
  FAILED:     "failed",
};

// ── 분석 7단계 (AnalyzingPage와 동기화) ──────────────────────────────────────
export const ANALYSIS_STEPS = [
  { step: 1, label: "영상 업로드 중",       key: "upload"        },
  { step: 2, label: "캘리브레이션 추출",     key: "calibration"   },
  { step: 3, label: "시선·자세 분석",        key: "visual"        },
  { step: 4, label: "음성 추출 중",          key: "audio_extract" },
  { step: 5, label: "발화 속도·볼륨 분석",   key: "audio_analyze" },
  { step: 6, label: "필러워드·발음 분석",    key: "speech"        },
  { step: 7, label: "AI 피드백 생성",        key: "gpt"           },
];

// ── 점수 배점표 ───────────────────────────────────────────────────────────────
export const SCORE_WEIGHTS = {
  gaze:            { label: "시선 처리율",  maxScore: 25, channel: "시각" },
  posture:         { label: "자세 안정성",  maxScore: 10, channel: "시각" },
  speech_rate:     { label: "발화 속도",    maxScore: 20, channel: "음성" },
  volume_pitch:    { label: "볼륨/피치",    maxScore: 15, channel: "음성" },
  filler_word:     { label: "필러워드",     maxScore: 15, channel: "어휘" },
  pronunciation:   { label: "발음 정확성",  maxScore: 10, channel: "어휘" },
  time_compliance: { label: "시간 준수",    maxScore:  5, channel: "전달" },
};

// ── 파일 업로드 제한 ──────────────────────────────────────────────────────────
export const ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/avi", "video/webm"];
export const MAX_FILE_SIZE_MB = 500;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

// ── 점수 등급 컷 ─────────────────────────────────────────────────────────────
export const SCORE_GRADES = [
  { min: 90, label: "S", color: "#6366f1" },
  { min: 80, label: "A", color: "#22c55e" },
  { min: 70, label: "B", color: "#3b82f6" },
  { min: 60, label: "C", color: "#f59e0b" },
  { min:  0, label: "D", color: "#ef4444" },
];

// ── 폴링 주기 (분석 상태 조회) ────────────────────────────────────────────────
export const POLLING_INTERVAL_MS = 2000;
