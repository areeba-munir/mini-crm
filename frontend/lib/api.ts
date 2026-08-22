const API_URL = process.env.NEXT_PUBLIC_API_URL;

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(
    message: string,
    status: number,
    details: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

type ApiRequestOptions = RequestInit & {
  token?: string;
};

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  if (!API_URL) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not configured",
    );
  }

  const { token, ...fetchOptions } = options;
  const headers = new Headers(fetchOptions.headers);

  if (
    typeof fetchOptions.body === "string" &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...fetchOptions,
      headers,
    },
  );

  if (response.status === 204) {
    return undefined as T;
  }

  const responseData: unknown = await response
    .json()
    .catch(() => null);

  if (!response.ok) {
    let message = "Request failed";

    if (
      responseData &&
      typeof responseData === "object" &&
      "detail" in responseData &&
      typeof responseData.detail === "string"
    ) {
      message = responseData.detail;
    }

    throw new ApiError(
      message,
      response.status,
      responseData,
    );
  }

  return responseData as T;
}