import { useState } from "react";

// ─────────────────────────────────────────────
// Speacher — HistoryPage.jsx
// 의존성: React, Tailwind CSS
// 사용법: <HistoryPage onNavigate={(page) => ...} />
// 백엔드 연동: GET /api/v1/analysis/history
// ─────────────────────────────────────────────

// ── 더미 데이터 (백엔드 연동 시 API로 교체) ──
const DUMMY_HISTORY = [
  { id: 1, title: "캡스톤 설계 발표",       date: "2026-03-23", duration: "12분 05초", score: 88 },
  { id: 2, title: "팀 프로젝트 중간 발표",   date: "2026-03-20", duration: "8분 32초",  score: 91 },
  { id: 3, title: "모의 발표 연습 #5",      date: "2026-03-18", duration: "10분 14초", score: 82 },
  { id: 4, title: "모의 발표 연습 #4",      date: "2026-03-15", duration: "9분 47초",  score: 75 },
  { id: 5, title: "소프트웨어공학 발표",     date: "2026-03-10", duration: "15분 20초", score: 70 },
  { id: 6, title: "모의 발표 연습 #3",      date: "2026-03-05", duration: "7분 58초",  score: 65 },
  { id: 7, title: "모의 발표 연습 #2",      date: "2026-02-28", duration: "6분 33초",  score: 60 },
  { id: 8, title: "모의 발표 연습 #1",      date: "2026-02-20", duration: "5분 12초",  score: 55 },
];

const scoreBadge = (score) => {
  if (score >= 90) return { bg: "bg-amber-500/10  border-amber-500/20  text-amber-400",  grade: "S" };
  if (score >= 80) return { bg: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400", grade: "A" };
  if (score >= 70) return { bg: "bg-sky-500/10    border-sky-500/20    text-sky-400",    grade: "B" };
  if (score >= 55) return { bg: "bg-amber-500/10  border-amber-500/20  text-amber-400",  grade: "C" };
  return               { bg: "bg-red-500/10    border-red-500/20    text-red-400",    grade: "D" };
};

export default function HistoryPage({ onNavigate }) {
  const [sort, setSort] = useState("newest"); // "newest" | "oldest"

  const sorted = [...DUMMY_HISTORY].sort((a, b) => {
    if (sort === "newest") return new Date(b.date) - new Date(a.date);
    return new Date(a.date) - new Date(b.date);
  });

  return (
    <div
      className="min-h-screen bg-neutral-950 text-white"
      style={{ fontFamily: "'DM Sans', sans-serif" }}
    >
      {/* 헤더 */}
      <header className="sticky top-0 z-20 bg-neutral-950/90 backdrop-blur border-b border-neutral-800/60 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => onNavigate?.("dashboard")}
            className="w-9 h-9 rounded-xl bg-neutral-800 hover:bg-neutral-700 flex items-center justify-center text-neutral-400 hover:text-white transition-all"
          >
            <ArrowLeftIcon />
          </button>
          <div>
            <h1 className="text-base font-semibold text-white" style={{ fontFamily: "'DM Serif Display', serif" }}>
              분석 이력
            </h1>
            <p className="text-xs text-neutral-500">총 {DUMMY_HISTORY.length}개</p>
          </div>
        </div>

        {/* 날짜순 정렬 토글 */}
        <div className="flex items-center bg-neutral-900 border border-neutral-800 rounded-xl p-1">
          {[
            { key: "newest", label: "최신순" },
            { key: "oldest", label: "오래된순" },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setSort(key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                sort === key
                  ? "bg-neutral-800 text-white"
                  : "text-neutral-500 hover:text-neutral-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8">
        <div className="space-y-3">
          {sorted.map((item, i) => {
            const badge = scoreBadge(item.score);
            return (
              <button
                key={item.id}
                onClick={() => onNavigate?.("result")}
                className="w-full flex items-center gap-4 px-5 py-4 bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 hover:border-neutral-700 rounded-2xl transition-all duration-150 group text-left"
              >
                {/* 번호 */}
                <span className="text-xs text-neutral-600 w-5 text-center flex-shrink-0">
                  {i + 1}
                </span>

                {/* 정보 */}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate mb-1">
                    {item.title}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-neutral-500">
                    <span>{item.date}</span>
                    <span>·</span>
                    <span>{item.duration}</span>
                  </div>
                </div>

                {/* 점수 + 등급 */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-lg border ${badge.bg}`}>
                    {badge.grade}등급
                  </span>
                  <span className={`text-sm font-bold ${badge.bg.split(" ").pop()}`}>
                    {item.score}점
                  </span>
                </div>

                {/* 화살표 */}
                <ChevronRightIcon />
              </button>
            );
          })}
        </div>
      </main>
    </div>
  );
}

function ArrowLeftIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
    </svg>
  );
}
function ChevronRightIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-600 group-hover:text-neutral-400 transition-colors flex-shrink-0">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}
