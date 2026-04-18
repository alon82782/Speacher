import { create } from "zustand";
import { persist } from "zustand/middleware";
import { TOKEN_KEY, REFRESH_TOKEN_KEY } from "../constants";
import { clearTokens } from "../api/axiosInstance";

/**
 * 인증 상태 전역 스토어 (Zustand + persist)
 * - user, accessToken, refreshToken은 localStorage에 자동 저장
 */
const useAuthStore = create(
  persist(
    (set, get) => ({
      // ── State ──────────────────────────────────────────────────────────────
      user: null,                 // { id, email, name, created_at }
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      // ── Actions ────────────────────────────────────────────────────────────

      /** 로그인 성공 후 호출 */
      setAuth: ({ user, access_token, refresh_token }) => {
        localStorage.setItem(TOKEN_KEY, access_token);
        localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
        set({
          user,
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
        });
      },

      /** 내 정보 업데이트 (이름 변경 등) */
      updateUser: (userData) =>
        set((state) => ({ user: { ...state.user, ...userData } })),

      /** 로그아웃 */
      clearAuth: () => {
        clearTokens();
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      /** 토큰 갱신 */
      setAccessToken: (token) => {
        localStorage.setItem(TOKEN_KEY, token);
        set({ accessToken: token });
      },
    }),
    {
      name: "speacher-auth",
      // user와 토큰만 persist (민감 정보는 localStorage 별도 관리)
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useAuthStore;
