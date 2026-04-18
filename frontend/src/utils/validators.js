import { ALLOWED_VIDEO_TYPES, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from "../constants";

/**
 * 업로드 파일 유효성 검사
 * @returns { valid: boolean, error: string|null }
 */
export const validateVideoFile = (file) => {
  if (!file) return { valid: false, error: "파일을 선택해주세요." };

  if (!ALLOWED_VIDEO_TYPES.includes(file.type)) {
    return { valid: false, error: "MP4, MOV, AVI, WEBM 형식만 업로드 가능합니다." };
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return { valid: false, error: `파일 크기는 ${MAX_FILE_SIZE_MB}MB 이하여야 합니다.` };
  }

  return { valid: true, error: null };
};

/** 이메일 형식 검사 */
export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

/** 비밀번호 강도 검사 (8자 이상, 영문+숫자 포함) */
export const validatePassword = (password) => {
  if (password.length < 8) return { valid: false, error: "비밀번호는 8자 이상이어야 합니다." };
  if (!/[a-zA-Z]/.test(password)) return { valid: false, error: "영문자를 포함해야 합니다." };
  if (!/[0-9]/.test(password)) return { valid: false, error: "숫자를 포함해야 합니다." };
  return { valid: true, error: null };
};
