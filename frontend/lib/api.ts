/**
 * Configuración y cliente HTTP para comunicarse con el backend Django
 */

import { ErrorResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean>;
}

type TokenPair = { access: string; refresh: string };

const ACCESS_KEY = "docsmind_access";
const REFRESH_KEY = "docsmind_refresh";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_KEY);
}

export function setTokens(tokens: TokenPair) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_KEY, tokens.access);
  window.localStorage.setItem(REFRESH_KEY, tokens.refresh);
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}

interface ApiErrorDetail {
  status: number;
  message: string;
  data?: ErrorResponse;
}

export class ApiError extends Error implements ApiErrorDetail {
  status: number;
  data?: ErrorResponse;

  constructor(status: number, message: string, data?: ErrorResponse) {
    super(message);
    this.status = status;
    this.data = data;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  const response = await fetch(`${API_URL}/api/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) return null;
  const data = (await response.json()) as { access: string; refresh?: string };

  const next: TokenPair = {
    access: data.access,
    refresh: data.refresh ?? refresh,
  };
  setTokens(next);
  return next.access;
}

/**
 * Realiza una solicitud HTTP al backend con manejo de errores y CORS
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
  ,
  _retried = false
): Promise<T> {
  const { params, ...fetchOptions } = options;

  // Construir URL con parámetros
  let url = `${API_URL}${endpoint}`;
  if (params) {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      queryParams.append(key, String(value));
    });
    url += `?${queryParams.toString()}`;
  }

  // Configurar headers por defecto
  const headers: HeadersInit = {
    // Solo poner Content-Type JSON si no es FormData
    ...(!(fetchOptions.body instanceof FormData) && {
      "Content-Type": "application/json",
    }),
    ...fetchOptions.headers,
  };

  const access = getAccessToken();
  if (access) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${access}`;
  }

  const config: RequestInit = {
    ...fetchOptions,
    headers,
  };

  try {
    const response = await fetch(url, config);

    // Si expiró el access token, intentamos refresh 1 vez y reintentamos
    if (response.status === 401 && !_retried) {
      const newAccess = await refreshAccessToken();
      if (newAccess) {
        const nextHeaders: HeadersInit = {
          ...headers,
          Authorization: `Bearer ${newAccess}`,
        };
        return apiRequest<T>(
          endpoint,
          { ...options, headers: nextHeaders },
          true
        );
      }
    }

    // Intentar parsear la respuesta
    let data: T | ErrorResponse;
    const contentType = response.headers.get("content-type");
    
    if (contentType?.includes("application/json")) {
      data = await response.json();
    } else {
      data = (await response.text()) as T;
    }

    // Manejo de errores
    if (!response.ok) {
      throw new ApiError(
        response.status,
        `${response.status} ${response.statusText}`,
        data as ErrorResponse
      );
    }

    return data as T;
  } catch (error) {
    // Re-lanzar ApiError
    if (error instanceof ApiError) {
      throw error;
    }

    // Convertir otros errores
    if (error instanceof TypeError) {
      throw new ApiError(0, `Network error: ${error.message}`);
    }

    throw error;
  }
}

/**
 * GET request
 */
export const apiGet = <T>(endpoint: string, options?: RequestOptions) =>
  apiRequest<T>(endpoint, { ...options, method: "GET" });

/**
 * POST request
 */
export const apiPost = <T>(
  endpoint: string,
  body?: unknown,
  options?: RequestOptions
) =>
  apiRequest<T>(endpoint, {
    ...options,
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });

/**
 * PUT request
 */
export const apiPut = <T>(
  endpoint: string,
  body?: unknown,
  options?: RequestOptions
) =>
  apiRequest<T>(endpoint, {
    ...options,
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });

/**
 * DELETE request
 */
export const apiDelete = <T>(endpoint: string, options?: RequestOptions) =>
  apiRequest<T>(endpoint, { ...options, method: "DELETE" });

/**
 * FormData POST (para subidas de archivos)
 */
export const apiPostFormData = <T>(
  endpoint: string,
  formData: FormData,
  options?: RequestOptions
) => {
  const headers: Record<string, string> = {
    ...(options?.headers as Record<string, string> | undefined),
  };
  // No establecer Content-Type para FormData (el navegador lo hace automáticamente)
  delete headers["Content-Type"];

  return apiRequest<T>(endpoint, {
    ...options,
    method: "POST",
    body: formData,
    headers,
  });
};

export default apiRequest;
