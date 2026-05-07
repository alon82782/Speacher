import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../stores/authStore";
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);

// ─────────────────────────────────────────────
// Speacher — Dashboard.jsx
// 의존성: React, Tailwind CSS, chart.js
// 설치: npm install chart.js
// 사용법: <Dashboard user={{ name: "홍길동" }} onNavigate={(page) => ...} />
// ─────────────────────────────────────────────

// ── 더미 데이터 (백엔드 연동 시 API로 교체) ──
const DUMMY_STATS = {
  totalCount: 12,
  recentAvg: 82,       // 최근 3회 평균
  previousAvg: 71,     // 이전 3회 평균
  diff: 11,            // 변화량
  bestScore: 91,
  lastDate: "2026-03-20",
};

const DUMMY_HISTORY = [
  { id: 1, title: "팀 프로젝트 중간 발표", date: "2026-03-20", score: 91, duration: "8분 32초" },
  { id: 2, title: "캡스톤 설계 발표",     date: "2026-03-18", score: 88, duration: "12분 05초" },
  { id: 3, title: "모의 발표 연습 #3",    date: "2026-03-15", score: 82, duration: "6분 44초" },
  { id: 4, title: "모의 발표 연습 #2",    date: "2026-03-10", score: 78, duration: "7분 11초" },
  { id: 5, title: "모의 발표 연습 #1",    date: "2026-03-05", score: 70, duration: "5분 58초" },
];

const DUMMY_CHART = {
  labels: ["3/05", "3/10", "3/15", "3/18", "3/20"],
  scores: [70, 78, 82, 88, 91],
  movingAvg: [null, null, 76.7, 82.7, 87.0], // 최근 3회 이동 평균
};

// ── 점수 등급 색상 ──
const scoreColor = (score) => {
  if (score >= 85) return "text-emerald-400";
  if (score >= 70) return "text-sky-400";
  if (score >= 55) return "text-amber-400";
  return "text-red-400";
};

const scoreBadgeBg = (score) => {
  if (score >= 85) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  if (score >= 70) return "bg-sky-500/10 text-sky-400 border-sky-500/20";
  if (score >= 55) return "bg-amber-500/10 text-amber-400 border-amber-500/20";
  return "bg-red-500/10 text-red-400 border-red-500/20";
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { user: rawUser, clearAuth } = useAuthStore();
  const user = { name: rawUser?.name ?? "사용자", ...rawUser };
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  // ── 차트 초기화 ──
  useEffect(() => {
    if (!chartRef.current) return;
    if (chartInstance.current) chartInstance.current.destroy();

    const ctx = chartRef.current.getContext("2d");
    chartInstance.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: DUMMY_CHART.labels,
        datasets: [
          {
            label: "점수",
            data: DUMMY_CHART.scores,
            borderColor: "#38bdf8",
            backgroundColor: "rgba(56,189,248,0.08)",
            borderWidth: 2,
            pointBackgroundColor: "#38bdf8",
            pointRadius: 5,
            pointHoverRadius: 7,
            tension: 0.3,
            fill: true,
          },
          {
            label: "3회 이동 평균",
            data: DUMMY_CHART.movingAvg,
            borderColor: "#a78bfa",
            borderWidth: 2,
            borderDash: [5, 4],
            pointRadius: 0,
            pointHoverRadius: 0,
            tension: 0.3,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: "#9ca3af", font: { size: 12 }, boxWidth: 16 },
          },
          tooltip: {
            backgroundColor: "#1f2937",
            titleColor: "#f9fafb",
            bodyColor: "#9ca3af",
            borderColor: "#374151",
            borderWidth: 1,
          },
        },
        scales: {
          x: {
            ticks: { color: "#6b7280", font: { size: 11 } },
            grid: { color: "rgba(255,255,255,0.04)" },
          },
          y: {
            min: 40,
            max: 100,
            ticks: { color: "#6b7280", font: { size: 11 } },
            grid: { color: "rgba(255,255,255,0.04)" },
          },
        },
      },
    });

    return () => chartInstance.current?.destroy();
  }, []);

  const nav = (page) => {
    setSidebarOpen(false);
    if (page === "logout") {
      clearAuth();
      navigate("/");
    } else if (page === "dashboard") {
      navigate("/dashboard");
    } else if (page === "upload") {
      navigate("/upload");
    } else if (page === "history") {
      navigate("/history");
    } else if (page === "mypage") {
      navigate("/mypage");
    } else if (page === "result") {
      navigate("/result/demo");
    } else {
      navigate("/" + page);
    }
  };

  const diffSign = DUMMY_STATS.diff >= 0 ? "+" : "";

  return (
    <div
      className="min-h-screen bg-neutral-950 text-white"
      style={{ fontFamily: "'DM Sans', sans-serif" }}
    >
      {/* ── 사이드바 오버레이 ── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── 사이드바 ── */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-neutral-900 border-r border-neutral-800 z-40 flex flex-col transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* 사이드바 헤더 */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-neutral-800">
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 rounded-lg bg-sky-500 flex items-center justify-center">
              <MicIcon size={14} />
            </span>
            <span
              className="text-white text-lg"
              style={{ fontFamily: "'DM Serif Display', serif" }}
            >
              Speacher
            </span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="text-neutral-500 hover:text-white transition-colors"
          >
            <XIcon />
          </button>
        </div>

        {/* 사용자 정보 */}
        <div className="px-5 py-4 border-b border-neutral-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-sky-500/20 border border-sky-500/30 flex items-center justify-center text-sky-400 text-sm font-semibold">
              {user.name[0]}
            </div>
            <div>
              <div className="text-sm font-medium text-white">{user.name}</div>
              <div className="text-xs text-neutral-500">발표자</div>
            </div>
          </div>
        </div>

        {/* 네비게이션 */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {[
            { icon: <HomeIcon />, label: "대시보드", page: "dashboard", active: true },
            { icon: <UploadIcon />, label: "영상 업로드", page: "upload" },
            { icon: <HistoryIcon />, label: "분석 이력", page: "history" },
            { icon: <UserIcon />, label: "마이페이지", page: "mypage" },
          ].map(({ icon, label, page, active }) => (
            <button
              key={page}
              onClick={() => nav(page)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-150 ${
                active
                  ? "bg-sky-500/10 text-sky-400 border border-sky-500/20"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-800"
              }`}
            >
              {icon}
              {label}
            </button>
          ))}
        </nav>

        {/* 로그아웃 */}
        <div className="px-3 py-4 border-t border-neutral-800">
          <button
            onClick={() => nav("logout")}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-neutral-500 hover:text-red-400 hover:bg-red-500/5 transition-all duration-150"
          >
            <LogoutIcon />
            로그아웃
          </button>
        </div>
      </aside>

      {/* ── 메인 콘텐츠 ── */}
      <div className="flex flex-col min-h-screen">

        {/* 상단 헤더 */}
        <header className="sticky top-0 z-20 bg-neutral-950/90 backdrop-blur border-b border-neutral-800/60 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="w-9 h-9 rounded-xl bg-neutral-800 hover:bg-neutral-700 flex items-center justify-center text-neutral-400 hover:text-white transition-all duration-150"
            >
              <HamburgerIcon />
            </button>
            <h1
              className="text-lg text-white"
              style={{ fontFamily: "'DM Serif Display', serif" }}
            >
              대시보드
            </h1>
          </div>

          <button
            onClick={() => nav("upload")}
            className="flex items-center gap-2 bg-sky-500 hover:bg-sky-400 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-all duration-150"
          >
            <PlusIcon />
            새 분석 시작
          </button>
        </header>

        {/* 본문 */}
        <main className="flex-1 px-6 py-8 max-w-5xl mx-auto w-full space-y-8">

          {/* 환영 메시지 */}
          <div>
            <h2
              className="text-2xl text-white mb-1"
              style={{ fontFamily: "'DM Serif Display', serif" }}
            >
              안녕하세요, {user.name}님 👋
            </h2>
            <p className="text-neutral-500 text-sm">
              마지막 분석일: {DUMMY_STATS.lastDate} · 총 {DUMMY_STATS.totalCount}회 분석
            </p>
          </div>

          {/* 통계 카드 4개 */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 최근 3회 평균 */}
            <StatCard
              label="최근 3회 평균"
              value={`${DUMMY_STATS.recentAvg}점`}
              sub={
                <span className={DUMMY_STATS.diff >= 0 ? "text-emerald-400" : "text-red-400"}>
                 지난 3회 대비 {diffSign}{DUMMY_STATS.diff}점
                 </span>
}
              accent="sky"
            />
            {/* 최고 점수 */}
            <StatCard
              label="최고 점수"
              value={`${DUMMY_STATS.bestScore}점`}
              sub={<span className="text-neutral-500">역대 최고</span>}
              accent="emerald"
            />
            {/* 총 분석 횟수 */}
            <StatCard
              label="총 분석 횟수"
              value={`${DUMMY_STATS.totalCount}회`}
              sub={<span className="text-neutral-500">누적 연습량</span>}
              accent="violet"
            />
            {/* 최근 분석일 */}
            <StatCard
              label="최근 분석일"
              value={DUMMY_STATS.lastDate}
              sub={<span className="text-neutral-500">마지막 연습</span>}
              accent="amber"
              small
            />
          </div>

          {/* 점수 추이 차트 */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-white font-semibold">점수 추이</h3>
                <p className="text-neutral-500 text-xs mt-0.5">최근 5회 발표 · 3회 이동 평균 포함</p>
              </div>
            </div>
            <div className="h-52">
              <canvas ref={chartRef} />
            </div>
          </div>

          {/* 최근 분석 이력 */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-white font-semibold">최근 분석 이력</h3>
                <p className="text-neutral-500 text-xs mt-0.5">최근 5회</p>
              </div>
              <button
                onClick={() => nav("history")}
                className="text-xs text-sky-500 hover:text-sky-400 transition-colors"
              >
                전체 보기 →
              </button>
            </div>

            <div className="space-y-3">
              {DUMMY_HISTORY.map((item, i) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between px-4 py-3 bg-neutral-800/50 hover:bg-neutral-800 border border-neutral-700/50 rounded-xl transition-all duration-150 group"
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <div className="flex items-center gap-4">
                    {/* 순위 번호 */}
                    <span className="text-xs text-neutral-600 w-4 text-center">{i + 1}</span>
                    <div>
                      <div className="text-sm text-white font-medium">{item.title}</div>
                      <div className="text-xs text-neutral-500 mt-0.5">
                        {item.date} · {item.duration}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-semibold px-2.5 py-1 rounded-lg border text-xs ${scoreBadgeBg(item.score)}`}>
                      {item.score}점
                    </span>
                    <button
                      onClick={() => nav("result")}
                      className="text-xs text-neutral-500 hover:text-sky-400 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      상세 →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}

// ── StatCard ──
function StatCard({ label, value, sub, accent, small }) {
  const accents = {
    sky:     "from-sky-500/10 to-transparent border-sky-500/20 text-sky-400",
    emerald: "from-emerald-500/10 to-transparent border-emerald-500/20 text-emerald-400",
    violet:  "from-violet-500/10 to-transparent border-violet-500/20 text-violet-400",
    amber:   "from-amber-500/10 to-transparent border-amber-500/20 text-amber-400",
  };
  return (
    <div className={`bg-gradient-to-br ${accents[accent]} border rounded-2xl p-4`}>
      <div className="text-xs text-neutral-500 mb-2">{label}</div>
      <div className={`font-semibold mb-1 ${small ? "text-lg" : "text-2xl"} ${accents[accent].split(" ").pop()}`}>
        {value}
      </div>
      <div className="text-xs">{sub}</div>
    </div>
  );
}

// ── 아이콘 ──
function MicIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="22" />
    </svg>
  );
}
function HamburgerIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}
function XIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
function HomeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  );
}
function UploadIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
    </svg>
  );
}
function HistoryIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="12 8 12 12 14 14" /><path d="M3.05 11a9 9 0 1 1 .5 4m-.5 5v-5h5" />
    </svg>
  );
}
function UserIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
    </svg>
  );
}
function LogoutIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}
function PlusIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}
