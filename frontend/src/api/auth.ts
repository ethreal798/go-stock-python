import request from "./index";

/**
 * 登录 (Form Data)
 */
export function login(data: FormData) {
  return request.post("/auth/login", data, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}

/**
 * 注册 (JSON)
 */
export function register(data: any) {
  return request.post("/auth/register", data);
}
