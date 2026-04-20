import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";

// ─────────────────────────────────────────────
// Speacher — UploadPage.jsx
// 의존성: React, Tailwind CSS
// 사용법: <UploadPage onNavigate={(page) => ...} />
// ─────────────────────────────────────────────

const ACCEPTED_FORMATS = ["video/mp4", "video/quicktime", "video/webm", "video/x-msvideo"];
const MAX_SIZE_MB = 500;

const CALIBRATION_STEPS = [
  { icon: "🧍", title: "정자세로 서기", desc: "카메라 정면을 바라보고 어깨를 펴주세요." },
  { icon: "👀", title: "카메라 응시", desc: "영상 시작 후 10초간 카메라를 바라봐 주세요." },
  { icon: "🎙️", title: "아래 문장을 읽어주세요", desc: "\"안녕하세요, 지금부터 발표를 시작하겠습니다.\"" },
];

export default function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const inputRef = useRef(null);

  // ── 파일 유효성 검사 ──
  const validateFile = (f) => {
    if (!ACCEPTED_FORMATS.includes(f.type)) {
      return "MP4, MOV, WEBM, AVI 형식만 지원합니다.";
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      return `파일 크기는 ${MAX_SIZE_MB}MB 이하여야 합니다.`;
    }
    return null;
  };

  const handleFile = (f) => {
    const err = validateFile(f);
    if (err) { setError(err); setFile(null); return; }
    setError("");
    setFile(f);
  };

  // ── 드래그 앤 드롭 ──
  const onDragOver = useCallback((e) => { e.preventDefault(); setDragging(true); }, []);
  const onDragLeave = useCallback(() => setDragging(false), []);
  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  // ── 파일 선택 ──
  const onInputChange = (e) => {
    const f = e.target.files[0];
    if (f) handleFile(f);
  };

  // ── 업로드 시작 ──
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadProgress(0);

    // TODO: 실제 API 연동 (POST /api/v1/analysis)
    // FormData로 파일 전송 후 job_id 받아서 분석 중 페이지로 이동
    for (let i = 0; i <= 100; i += 10) {
      await new Promise((r) => setTimeout(r, 120));
      setUploadProgress(i);
    }

    setUploading(false);
    navigate("/analyzing/demo");
  };

  const formatSize = (bytes) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDuration = (file) => file.name;

  return (
    <div
      className="min-h-screen bg-neutral-950 text-white"
      style={{ fontFamily: "'DM Sans', sans-serif" }}
    >
      {/* 헤더 */}
      <header className="sticky top-0 z-20 bg-neutral-950/90 backdrop-blur border-b border-neutral-800/60 px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => navigate("/dashboard")}
          className="w-9 h-9 rounded-xl bg-neutral-800 hover:bg-neutral-700 flex items-center justify-center text-neutral-400 hover:text-white transition-all duration-150"
        >
          <ArrowLeftIcon />
        </button>
        <h1
          className="text-lg text-white"
          style={{ fontFamily: "'DM Serif Display', serif" }}
        >
          새 분석 시작
        </h1>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-10 space-y-8">

        {/* ── 캘리브레이션 안내 ── */}
        <section className="bg-sky-500/5 border border-sky-500/20 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="w-6 h-6 rounded-full bg-sky-500/20 flex items-center justify-center">
              <InfoIcon />
            </span>
            <h2 className="text-sm font-semibold text-sky-400">촬영 전 캘리브레이션 안내</h2>
          </div>
          <p className="text-neutral-400 text-sm mb-5">
            영상 시작 후 <span className="text-white font-medium">첫 10초</span>는 AI가 개인 기준값을 잡는 구간이에요.
            이 구간은 분석에서 제외되며, 정확한 분석을 위해 아래 사항을 지켜주세요.
          </p>
          <div className="grid grid-cols-3 gap-3">
            {CALIBRATION_STEPS.map((step) => (
              <div
                key={step.title}
                className="bg-neutral-900 border border-neutral-800 rounded-xl p-3 text-center"
              >
                <div className="text-2xl mb-2">{step.icon}</div>
                <div className="text-xs font-medium text-white mb-1">{step.title}</div>
                <div className="text-xs text-neutral-500 leading-relaxed">{step.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── 파일 업로드 영역 ── */}
        <section>
          <h2
            className="text-base font-semibold text-white mb-4"
            style={{ fontFamily: "'DM Serif Display', serif" }}
          >
            발표 영상 업로드
          </h2>

          {/* 드래그 앤 드롭 존 */}
          {!file ? (
            <div
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
              onClick={() => inputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
                dragging
                  ? "border-sky-500 bg-sky-500/5"
                  : "border-neutral-700 hover:border-neutral-500 bg-neutral-900/50 hover:bg-neutral-900"
              }`}
            >
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-all duration-200 ${
                dragging ? "bg-sky-500/20" : "bg-neutral-800"
              }`}>
                <UploadCloudIcon dragging={dragging} />
              </div>
              <p className="text-white font-medium mb-1">
                {dragging ? "여기에 놓으세요!" : "영상 파일을 드래그하거나 클릭하세요"}
              </p>
              <p className="text-neutral-500 text-sm">MP4, MOV, WEBM, AVI · 최대 500MB</p>

              <input
                ref={inputRef}
                type="file"
                accept="video/*"
                className="hidden"
                onChange={onInputChange}
              />
            </div>
          ) : (
            /* 파일 선택됨 */
            <div className="bg-neutral-900 border border-neutral-700 rounded-2xl p-5">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center flex-shrink-0">
                  <VideoIcon />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">{file.name}</div>
                  <div className="text-xs text-neutral-500 mt-0.5">{formatSize(file.size)}</div>
                </div>
                <button
                  onClick={() => { setFile(null); setError(""); }}
                  className="w-8 h-8 rounded-lg bg-neutral-800 hover:bg-red-500/10 hover:text-red-400 flex items-center justify-center text-neutral-500 transition-all duration-150"
                >
                  <XIcon />
                </button>
              </div>

              {/* 업로드 진행바 */}
              {uploading && (
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-neutral-500 mb-1.5">
                    <span>업로드 중...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-neutral-800 rounded-full h-1.5">
                    <div
                      className="bg-sky-500 h-1.5 rounded-full transition-all duration-150"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 에러 메시지 */}
          {error && (
            <div className="mt-3 flex items-center gap-2 text-red-400 text-sm">
              <AlertIcon />
              {error}
            </div>
          )}
        </section>

        {/* ── 분석 항목 안내 ── */}
        <section className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">분석 항목</h3>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "시선 처리율", icon: "👁️", weight: "40점", channel: "시각" },
              { label: "자세 안정성", icon: "🧍", weight: "15점", channel: "시각" },
              { label: "발화 속도",   icon: "⏱️", weight: "16점", channel: "음성" },
              { label: "목소리 크기", icon: "🔊", weight: "13점", channel: "음성" },
              { label: "발음 정확성", icon: "🗣️", weight: "7점",  channel: "어휘" },
              { label: "필러워드",   icon: "💬", weight: "6점",  channel: "어휘" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3 px-3 py-2.5 bg-neutral-800/50 rounded-xl">
                <span className="text-lg">{item.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-white">{item.label}</div>
                  <div className="text-xs text-neutral-500">{item.channel} · {item.weight}</div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── 분석 시작 버튼 ── */}
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className={`w-full py-3.5 rounded-2xl text-sm font-semibold transition-all duration-200 ${
            file && !uploading
              ? "bg-sky-500 hover:bg-sky-400 text-white"
              : "bg-neutral-800 text-neutral-600 cursor-not-allowed"
          }`}
        >
          {uploading ? (
            <span className="flex items-center justify-center gap-2">
              <SpinIcon />
              업로드 중...
            </span>
          ) : (
            "분석 시작하기"
          )}
        </button>

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
function InfoIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round">
      <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  );
}
function UploadCloudIcon({ dragging }) {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={dragging ? "#38bdf8" : "#6b7280"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
    </svg>
  );
}
function VideoIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="23 7 16 12 23 17 23 7" /><rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
    </svg>
  );
}
function XIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
function AlertIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}
function SpinIcon() {
  return (
    <svg className="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
