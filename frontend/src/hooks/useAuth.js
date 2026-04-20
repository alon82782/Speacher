import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import * as authApi from "../api/authApi";
import useAuthStore from "../stores/authStore";

export const AUTH_KEYS = {
  me: ["auth", "me"],
};

export const useGetMe = () => {
  const { isAuthenticated } = useAuthStore();
  return useQuery({
    queryKey: AUTH_KEYS.me,
    queryFn: authApi.getMe,
    enabled: isAuthenticated,
    select: (res) => res,
    staleTime: 1000 * 60 * 5,
  });
};

export const useRegister = () => {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: authApi.register,
    onSuccess: (res) => {
      setAuth({
        user: { id: res.user_id },
        access_token: res.tokens.access_token,
        refresh_token: res.tokens.refresh_token,
      });
      navigate("/dashboard");
    },
  });
};

export const useLogin = () => {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (res) => {
      setAuth({
        user: res.user,
        access_token: res.tokens.access_token,
        refresh_token: res.tokens.refresh_token,
      });
      queryClient.invalidateQueries({ queryKey: AUTH_KEYS.me });
      navigate("/dashboard");
    },
  });
};

export const useLogout = () => {
  const { clearAuth } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      clearAuth();
      queryClient.clear();
      navigate("/");
    },
  });
};

export const useUpdateMe = () => {
  const { updateUser } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.updateMe,
    onSuccess: (res) => {
      updateUser(res);
      queryClient.invalidateQueries({ queryKey: AUTH_KEYS.me });
    },
  });
};

export const useUpdatePassword = () =>
  useMutation({ mutationFn: authApi.updatePassword });

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
