const API_BASE = "/api";

interface RequestConfig extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public errors?: unknown[]
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  config: RequestConfig = {}
): Promise<T> {
  const { params, ...fetchConfig } = config;

  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.set(key, String(value));
      }
    });
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  const headers: Record<string, string> = {
    ...(fetchConfig.headers as Record<string, string>),
  };

  if (!(fetchConfig.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...fetchConfig,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    let errorData: { code?: string; detail?: string; errors?: unknown[] } = {};
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    throw new ApiError(
      response.status,
      errorData.code || "UNKNOWN_ERROR",
      errorData.detail || "An error occurred",
      errorData.errors
    );
  }

  if (response.status === 204) return undefined as T;

  const contentType = response.headers.get("content-type");
  if (contentType?.includes("text/event-stream")) {
    return response as unknown as T;
  }

  return response.json();
}

export const api = {
  get: <T>(endpoint: string, config?: RequestConfig) =>
    request<T>(endpoint, { ...config, method: "GET" }),

  post: <T>(endpoint: string, body?: unknown, config?: RequestConfig) =>
    request<T>(endpoint, {
      ...config,
      method: "POST",
      body: JSON.stringify(body ?? {}),
    }),

  patch: <T>(endpoint: string, body?: unknown, config?: RequestConfig) =>
    request<T>(endpoint, {
      ...config,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(endpoint: string, config?: RequestConfig) =>
    request<T>(endpoint, { ...config, method: "DELETE" }),

  upload: <T>(endpoint: string, formData: FormData, config?: RequestConfig) =>
    request<T>(endpoint, {
      ...config,
      method: "POST",
      body: formData,
    }),
};

export { ApiError };
