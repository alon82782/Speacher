import axiosInstance from "./axiosInstance";

/**
 * POST /analysis/validate — 업로드 전 파일 사전 검증
 * @param {File} file
 */
export const validateFile = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return axiosInstance.post("/analysis/validate", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};

/**
 * POST /analysis — 영상 업로드 및 분석 시작
 * @param {File} file
 * @param {{ title, target_duration_sec }} meta
 * @param {(progress: number) => void} onUploadProgress
 * @returns { job_id }
 */
export const startAnalysis = (file, meta, onUploadProgress) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", meta.title || file.name);
  if (meta.target_duration_sec) {
    formData.append("target_duration_sec", meta.target_duration_sec);
  }
  return axiosInstance.post("/analysis", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      const percent = Math.round((e.loaded * 100) / e.total);
      onUploadProgress?.(percent);
    },
  }).then((r) => r.data);
};

/**
 * POST /analysis/{job_id}/retry — 실패한 분석 재시도
 */
export const retryAnalysis = (jobId) =>
  axiosInstance.post(`/analysis/${jobId}/retry`).then((r) => r.data);

/**
 * GET /analysis/{job_id}/status — 분석 진행 상태 조회
 * @returns { status, current_step, progress }
 */
export const getAnalysisStatus = (jobId) =>
  axiosInstance.get(`/analysis/${jobId}/status`).then((r) => r.data);

/**
 * GET /analysis/{job_id}/result — 분석 결과 조회
 * @returns { total_score, scores, channel_scores }
 */
export const getAnalysisResult = (jobId) =>
  axiosInstance.get(`/analysis/${jobId}/result`).then((r) => r.data);

/**
 * GET /analysis/{job_id}/timeline — 타임라인 이벤트 조회
 */
export const getAnalysisTimeline = (jobId) =>
  axiosInstance.get(`/analysis/${jobId}/timeline`).then((r) => r.data);

/**
 * GET /analysis/{job_id}/feedback — GPT 피드백 조회
 */
export const getAnalysisFeedback = (jobId) =>
  axiosInstance.get(`/analysis/${jobId}/feedback`).then((r) => r.data);

/**
 * GET /analysis/history — 분석 이력 목록
 * @param {{ page, size, sort }} params
 */
export const getAnalysisHistory = (params) =>
  axiosInstance.get("/analysis/history", { params }).then((r) => r.data);

/**
 * GET /analysis/stats — 대시보드 통계
 */
export const getAnalysisStats = () =>
  axiosInstance.get("/analysis/stats").then((r) => r.data);

/**
 * DELETE /analysis/{job_id} — 분석 기록 삭제
 */
export const deleteAnalysis = (jobId) =>
  axiosInstance.delete(`/analysis/${jobId}`).then((r) => r.data);
