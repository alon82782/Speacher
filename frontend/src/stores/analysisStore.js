import { create } from "zustand";
import { JOB_STATUS } from "../constants";

/**
 * 분석 진행 상태 전역 스토어
 * - 업로드 진행률, 현재 분석 Job, 폴링 여부 관리
 */
const useAnalysisStore = create((set, get) => ({
  // ── 업로드 상태 ────────────────────────────────────────────────────────────
  uploadProgress: 0,         // 0~100
  selectedFile: null,        // File 객체
  fileTitle: "",             // 발표 제목

  // ── 현재 분석 Job ──────────────────────────────────────────────────────────
  currentJobId: null,
  jobStatus: null,           // JOB_STATUS 값
  currentStep: 0,            // 1~7
  stepProgress: 0,           // 현재 단계 내 진행률 0~100
  isPolling: false,

  // ── Actions ────────────────────────────────────────────────────────────────

  setSelectedFile: (file) => set({ selectedFile: file }),
  setFileTitle: (title) => set({ fileTitle: title }),
  setUploadProgress: (progress) => set({ uploadProgress: progress }),

  /** 분석 시작 시 호출 */
  startJob: (jobId) =>
    set({
      currentJobId: jobId,
      jobStatus: JOB_STATUS.PENDING,
      currentStep: 0,
      stepProgress: 0,
      isPolling: true,
    }),

  /** 폴링 결과 반영 */
  updateJobStatus: ({ status, current_step, step_progress }) =>
    set({
      jobStatus: status,
      currentStep: current_step ?? get().currentStep,
      stepProgress: step_progress ?? 0,
      isPolling: status === JOB_STATUS.PROCESSING || status === JOB_STATUS.PENDING,
    }),

  /** 분석 완료/실패 처리 */
  finishJob: (status) =>
    set({ jobStatus: status, isPolling: false }),

  /** 업로드 페이지 이탈 시 초기화 */
  resetUpload: () =>
    set({ uploadProgress: 0, selectedFile: null, fileTitle: "" }),

  /** 전체 초기화 */
  reset: () =>
    set({
      uploadProgress: 0,
      selectedFile: null,
      fileTitle: "",
      currentJobId: null,
      jobStatus: null,
      currentStep: 0,
      stepProgress: 0,
      isPolling: false,
    }),
}));

export default useAnalysisStore;
