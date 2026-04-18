import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import * as analysisApi from "../api/analysisApi";
import useAnalysisStore from "../stores/analysisStore";
import { JOB_STATUS, POLLING_INTERVAL_MS } from "../constants";

// ── Query Keys ────────────────────────────────────────────────────────────────
export const ANALYSIS_KEYS = {
  status:   (id) => ["analysis", "status",   id],
  result:   (id) => ["analysis", "result",   id],
  timeline: (id) => ["analysis", "timeline", id],
  feedback: (id) => ["analysis", "feedback", id],
  history:  (params) => ["analysis", "history", params],
  stats:    () => ["analysis", "stats"],
};

// ── 파일 업로드 + 분석 시작 ───────────────────────────────────────────────────
export const useStartAnalysis = () => {
  const { startJob, setUploadProgress } = useAnalysisStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: ({ file, meta }) =>
      analysisApi.startAnalysis(file, meta, setUploadProgress),
    onSuccess: (res) => {
      const jobId = res.data.job_id;
      startJob(jobId);
      navigate(`/analyzing/${jobId}`);
    },
  });
};

// ── 분석 상태 폴링 ────────────────────────────────────────────────────────────
export const useAnalysisStatus = (jobId) => {
  const { updateJobStatus, finishJob } = useAnalysisStore();

  return useQuery({
    queryKey: ANALYSIS_KEYS.status(jobId),
    queryFn: () => analysisApi.getAnalysisStatus(jobId),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status;
      // 완료/실패 시 폴링 중단
      if (status === JOB_STATUS.COMPLETED || status === JOB_STATUS.FAILED) return false;
      return POLLING_INTERVAL_MS;
    },
    select: (res) => res.data,
    onSuccess: (data) => {
      updateJobStatus(data);
      if (data.status === JOB_STATUS.COMPLETED || data.status === JOB_STATUS.FAILED) {
        finishJob(data.status);
      }
    },
  });
};

// ── 분석 결과 조회 ────────────────────────────────────────────────────────────
export const useAnalysisResult = (jobId) =>
  useQuery({
    queryKey: ANALYSIS_KEYS.result(jobId),
    queryFn: () => analysisApi.getAnalysisResult(jobId),
    enabled: !!jobId,
    select: (res) => res.data,
    staleTime: Infinity, // 결과는 변하지 않으므로 캐시 유지
  });

// ── 타임라인 조회 ─────────────────────────────────────────────────────────────
export const useAnalysisTimeline = (jobId) =>
  useQuery({
    queryKey: ANALYSIS_KEYS.timeline(jobId),
    queryFn: () => analysisApi.getAnalysisTimeline(jobId),
    enabled: !!jobId,
    select: (res) => res.data,
    staleTime: Infinity,
  });

// ── GPT 피드백 조회 ───────────────────────────────────────────────────────────
export const useAnalysisFeedback = (jobId) =>
  useQuery({
    queryKey: ANALYSIS_KEYS.feedback(jobId),
    queryFn: () => analysisApi.getAnalysisFeedback(jobId),
    enabled: !!jobId,
    select: (res) => res.data,
    staleTime: Infinity,
  });

// ── 분석 이력 목록 ────────────────────────────────────────────────────────────
export const useAnalysisHistory = (params = { page: 1, size: 10 }) =>
  useQuery({
    queryKey: ANALYSIS_KEYS.history(params),
    queryFn: () => analysisApi.getAnalysisHistory(params),
    select: (res) => res.data,
    keepPreviousData: true,
  });

// ── 대시보드 통계 ─────────────────────────────────────────────────────────────
export const useAnalysisStats = () =>
  useQuery({
    queryKey: ANALYSIS_KEYS.stats(),
    queryFn: analysisApi.getAnalysisStats,
    select: (res) => res.data,
    staleTime: 1000 * 60 * 3, // 3분
  });

// ── 분석 삭제 ─────────────────────────────────────────────────────────────────
export const useDeleteAnalysis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: analysisApi.deleteAnalysis,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analysis", "history"] });
      queryClient.invalidateQueries({ queryKey: ANALYSIS_KEYS.stats() });
    },
  });
};

// ── 분석 재시도 ───────────────────────────────────────────────────────────────
export const useRetryAnalysis = () => {
  const { startJob } = useAnalysisStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: analysisApi.retryAnalysis,
    onSuccess: (res, jobId) => {
      startJob(jobId);
      navigate(`/analyzing/${jobId}`);
    },
  });
};
