import axiosInstance from "./axiosInstance";

/**
 * POST /auth/register
 * @param {{ email, password, name }} data
 */
export const register = (data) =>
  axiosInstance.post("/auth/register", data).then((r) => r.data);

/**
 * POST /auth/login
 * @param {{ email, password }} data
 * @returns { access_token, refresh_token, user }
 */
export const login = (data) =>
  axiosInstance.post("/auth/login", data).then((r) => r.data);

/**
 * POST /auth/logout
 */
export const logout = () =>
  axiosInstance.post("/auth/logout").then((r) => r.data);

/**
 * POST /auth/refresh
 * @param {string} refreshToken
 */
export const refreshToken = (refreshToken) =>
  axiosInstance.post("/auth/refresh", { refresh_token: refreshToken }).then((r) => r.data);

/**
 * GET /auth/verify — 토큰 유효성 확인
 */
export const verifyToken = () =>
  axiosInstance.get("/auth/verify").then((r) => r.data);

/**
 * GET /auth/me — 내 정보 조회
 */
export const getMe = () =>
  axiosInstance.get("/auth/me").then((r) => r.data);

/**
 * PUT /auth/me — 내 정보 수정
 * @param {{ name }} data
 */
export const updateMe = (data) =>
  axiosInstance.put("/auth/me", data).then((r) => r.data);

/**
 * PUT /auth/me/password — 비밀번호 변경
 * @param {{ current_password, new_password }} data
 */
export const updatePassword = (data) =>
  axiosInstance.put("/auth/me/password", data).then((r) => r.data);

/**
 * DELETE /auth/me — 회원 탈퇴
 * @param {{ password }} data
 */
export const deleteAccount = (data) =>
  axiosInstance.delete("/auth/me", { data }).then((r) => r.data);
