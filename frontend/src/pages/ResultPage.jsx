import { useState } from "react";
import { useNavigate } from "react-router-dom";

// ─────────────────────────────────────────────
// Speacher — ResultPage.jsx
// 의존성: React, Tailwind CSS
// 사용법: <ResultPage onNavigate={(page) => ...} />
// 백엔드 연동: GET /api/v1/analysis/{jobId}/result
// ─────────────────────────────────────────────

// ── 더미 데이터 (백엔드 연동 시 API로 교체) ──
const DUMMY_RESULT = {
  title: "캡스톤 설계 발표",
  date: "2026-03-23",
  duration: "12분 05초",
  totalScore: 82,

  // 채널별 점수
  channels: {
    visual: { score: 44, max: 55, label: "시각" },
    audio:  { score: 28, max: 35, label: "음성" },
    lexical:{ score: 5,  max: 7,  label: "어휘" },
    delivery:{ score: 2, max: 3,  label: "전달" },
  },

  // 지표별 점수
  metrics: [
    { label: "시선 처리율",  score: 32, max: 40, channel: "visual",   value: "80%",     status: "good" },
    { label: "자세 안정성",  score: 12, max: 15, channel: "visual",   value: "변동폭 8%", status: "good" },
    { label: "발화 속도",    score: 10, max: 12, channel: "audio",    value: "342 SPM",  status: "good" },
    { label: "발화 속도 변화율", score: 2, max: 4, channel: "audio",  value: "±52 SPM",  status: "warn" },
    { label: "목소리 크기",  score: 5,  max: 7,  channel: "audio",    value: "-18 dBFS", status: "good" },
    { label: "볼륨 변화율",  score: 2,  max: 3,  channel: "audio",    value: "±4.2 dB",  status: "warn" },
    { label: "필러워드",     score: 3,  max: 7,  channel: "lexical",  value: "14회",     status: "danger" },
    { label: "발음 정확성",  score: 5,  max: 6,  channel: "lexical",  value: "WER 8%",   status: "good" },
    { label: "시간 준수",    score: 2,  max: 3,  channel: "delivery", value: "12분 05초", status: "good" },
  ],

  // GPT 피드백
  feedback: {
    summary: "전반적으로 안정적인 발표였습니다. 시선 처리와 발화 속도는 양호하나, 필러워드 사용이 빈번하고 발화 속도 변화율이 다소 높아 개선이 필요합니다.",
    priority: {
      label: "필러워드 줄이기",
      detail: "\"음\", \"어\", \"그\" 등의 필러워드가 14회 감지됐습니다. 발표 전 스크립트를 충분히 숙지하고, 막히는 구간에서 잠깐 멈추는 연습을 해보세요.",
    },
    positives: [
      "시선 처리율 80%로 청중과의 눈맞춤이 잘 이루어졌습니다.",
      "발화 속도 342 SPM으로 적절한 속도를 유지했습니다.",
      "자세 변동폭 8%로 안정적인 자세를 유지했습니다.",
    ],
    improvements: [
      "필러워드 14회 → 6회 이하로 줄이는 것을 목표로 연습하세요.",
      "발화 속도 변화가 ±52 SPM으로 구간별 편차가 있습니다. 일정한 속도를 유지해보세요.",
    ],
  },
};

// ── 등급 계산 ──
const getGrade = (score) => {
  if (score >= 90) return { label: "S", color: "text-amber-400",  bg: "bg-amber-500/10  border-amber-500/20" };
  if (score >= 80) return { label: "A", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" };
  if (score >= 70) return { label: "B", color: "text-sky-400",    bg: "bg-sky-500/10    border-sky-500/20" };
  if (score >= 55) return { label: "C", color: "text-amber-400",  bg: "bg-amber-500/10  border-amber-500/20" };
  return              { label: "D", color: "text-red-400",    bg: "bg-red-500/10    border-red-500/20" };
};

const statusStyle = {
  good:   "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  warn:   "text-amber-400  bg-amber-500/10  border-amber-500/20",
  danger: "text-red-400    bg-red-500/10    border-red-500/20",
};
const statusLabel = { good: "양호", warn: "주의", danger: "위험" };

const channelColor = {
  visual:   "bg-sky-500",
  audio:    "bg-violet-500",
  lexical:  "bg-emerald-500",
  delivery: "bg-amber-500",
};
const channelBg = {
  visual:   "bg-sky-500/10 border-sky-500/20 text-sky-400",
  audio:    "bg-violet-500/10 border-violet-500/20 text-violet-400",
  lexical:  "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
  delivery: "bg-amber-500/10 border-amber-500/20 text-amber-400",
};

export default function ResultPage() {
  const navigate = useNavigate();
  const r = DUMMY_RESULT;
  const grade = getGrade(r.totalScore);

  return (
    <div
      className="min-h-screen bg-neutral-950 text-white"
      style={{ fontFamily: "'DM Sans', sans-serif" }}
    >
      {/* 헤더 */}
      <header className="sticky top-0 z-20 bg-neutral-950/90 backdrop-blur border-b border-neutral-800/60 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/dashboard")}
            className="w-9 h-9 rounded-xl bg-neutral-800 hover:bg-neutral-700 flex items-center justify-center text-neutral-400 hover:text-white transition-all duration-150"
          >
            <ArrowLeftIcon />
          </button>
          <div>
            <h1 className="text-base font-semibold text-white" style={{ fontFamily: "'DM Serif Display', serif" }}>
              분석 결과
            </h1>
            <p className="text-xs text-neutral-500">{r.title} · {r.date} · {r.duration}</p>
          </div>
        </div>

        {/* 결과 상세 버튼 */}
        <button
          onClick={() => navigate("/result/demo/detail")}
          className="flex items-center gap-2 bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-sm text-neutral-300 hover:text-white px-4 py-2 rounded-xl transition-all duration-150"
        >
          <ChartIcon />
          결과 상세 보기
        </button>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8 space-y-6">

        {/* ── 종합 점수 카드 ── */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 flex items-center gap-6">
          {/* 점수 원형 */}
          <div className="relative w-24 h-24 flex-shrink-0">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 96 96">
              <circle cx="48" cy="48" r="40" fill="none" stroke="#1f2937" strokeWidth="8" />
              <circle
                cx="48" cy="48" r="40"
                fill="none"
                stroke="#38bdf8"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 40 * r.totalScore / 100} ${2 * Math.PI * 40}`}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-white">{r.totalScore}</span>
              <span className="text-xs text-neutral-500">/ 100</span>
            </div>
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className={`text-2xl font-bold ${grade.color}`}>{grade.label}등급</span>
              <span className={`text-xs px-2 py-0.5 rounded-lg border ${grade.bg} ${grade.color}`}>
                {r.totalScore}점
              </span>
            </div>
            <p className="text-sm text-neutral-400 leading-relaxed">{r.feedback.summary}</p>
          </div>
        </div>

        {/* ── 채널별 점수 ── */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-white mb-4">채널별 점수</h2>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(r.channels).map(([key, ch]) => {
              const pct = Math.round((ch.score / ch.max) * 100);
              return (
                <div key={key} className={`border rounded-xl p-4 ${channelBg[key]}`}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-medium">{ch.label}</span>
                    <span className="text-sm font-bold">{ch.score}<span className="text-xs font-normal opacity-60">/{ch.max}</span></span>
                  </div>
                  <div className="w-full bg-black/20 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${channelColor[key]} transition-all duration-500`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── 지표별 점수 ── */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-white mb-4">지표별 점수</h2>
          <div className="space-y-2">
            {r.metrics.map((m) => {
              const pct = Math.round((m.score / m.max) * 100);
              return (
                <div key={m.label} className="flex items-center gap-3 py-2 border-b border-neutral-800 last:border-0">
                  <div className="w-24 text-xs text-neutral-400 flex-shrink-0">{m.label}</div>
                  <div className="flex-1 bg-neutral-800 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-500 ${channelColor[m.channel]}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="w-16 text-xs text-neutral-400 text-right flex-shrink-0">{m.value}</div>
                  <span className={`text-xs px-2 py-0.5 rounded-lg border flex-shrink-0 ${statusStyle[m.status]}`}>
                    {statusLabel[m.status]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── 핵심 개선 포인트 ── */}
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-amber-400 text-lg">⚡</span>
            <h2 className="text-sm font-semibold text-amber-400">핵심 개선 포인트</h2>
          </div>
          <div className="font-medium text-white text-sm mb-2">{r.feedback.priority.label}</div>
          <p className="text-neutral-400 text-sm leading-relaxed">{r.feedback.priority.detail}</p>
        </div>

        {/* ── 잘한 점 / 개선할 점 ── */}
        <div className="grid grid-cols-1 gap-4">
          {/* 잘한 점 */}
          <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-emerald-400">👍</span>
              <h2 className="text-sm font-semibold text-emerald-400">잘한 점</h2>
            </div>
            <ul className="space-y-2">
              {r.feedback.positives.map((p, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-neutral-400">
                  <span className="text-emerald-500 mt-0.5 flex-shrink-0">✓</span>
                  {p}
                </li>
              ))}
            </ul>
          </div>

          {/* 개선할 점 */}
          <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-red-400">📌</span>
              <h2 className="text-sm font-semibold text-red-400">개선할 점</h2>
            </div>
            <ul className="space-y-2">
              {r.feedback.improvements.map((p, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-neutral-400">
                  <span className="text-red-400 mt-0.5 flex-shrink-0">→</span>
                  {p}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* ── 하단 버튼 ── */}
        <div className="grid grid-cols-2 gap-3 pb-6">
          <button
            onClick={() => navigate("/result/demo/detail")}
            className="flex items-center justify-center gap-2 bg-sky-500 hover:bg-sky-400 text-white text-sm font-semibold py-3 rounded-xl transition-all duration-150"
          >
            <ChartIcon />
            결과 상세 보기
          </button>
          <button
            onClick={() => navigate("/upload")}
            className="flex items-center justify-center gap-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 hover:text-white text-sm font-semibold py-3 rounded-xl transition-all duration-150"
          >
            <RetryIcon />
            다시 분석하기
          </button>
        </div>

      </main>
    </div>
  );
}

// ── 아이콘 ──
function ArrowLeftIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
    </svg>
  );
}
function ChartIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}
function RetryIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1 4 1 10 7 10" /><path d="M3.51 15a9 9 0 1 0 .49-4" />
    </svg>
  );
}
