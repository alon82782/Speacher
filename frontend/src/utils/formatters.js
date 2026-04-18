import { SCORE_GRADES } from "../constants";

/** 날짜 → "2025-03-24" */
export const formatDate = (dateStr) => {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("ko-KR", {
    year: "numeric", month: "2-digit", day: "2-digit",
  }).replace(/\. /g, "-").replace(".", "");
};

/** 날짜 → "2025-03-24 14:30" */
export const formatDateTime = (dateStr) => {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return `${formatDate(dateStr)} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
};

/** 초 → "1분 30초" */
export const formatDuration = (seconds) => {
  if (!seconds && seconds !== 0) return "-";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}분 ${s}초` : `${s}초`;
};

/** 파일 크기 → "12.3 MB" */
export const formatFileSize = (bytes) => {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
};

/** 점수 → 등급 { label, color } */
export const getScoreGrade = (score) => {
  return SCORE_GRADES.find((g) => score >= g.min) || SCORE_GRADES[SCORE_GRADES.length - 1];
};

/** 0~100 점수 → 퍼센트 문자열 "85%" */
export const formatScore = (score) => `${Math.round(score ?? 0)}점`;

/** wpm → "분당 120 단어" */
export const formatWpm = (wpm) => `분당 ${Math.round(wpm ?? 0)}단어`;
