import { useState, useEffect, useRef } from "react";

// ─────────────────────────────────────────────
// Speacher — AnalyzingPage.jsx
// 의존성: React, Tailwind CSS
// 사용법: <AnalyzingPage jobId="abc123" onNavigate={(page) => ...} />
// 백엔드 연동: GET /api/v1/analysis/{jobId}/status 를 2초마다 폴링
// ─────────────────────────────────────────────

const STEPS = [
  { id: 1, label: "녹음 품질 검증",    desc: "SNR 분석 중...",           icon: "🔍" },
  { id: 2, label: "캘리브레이션 처리", desc: "개인 기준값 추출 중...",    icon: "📐" },
  { id: 3, label: "영상 전처리",       desc: "음성/프레임 분리 중...",    icon: "🎬" },
  { id: 4, label: "음성 분석",         desc: "Whisper로 분석 중...",      icon: "🎙️" },
  { id: 5, label: "시각 분석",         desc: "MediaPipe로 분석 중...",    icon: "👁️" },
  { id: 6, label: "점수 계산",         desc: "지표별 점수 산출 중...",    icon: "📊" },
  { id: 7, label: "AI 피드백 생성",    desc: "GPT-4o 피드백 작성 중...", icon: "🤖" },
];

// ── 더미 시뮬레이터 (백엔드 연동 전 테스트용) ──
// 백엔드 연동 시 아래 useDummyProgress를 usePolling으로 교체
const useDummyProgress = (onComplete) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [stepProgress, setStepProgress] = useState(0); // 현재 단계 내 진행도 0~100
  const [done, setDone] = useState(false);

  useEffect(() => {
    let step = 1;
    let progress = 0;
    const interval = setInterval(() => {
      progress += 8;
      if (progress >= 100) {
        progress = 0;
        step += 1;
        if (step > STEPS.length) {
          clearInterval(interval);
          setDone(true);
          setTimeout(() => onComplete?.(), 800);
          return;
        }
        setCurrentStep(step);
      }
      setStepProgress(progress);
    }, 180);
    return () => clearInterval(interval);
  }, []);

  const totalProgress = Math.round(
    ((currentStep - 1) / STEPS.length) * 100 + stepProgress / STEPS.length
  );

  return { currentStep, stepProgress, totalProgress, done };
};

// ── 실제 백엔드 폴링 훅 (백엔드 완성 후 교체용) ──
// const usePolling = (jobId, onComplete) => {
//   const [currentStep, setCurrentStep] = useState(1);
//   const [stepProgress, setStepProgress] = useState(0);
//   const [totalProgress, setTotalProgress] = useState(0);
//   const [done, setDone] = useState(false);
//   useEffect(() => {
//     const poll = async () => {
//       const res = await fetch(`/api/v1/analysis/${jobId}/status`);
//       const data = await res.json();
//       // data: { step: 3, step_progress: 60, total_progress: 35, status: "processing" | "done" }
//       setCurrentStep(data.step);
//       setStepProgress(data.step_progress);
//       setTotalProgress(data.total_progress);
//       if (data.status === "done") { setDone(true); onComplete?.(); }
//     };
//     const id = setInterval(poll, 2000);
//     poll();
//     return () => clearInterval(id);
//   }, [jobId]);
//   return { currentStep, stepProgress, totalProgress, done };
// };

export default function AnalyzingPage({ jobId = "demo", onNavigate }) {
  const { currentStep, stepProgress, totalProgress, done } = useDummyProgress(
    () => onNavigate?.("result")
  );

  return (
    <div
      className="min-h-screen bg-neutral-950 text-white flex flex-col"
      style={{ fontFamily: "'DM Sans', sans-serif" }}
    >
      {/* 헤더 */}
      <header className="border-b border-neutral-800/60 px-6 py-4 flex items-center gap-3">
        <span className="w-7 h-7 rounded-lg bg-sky-500 flex items-center justify-center">
          <MicIcon />
        </span>
        <span
          className="text-white text-lg"
          style={{ fontFamily: "'DM Serif Display', serif" }}
        >
          Speacher
        </span>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="w-full max-w-lg space-y-10">

          {/* 상단 타이틀 */}
          <div className="text-center">
            {done ? (
              <>
                <div className="text-5xl mb-4">✅</div>
                <h2
                  className="text-2xl text-white mb-2"
                  style={{ fontFamily: "'DM Serif Display', serif" }}
                >
                  분석 완료!
                </h2>
                <p className="text-neutral-500 text-sm">결과 페이지로 이동합니다...</p>
              </>
            ) : (
              <>
                <div className="relative w-16 h-16 mx-auto mb-5">
                  {/* 회전 링 */}
                  <svg className="animate-spin w-full h-full" viewBox="0 0 64 64">
                    <circle cx="32" cy="32" r="28" fill="none" stroke="#1f2937" strokeWidth="4" />
                    <circle
                      cx="32" cy="32" r="28"
                      fill="none" stroke="#38bdf8" strokeWidth="4"
                      strokeLinecap="round"
                      strokeDasharray={`${2 * Math.PI * 28 * totalProgress / 100} ${2 * Math.PI * 28}`}
                      strokeDashoffset={2 * Math.PI * 28 * 0.25}
                      style={{ transition: "stroke-dasharray 0.3s ease" }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center text-sky-400 text-sm font-semibold">
                    {totalProgress}%
                  </div>
                </div>
                <h2
                  className="text-2xl text-white mb-2"
                  style={{ fontFamily: "'DM Serif Display', serif" }}
                >
                  발표 영상 분석 중
                </h2>
                <p className="text-neutral-500 text-sm">페이지를 닫지 말고 잠시 기다려주세요.</p>
              </>
            )}
          </div>

          {/* 전체 진행바 */}
          <div>
            <div className="flex justify-between text-xs text-neutral-500 mb-2">
              <span>전체 진행도</span>
              <span>{totalProgress}%</span>
            </div>
            <div className="w-full bg-neutral-800 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-sky-500 to-indigo-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${totalProgress}%` }}
              />
            </div>
          </div>

          {/* 단계별 목록 */}
          <div className="space-y-2">
            {STEPS.map((step) => {
              const isActive = step.id === currentStep && !done;
              const isDone = step.id < currentStep || done;
              const isPending = step.id > currentStep && !done;

              return (
                <div
                  key={step.id}
                  className={`flex items-center gap-4 px-4 py-3 rounded-xl border transition-all duration-300 ${
                    isActive
                      ? "bg-sky-500/5 border-sky-500/30"
                      : isDone
                      ? "bg-neutral-900/50 border-neutral-800/50"
                      : "bg-transparent border-transparent"
                  }`}
                >
                  {/* 아이콘/체크 */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm transition-all duration-300 ${
                    isDone
                      ? "bg-emerald-500/10 border border-emerald-500/20"
                      : isActive
                      ? "bg-sky-500/10 border border-sky-500/30"
                      : "bg-neutral-800 border border-neutral-700"
                  }`}>
                    {isDone ? "✓" : isActive ? (
                      <span className="animate-pulse">{step.icon}</span>
                    ) : (
                      <span className="text-neutral-600">{step.icon}</span>
                    )}
                  </div>

                  {/* 텍스트 */}
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium transition-colors duration-300 ${
                      isDone ? "text-neutral-400" : isActive ? "text-white" : "text-neutral-600"
                    }`}>
                      {step.label}
                    </div>
                    {isActive && (
                      <div className="text-xs text-sky-400 mt-0.5">{step.desc}</div>
                    )}
                  </div>

                  {/* 단계 내 진행바 (현재 단계만) */}
                  {isActive && (
                    <div className="w-20 bg-neutral-800 rounded-full h-1 flex-shrink-0">
                      <div
                        className="bg-sky-500 h-1 rounded-full transition-all duration-200"
                        style={{ width: `${stepProgress}%` }}
                      />
                    </div>
                  )}

                  {/* 완료 표시 */}
                  {isDone && (
                    <span className="text-xs text-emerald-400 flex-shrink-0">완료</span>
                  )}
                </div>
              );
            })}
          </div>

        </div>
      </main>
    </div>
  );
}

function MicIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="22" />
    </svg>
  );
}
