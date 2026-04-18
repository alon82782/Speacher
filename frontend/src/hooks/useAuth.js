import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import * as authApi from "../api/authApi";
import useAuthStore from "../stores/authStore";

// ── Query Keys ────────────────────────────────────────────────────────────────
export const AUTH_KEYS = {
  me: ["auth", "me"],
};

// ── 내 정보 조회 ──────────────────────────────────────────────────────────────
export const useGetMe = () => {
  const { isAuthenticated } = useAuthStore();
  return useQuery({
    queryKey: AUTH_KEYS.me,
    queryFn: authApi.getMe,
    enabled: isAuthenticated,
    select: (res) => res.data,
    staleTime: 1000 * 60 * 5, // 5분
  });
};

// ── 회원가입 ──────────────────────────────────────────────────────────────────
export const useRegister = () => {
  const navigate = useNavigate();
  return useMutation({
    mutationFn: authApi.register,
    onSuccess: () => {
      navigate("/", { state: { message: "회원가입이 완료됐습니다. 로그인해주세요." } });
    },
  });
};

// ── 로그인 ────────────────────────────────────────────────────────────────────
export const useLogin = () => {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (res) => {
      setAuth(res.data);
      queryClient.invalidateQueries({ queryKey: AUTH_KEYS.me });
      navigate("/dashboard");
    },
  });
};

// ── 로그아웃 ──────────────────────────────────────────────────────────────────
export const useLogout = () => {
  const { clearAuth } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      // API 실패해도 반드시 로컬 상태 초기화
      clearAuth();
      queryClient.clear();
      navigate("/");
    },
  });
};

// ── 내 정보 수정 ──────────────────────────────────────────────────────────────
export const useUpdateMe = () => {
  const { updateUser } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.updateMe,
    onSuccess: (res) => {
      updateUser(res.data);
      queryClient.invalidateQueries({ queryKey: AUTH_KEYS.me });
    },
  });
};

// ── 비밀번호 변경 ─────────────────────────────────────────────────────────────
export const useUpdatePassword = () =>
  useMutation({ mutationFn: authApi.updatePassword });

// ── 회원 탈퇴 ─────────────────────────────────────────────────────────────────
export const useDeleteAccount = () => {
  const { clearAuth } = useAuthStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: authApi.deleteAccount,
    onSuccess: () => {
      clearAuth();
      navigate("/");
    },
  });
};
