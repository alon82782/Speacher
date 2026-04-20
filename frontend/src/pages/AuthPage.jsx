import { useState } from "react";
import { useLogin, useRegister } from "../hooks/useAuth";

const INPUT_BASE =
  "w-full bg-neutral-900 border border-neutral-700 rounded-xl px-4 py-3 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all duration-200";

const BTN_PRIMARY =
  "w-full bg-sky-500 hover:bg-sky-400 active:bg-sky-600 text-white font-semibold text-sm rounded-xl py-3 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 focus:ring-offset-neutral-950";

export default function AuthPage() {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const loginMutation = useLogin();
  const registerMutation = useRegister();

  const isLogin = mode === "login";

  const validate = () => {
    const e = {};
    if (!isLogin && !form.name.trim()) e.name = "이름을 입력해주세요.";
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) e.email = "올바른 이메일 형식이 아닙니다.";
    if (form.password.length < 8) e.password = "비밀번호는 8자 이상이어야 합니다.";
    if (!isLogin && form.password !== form.confirm) e.confirm = "비밀번호가 일치하지 않습니다.";
    return e;
  };

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
    setErrors((err) => ({ ...err, [e.target.name]: undefined }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setLoading(true);
    try {
      if (isLogin) {
        await loginMutation.mutateAsync({ email: form.email, password: form.password });
      } else {
        await registerMutation.mutateAsync({ email: form.email, password: form.password, name: form.name });
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || "오류가 발생했습니다.";
      setErrors({ email: msg });
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(isLogin ? "signup" : "login");
    setForm({ name: "", email: "", password: "", confirm: "" });
    setErrors({});
  };

  return (
    <div className="min-h-screen bg-neutral-950 flex" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      {/* 왼쪽: 브랜딩 패널 */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-neutral-900 via-neutral-950 to-neutral-900" />
        <div className="absolute top-[-80px] left-[-80px] w-72 h-72 rounded-full bg-sky-500/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-[-60px] right-[-60px] w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
        <div className="relative z-10 flex items-center gap-2">
          <span className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center"><MicIcon /></span>
          <span className="text-white text-xl tracking-tight" style={{ fontFamily: "'DM Serif Display', serif" }}>Speacher</span>
        </div>
        <div className="relative z-10">
          <h2 className="text-5xl text-white leading-tight mb-6" style={{ fontFamily: "'DM Serif Display', serif" }}>
            발표를 분석하고,<br />
            <span className="text-sky-400">더 나은 발표자</span>로.
          </h2>
          <p className="text-neutral-400 text-base leading-relaxed max-w-sm">
            AI가 시선, 자세, 발화 속도를 실시간으로 분석해 구체적인 피드백을 제공합니다.
          </p>
        </div>
        <div className="relative z-10 flex gap-10">
          {[
            { val: "55%", label: "시각 채널 비중" },
            { val: "3초", label: "캘리브레이션" },
            { val: "100점", label: "종합 발표 점수" },
          ].map(({ val, label }) => (
            <div key={label}>
              <div className="text-sky-400 text-2xl font-semibold">{val}</div>
              <div className="text-neutral-500 text-xs mt-1">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 오른쪽: 폼 패널 */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2 mb-10 justify-center">
            <span className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center"><MicIcon /></span>
            <span className="text-white text-xl tracking-tight" style={{ fontFamily: "'DM Serif Display', serif" }}>Speacher</span>
          </div>

          <div className="flex bg-neutral-900 rounded-2xl p-1 mb-8 border border-neutral-800">
            {["login", "signup"].map((m) => (
              <button
                key={m}
                onClick={() => { if (m !== mode) switchMode(); }}
                className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  mode === m ? "bg-neutral-800 text-white shadow" : "text-neutral-500 hover:text-neutral-300"
                }`}
              >
                {m === "login" ? "로그인" : "회원가입"}
              </button>
            ))}
          </div>

          <div className="mb-8">
            <h1 className="text-2xl text-white mb-1" style={{ fontFamily: "'DM Serif Display', serif" }}>
              {isLogin ? "다시 오셨군요" : "시작해봐요"}
            </h1>
            <p className="text-neutral-500 text-sm">
              {isLogin ? "계정에 로그인해 이전 분석 결과를 확인하세요." : "무료로 시작하고 발표 실력을 키워보세요."}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {!isLogin && (
              <Field label="이름" error={errors.name}>
                <input name="name" value={form.name} onChange={handleChange} placeholder="홍길동" autoComplete="name" className={INPUT_BASE} />
              </Field>
            )}
            <Field label="이메일" error={errors.email}>
              <input name="email" type="email" value={form.email} onChange={handleChange} placeholder="example@email.com" autoComplete="email" className={INPUT_BASE} />
            </Field>
            <Field label="비밀번호" error={errors.password} hint={!isLogin ? "8자 이상" : undefined}>
              <input name="password" type="password" value={form.password} onChange={handleChange} placeholder="••••••••" autoComplete={isLogin ? "current-password" : "new-password"} className={INPUT_BASE} />
            </Field>
            {!isLogin && (
              <Field label="비밀번호 확인" error={errors.confirm}>
                <input name="confirm" type="password" value={form.confirm} onChange={handleChange} placeholder="••••••••" autoComplete="new-password" className={INPUT_BASE} />
              </Field>
            )}
            {isLogin && (
              <div className="text-right">
                <button type="button" className="text-xs text-sky-500 hover:text-sky-400 transition-colors">
                  비밀번호를 잊으셨나요?
                </button>
              </div>
            )}
            <button type="submit" disabled={loading} className={BTN_PRIMARY}>
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <SpinIcon />
                  {isLogin ? "로그인 중..." : "가입 중..."}
                </span>
              ) : isLogin ? "로그인" : "회원가입"}
            </button>
          </form>

          <p className="text-center text-neutral-500 text-sm mt-6">
            {isLogin ? "계정이 없으신가요?" : "이미 계정이 있으신가요?"}{" "}
            <button onClick={switchMode} className="text-sky-500 hover:text-sky-400 font-medium transition-colors">
              {isLogin ? "회원가입" : "로그인"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

function Field({ label, error, hint, children }) {
  return (
    <div>
      <div className="flex justify-between mb-1.5">
        <label className="text-xs font-medium text-neutral-400">{label}</label>
        {hint && <span className="text-xs text-neutral-600">{hint}</span>}
      </div>
      {children}
      {error && <p className="text-xs text-red-400 mt-1.5">{error}</p>}
    </div>
  );
}

function MicIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="22" />
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
