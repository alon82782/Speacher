import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../stores/authStore";

// ─────────────────────────────────────────────
// Speacher — MyPage.jsx
// 의존성: React, Tailwind CSS
// 사용법: <MyPage onNavigate={(page) => ...} />
// 백엔드 연동:
//   GET    /api/v1/auth/me              → 프로필 조회
//   PUT    /api/v1/auth/me              → 회원정보 수정
//   PUT    /api/v1/auth/me/password     → 비밀번호 변경
//   DELETE /api/v1/auth/me              → 회원 탈퇴
//   POST   /api/v1/auth/logout          → 로그아웃
// ─────────────────────────────────────────────

const DUMMY_USER = {
  name: "홍길동",
  email: "hong@example.com",
  joinedAt: "2026-02-20",
  totalCount: 8,
};

const INPUT_BASE =
  "w-full bg-neutral-800 border border-neutral-700 rounded-xl px-4 py-3 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all duration-200";

export default function MyPage() {
  const navigate = useNavigate();
  const { clearAuth } = useAuthStore();
  const [user, setUser] = useState(DUMMY_USER);

  // 회원정보 수정
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState({ name: user.name, email: user.email });
  const [editError, setEditError] = useState("");

  // 비밀번호 변경
  const [pwOpen, setPwOpen] = useState(false);
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });
  const [pwError, setPwError] = useState("");
  const [pwSuccess, setPwSuccess] = useState(false);

  // 회원 탈퇴 확인
  const [deleteOpen, setDeleteOpen] = useState(false);

  // ── 회원정보 수정 ──
  const handleEditSave = () => {
    if (!editForm.name.trim()) { setEditError("이름을 입력해주세요."); return; }
    if (!editForm.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) { setEditError("올바른 이메일 형식이 아닙니다."); return; }
    // TODO: PUT /api/v1/auth/me
    setUser((u) => ({ ...u, name: editForm.name, email: editForm.email }));
    setEditMode(false);
    setEditError("");
  };

  // ── 비밀번호 변경 ──
  const handlePwChange = () => {
    if (!pwForm.current) { setPwError("현재 비밀번호를 입력해주세요."); return; }
    if (pwForm.next.length < 8) { setPwError("새 비밀번호는 8자 이상이어야 합니다."); return; }
    if (pwForm.next !== pwForm.confirm) { setPwError("새 비밀번호가 일치하지 않습니다."); return; }
    // TODO: PUT /api/v1/auth/me/password
    setPwSuccess(true);
    setPwError("");
    setTimeout(() => { setPwOpen(false); setPwSuccess(false); setPwForm({ current: "", next: "", confirm: "" }); }, 1500);
  };

  return (
    <div
      className="min-h-screen bg-neutral-950 text-white"
      style={{ fontFamily: "'DM Sans', sans-serif" }}
    >
      {/* 헤더 */}
      <header className="sticky top-0 z-20 bg-neutral-950/90 backdrop-blur border-b border-neutral-800/60 px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => navigate("/dashboard")}
          className="w-9 h-9 rounded-xl bg-neutral-800 hover:bg-neutral-700 flex items-center justify-center text-neutral-400 hover:text-white transition-all"
        >
          <ArrowLeftIcon />
        </button>
        <h1 className="text-base font-semibold text-white" style={{ fontFamily: "'DM Serif Display', serif" }}>
          마이페이지
        </h1>
      </header>

      <main className="max-w-lg mx-auto px-6 py-10 space-y-5">

        {/* ── 프로필 카드 ── */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
          {/* 아바타 + 기본 정보 */}
          <div className="flex items-center gap-4 mb-6">
            <div className="w-14 h-14 rounded-2xl bg-sky-500/20 border border-sky-500/30 flex items-center justify-center text-sky-400 text-xl font-bold flex-shrink-0">
              {user.name[0]}
            </div>
            <div>
              <div className="text-lg font-semibold text-white">{user.name}</div>
              <div className="text-sm text-neutral-500">{user.email}</div>
            </div>
          </div>

          {/* 정보 항목 */}
          <div className="space-y-3 text-sm">
            <InfoRow label="가입일" value={user.joinedAt} />
            <InfoRow label="총 분석 횟수" value={`${user.totalCount}회`} />
          </div>

          {/* 회원정보 수정 버튼 */}
          {!editMode ? (
            <button
              onClick={() => { setEditMode(true); setEditForm({ name: user.name, email: user.email }); }}
              className="mt-5 w-full py-2.5 rounded-xl border border-neutral-700 hover:border-neutral-600 text-neutral-400 hover:text-white text-sm transition-all duration-150"
            >
              회원정보 수정
            </button>
          ) : (
            <div className="mt-5 space-y-3">
              <div>
                <label className="text-xs text-neutral-500 mb-1.5 block">이름</label>
                <input
                  value={editForm.name}
                  onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                  className={INPUT_BASE}
                  placeholder="이름"
                />
              </div>
              <div>
                <label className="text-xs text-neutral-500 mb-1.5 block">이메일</label>
                <input
                  value={editForm.email}
                  onChange={(e) => setEditForm((f) => ({ ...f, email: e.target.value }))}
                  className={INPUT_BASE}
                  placeholder="이메일"
                />
              </div>
              {editError && <p className="text-xs text-red-400">{editError}</p>}
              <div className="flex gap-2">
                <button
                  onClick={handleEditSave}
                  className="flex-1 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-sm font-semibold transition-all"
                >
                  저장
                </button>
                <button
                  onClick={() => { setEditMode(false); setEditError(""); }}
                  className="flex-1 py-2.5 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-400 text-sm transition-all"
                >
                  취소
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── 비밀번호 변경 ── */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-sm font-semibold text-white">비밀번호 변경</h2>
            <button
              onClick={() => { setPwOpen((v) => !v); setPwError(""); setPwSuccess(false); }}
              className="text-xs text-sky-500 hover:text-sky-400 transition-colors"
            >
              {pwOpen ? "접기" : "변경하기"}
            </button>
          </div>
          <p className="text-xs text-neutral-500 mb-4">주기적으로 비밀번호를 변경하면 계정을 안전하게 유지할 수 있어요.</p>

          {pwOpen && (
            <div className="space-y-3">
              {[
                { key: "current", label: "현재 비밀번호", placeholder: "현재 비밀번호 입력" },
                { key: "next",    label: "새 비밀번호",   placeholder: "8자 이상" },
                { key: "confirm", label: "새 비밀번호 확인", placeholder: "동일하게 입력" },
              ].map(({ key, label, placeholder }) => (
                <div key={key}>
                  <label className="text-xs text-neutral-500 mb-1.5 block">{label}</label>
                  <input
                    type="password"
                    value={pwForm[key]}
                    onChange={(e) => setPwForm((f) => ({ ...f, [key]: e.target.value }))}
                    placeholder={placeholder}
                    className={INPUT_BASE}
                  />
                </div>
              ))}
              {pwError && <p className="text-xs text-red-400">{pwError}</p>}
              {pwSuccess && <p className="text-xs text-emerald-400">비밀번호가 변경됐어요!</p>}
              <button
                onClick={handlePwChange}
                className="w-full py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-sm font-semibold transition-all"
              >
                변경하기
              </button>
            </div>
          )}
        </div>

        {/* ── 로그아웃 / 회원탈퇴 ── */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 space-y-3">
          {/* 로그아웃 */}
          <button
            onClick={() => { clearAuth(); navigate("/"); }}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-neutral-800 text-neutral-400 hover:text-white text-sm transition-all group"
          >
            <div className="flex items-center gap-3">
              <LogoutIcon />
              로그아웃
            </div>
            <ChevronRightIcon />
          </button>

          <div className="border-t border-neutral-800" />

          {/* 회원 탈퇴 */}
          {!deleteOpen ? (
            <button
              onClick={() => setDeleteOpen(true)}
              className="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-red-500/5 text-neutral-600 hover:text-red-400 text-sm transition-all group"
            >
              <div className="flex items-center gap-3">
                <TrashIcon />
                회원 탈퇴
              </div>
              <ChevronRightIcon />
            </button>
          ) : (
            <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
              <p className="text-sm text-red-400 font-semibold mb-1">정말 탈퇴하시겠어요?</p>
              <p className="text-xs text-neutral-500 mb-4">탈퇴 시 모든 분석 데이터가 삭제되며 복구할 수 없어요.</p>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    // TODO: DELETE /api/v1/auth/me
                    navigate("/");
                  }}
                  className="flex-1 py-2 rounded-xl bg-red-500 hover:bg-red-400 text-white text-sm font-semibold transition-all"
                >
                  탈퇴하기
                </button>
                <button
                  onClick={() => setDeleteOpen(false)}
                  className="flex-1 py-2 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-400 text-sm transition-all"
                >
                  취소
                </button>
              </div>
            </div>
          )}
        </div>

      </main>
    </div>
  );
}

// ── 서브 컴포넌트 ──
function InfoRow({ label, value }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-neutral-800 last:border-0">
      <span className="text-neutral-500">{label}</span>
      <span className="text-white">{value}</span>
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
function ChevronRightIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
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
function TrashIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" /><path d="M10 11v6M14 11v6" /><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </svg>
  );
}
