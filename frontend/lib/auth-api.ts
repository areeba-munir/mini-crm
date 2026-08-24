import { apiRequest } from "@/lib/api";
import type {
  LoginInput,
  PasswordChangeInput,
  RegisterInput,
  TokenResponse,
  User,
  UserUpdateInput,
} from "@/types/auth";

export function registerUser(input: RegisterInput): Promise<User> {
  return apiRequest<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function loginUser(input: LoginInput): Promise<TokenResponse> {
  const formData = new URLSearchParams({
    username: input.email,
    password: input.password,
  });

  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: formData,
  });
}

export function getCurrentUser(token: string): Promise<User> {
  return apiRequest<User>("/auth/me", {
    token,
  });
}

export function updateCurrentUser(
  input: UserUpdateInput,
  token: string,
): Promise<User> {
  return apiRequest<User>("/auth/me", {
    method: "PATCH",
    body: JSON.stringify(input),
    token,
  });
}

export function changeCurrentUserPassword(
  input: PasswordChangeInput,
  token: string,
): Promise<void> {
  return apiRequest<void>("/auth/me/password", {
    method: "PATCH",
    body: JSON.stringify(input),
    token,
  });
}
