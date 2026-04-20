import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);

// ─────────────────────────────────────────────
// Speacher — ResultDetailPage.jsx (v2)
// 의존성: React, Tailwind CSS, chart.js
// 사용법: <ResultDetailPage onNavigate={(page) => ...} />
// 백엔드 연동: GET /api/v1/analysis/{jobId}/timeline
// ─────────────────────────────────────────────

const TIME_LABELS = [
  "0:00","0:30","1:00","1:30","2:00","2:30","3:00","3:30",
  "4:00","4:30","5:00","5:30","6:00","6:30","7:00","7:30",
  "8:00","8:30","9:00","9:30","10:00","10:30","11:00","11:30","12:00"
];

const DUMMY_TIMELINE = {
  gaze:          [70,75,80,78,82,60,55,72,80,85,83,78,80,75,70,68,82,85,80,78,82,80,75,72,70],
  posture:       [90,88,85,87,83,80,75,78,82,85,83,80,78,75,80,82,85,88,85,82,80,78,75,72,70],
  speed:         [330,340,355,380,370,390,410,360,340,330,345,360,370,355,340,330,345,360,370,380,360,345,335,330,340],
  volume:        [-18,-17,-19,-18,-20,-17,-16,-18,-19,-18,-17,-18,-20,-19,-18,-17,-16,-18,-19,-18,-17,-18,-20,-19,-18],
  pronunciation: [92,91,93,90,88,85,83,87,90,92,91,90,89,88,90,91,92,93,91,90,89,88,87,90,91],
};

const TIMESTAMP_FEEDBACK = {
  1:  { type: "warn",   icon: "👁️", label: "시선 처리율 급락",  metric: "gaze",   desc: "청중 시선이 60% 이하로 떨어졌습니다. 카메라를 더 자주 바라보세요." },
  5:  { type: "warn",   icon: "⏱️", label: "발화 속도 급등",    metric: "speed",  desc: "390 SPM으로 빨라졌습니다. 의식적으로 속도를 줄여보세요." },
  6:  { type: "danger", icon: "⏱️", label: "발화 속도 위험",    metric: "speed",  desc: "410 SPM으로 기준 초과입니다. 잠깐 멈추고 호흡을 고르세요." },
  7:  { type: "warn",   icon: "🧍", label: "자세 불안정",        metric: "posture",desc: "어깨 기울기 변동이 커졌습니다. 자세를 바로잡아주세요." },
  14: { type: "warn",   icon: "👁️", label: "시선 처리율 하락",  metric: "gaze",   desc: "발표 중반 시선 처리율이 70% 이하로 내려왔습니다." },
  21: { type: "good",   icon: "👍", label: "안정적인 구간",      metric: null,     desc: "시선, 자세, 속도 모두 양호한 구간입니다." },
};

const METRICS = [
  { key: "gaze",         label: "시선 처리율", unit: "%",    color: "#38bdf8", yAxis: "y1", default: true },
  { key: "speed",        label: "발화 속도",   unit: "SPM",  color: "#34d399", yAxis: "y2", default: true },
  { key: "volume",       label: "볼륨",        unit: "dBFS", color: "#fb923c", yAxis: "y3", default: true },
  { key: "posture",      label: "자세 안정성", unit: "%",    color: "#a78bfa", yAxis: "y1", default: false },
  { key: "pronunciation",label: "발음 정확성", unit: "%",    color: "#f472b6", yAxis: "y1", default: false },
];

const eventStyle = {
  good:   { border: "border-emerald-500/25", bg: "bg-emerald-500/5",  badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20", text: "text-emerald-400" },
  warn:   { border: "border-amber-500/25",   bg: "bg-amber-500/5",    badge: "bg-amber-500/10  text-amber-400  border-amber-500/20",  text: "text-amber-400"   },
  danger: { border: "border-red-500/25",     bg: "bg-red-500/5",      badge: "bg-red-500/10    text-red-400    border-red-500/20",    text: "text-red-400"     },
  none:   { border: "border-neutral-800",    bg: "bg-neutral-900",    badge: "", text: "text-neutral-400" },
};

export default function ResultDetailPage() {
  const navigate = useNavigate();
  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  const feedbackRef = useRef(null);

  const [activeMetrics, setActiveMetrics] = useState(METRICS.filter((m) => m.default).map((m) => m.key));
  const [selectedIndex, setSelectedIndex] = useState(null);

  const toggleMetric = (key) =>
    setActiveMetrics((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );

  useEffect(() => {
    if (!chartRef.current) return;
    if (chartInstance.current) chartInstance.current.destroy();

    const ctx = chartRef.current.getContext("2d");
    const datasets = METRICS.filter((m) => activeMetrics.includes(m.key)).map((m) => ({
      label: m.label,
      data: DUMMY_TIMELINE[m.key],
      borderColor: m.color,
      backgroundColor: "transparent",
      borderWidth: 2,
      pointRadius: 2,
      pointHoverRadius: 6,
      tension: 0.35,
      fill: false,
      yAxisID: m.yAxis,
    }));

    const markerPlugin = {
      id: "markerPlugin",
      afterDraw(chart) {
        const { ctx: c, scales } = chart;
        Object.entries(TIMESTAMP_FEEDBACK).forEach(([idx, ev]) => {
          const x = scales.x.getPixelForValue(Number(idx));
          const top = scales.y1?.top ?? 0;
          const bottom = scales.y1?.bottom ?? chart.height;
          c.save();
          c.beginPath();
          c.moveTo(x, top);
          c.lineTo(x, bottom);
          c.strokeStyle =
            ev.type === "danger" ? "rgba(239,68,68,0.4)"
            : ev.type === "warn"  ? "rgba(245,158,11,0.4)"
            : "rgba(52,211,153,0.4)";
          c.lineWidth = 1.5;
          c.setLineDash([4, 3]);
          c.stroke();
          c.beginPath();
          c.arc(x, top + 5, 3.5, 0, Math.PI * 2);
          c.fillStyle =
            ev.type === "danger" ? "#ef4444"
            : ev.type === "warn"  ? "#f59e0b"
            : "#34d399";
          c.fill();
          c.restore();
        });
      },
    };

    chartInstance.current = new Chart(ctx, {
      type: "line",
      plugins: [markerPlugin],
      data: { labels: TIME_LABELS, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        onClick(_, elements) {
          if (!elements.length) return;
          const idx = elements[0].index;
          setSelectedIndex(idx);
          setTimeout(() => feedbackRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 50);
        },
        plugins: {
          legend: { labels: { color: "#6b7280", font: { size: 11 }, boxWidth: 10 } },
          tooltip: {
            backgroundColor: "#1f2937",
            titleColor: "#f9fafb",
            bodyColor: "#9ca3af",
            borderColor: "#374151",
            borderWidth: 1,
            callbacks: { title: (items) => `⏱ ${TIME_LABELS[items[0].dataIndex]}` },
          },
        },
        scales: {
          x: {
            ticks: { color: "#4b5563", font: { size: 10 }, maxTicksLimit: 13 },
            grid: { color: "rgba(255,255,255,0.03)" },
          },
          y1: {
            type: "linear", position: "left", min: 0, max: 100,
            ticks: { color: "#4b5563", font: { size: 10 }, callback: (v) => v + "%" },
            grid: { color: "rgba(255,255,255,0.03)" },
            display: activeMetrics.some((k) => ["gaze","posture","pronunciation"].includes(k)),
          },
          y2: {
            type: "linear", position: "right", min: 200, max: 500,
            ticks: { color: "#4b5563", font: { size: 10 } },
            grid: { drawOnChartArea: false },
            display: activeMetrics.includes("speed"),
          },
          y3: {
            type: "linear", position: "right", min: -30, max: 0,
            ticks: { color: "#4b5563", font: { size: 10 }, callback: (v) => v + "dB" },
            grid: { drawOnChartArea: false },
            display: activeMetrics.includes("volume"),
          },
        },
      },
    });

    return () => chartInstance.current?.destroy();
  }, [activeMetrics]);

  const selected = selectedIndex !== null ? {
    time: TIME_LABELS[selectedIndex],
    feedback: TIMESTAMP_FEEDBACK[selectedIndex] ?? null,
    values: Object.fromEntries(METRICS.map((m) => [m.key, DUMMY_TIMELINE[m.key][selectedIndex]])),
  } : null;

  const fb = selected?.feedback;
  const style = fb ? eventStyle[fb.type] : eventStyle.none;

  return (
    <div
      className="min-h-screen bg-neutral-950 text-white"
      style={{ fontFamily: "'DM Sans', sans-serif" }}
    >
      {/* 헤더 */}
      <header className="sticky top-0 z-20 bg-neutral-950/90 backdrop-blur border-b border-neutral-800/60 px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => navigate("/result/demo")}
          className="w-9 h-9 rounded-xl bg-neutral-800 hover:bg-neutral-700 flex items-center justify-center text-neutral-400 hover:text-white transition-all"
        >
          <ArrowLeftIcon />
        </button>
        <div>
          <h1 className="text-base font-semibold text-white" style={{ fontFamily: "'DM Serif Display', serif" }}>
            결과 상세
          </h1>
          <p className="text-xs text-neutral-500">캡스톤 설계 발표 · 타임라인 분석</p>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10 space-y-8">

        {/* ── 타임라인 차트 ── */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
          {/* 차트 헤더 + 토글 */}
          <div className="flex items-start justify-between mb-5">
            <div>
              <h2 className="text-sm font-semibold text-white">지표별 타임라인</h2>
              <p className="text-xs text-neutral-500 mt-1">
                구간 클릭 시 피드백 확인 &nbsp;·&nbsp;
                <span className="text-amber-400">● 주의</span>
                <span className="ml-2 text-red-400">● 위험</span>
                <span className="ml-2 text-emerald-400">● 양호</span>
              </p>
            </div>
            {/* 지표 토글 */}
            <div className="flex flex-wrap gap-1.5 justify-end max-w-xs">
              {METRICS.map((m) => (
                <button
                  key={m.key}
                  onClick={() => toggleMetric(m.key)}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border text-xs transition-all duration-150 ${
                    activeMetrics.includes(m.key)
                      ? "text-white border-neutral-600 bg-neutral-800"
                      : "text-neutral-600 border-neutral-800"
                  }`}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ backgroundColor: activeMetrics.includes(m.key) ? m.color : "#374151" }}
                  />
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div className="h-64">
            <canvas ref={chartRef} />
          </div>
        </div>

        {/* ── 피드백 카드 ── */}
        <div ref={feedbackRef}>
          {selected === null ? (
            <div className="bg-neutral-900 border border-dashed border-neutral-800 rounded-2xl py-14 flex flex-col items-center justify-center text-center">
              <div className="text-3xl mb-3">☝️</div>
              <p className="text-neutral-400 text-sm">차트 구간을 클릭하면</p>
              <p className="text-neutral-600 text-xs mt-1">해당 시점의 피드백이 여기에 표시돼요.</p>
            </div>
          ) : (
            <div className={`border rounded-2xl p-6 transition-all duration-200 ${style.border} ${style.bg}`}>
              {/* 타임코드 */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <span className="text-2xl font-bold text-white" style={{ fontFamily: "'DM Serif Display', serif" }}>
                    {selected.time}
                  </span>
                  {fb && (
                    <span className={`text-xs px-2.5 py-1 rounded-lg border ${style.badge}`}>
                      {fb.type === "good" ? "양호" : fb.type === "warn" ? "주의" : "위험"}
                    </span>
                  )}
                </div>
                <button onClick={() => setSelectedIndex(null)} className="text-neutral-600 hover:text-neutral-400">
                  <XIcon />
                </button>
              </div>

              {/* 이상 지표만 강조 표시 */}
              {fb?.metric ? (
                <div className="flex items-center gap-4 mb-6 p-4 bg-black/20 rounded-xl">
                  {METRICS.filter((m) => m.key === fb.metric).map((m) => (
                    <div key={m.key}>
                      <div className="text-xs text-neutral-500 mb-1">{m.label}</div>
                      <div className="text-2xl font-bold" style={{ color: m.color }}>
                        {selected.values[m.key]}{m.unit}
                      </div>
                    </div>
                  ))}
                  <div className="flex-1" />
                  {/* 나머지 지표는 작게 */}
                  <div className="flex gap-4">
                    {METRICS.filter((m) => m.key !== fb.metric).map((m) => (
                      <div key={m.key} className="text-center">
                        <div className="text-xs text-neutral-600 mb-1">{m.label}</div>
                        <div className="text-sm text-neutral-500">{selected.values[m.key]}{m.unit}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                /* 이상 지표 없을 때 전체 균등 표시 */
                <div className="flex gap-4 mb-6 p-4 bg-black/20 rounded-xl">
                  {METRICS.map((m) => (
                    <div key={m.key} className="flex-1 text-center">
                      <div className="text-xs text-neutral-500 mb-1">{m.label}</div>
                      <div className="text-sm font-semibold" style={{ color: m.color }}>
                        {selected.values[m.key]}{m.unit}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 피드백 텍스트 */}
              {fb ? (
                <div className="flex items-start gap-3">
                  <span className="text-xl mt-0.5">{fb.icon}</span>
                  <div>
                    <div className={`text-sm font-semibold mb-1 ${style.text}`}>{fb.label}</div>
                    <p className="text-sm text-neutral-400 leading-relaxed">{fb.desc}</p>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-neutral-500 text-center">이 구간은 특이사항 없이 안정적으로 진행됐어요. 👌</p>
              )}
            </div>
          )}
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
function XIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
