const ACCESS_TOKEN_KEY = "mini_crm_access_token";

export function saveAccessToken(
  token: string,
): void {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(
    ACCESS_TOKEN_KEY,
    token,
  );
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.sessionStorage.getItem(
    ACCESS_TOKEN_KEY,
  );
}

export function removeAccessToken(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(
    ACCESS_TOKEN_KEY,
  );
}