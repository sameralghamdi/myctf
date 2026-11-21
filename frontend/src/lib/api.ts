/**
 * Thin fetch wrapper. All calls are same-origin: in dev Vite proxies to Flask, in
 * production the Cloudflare Pages Function proxies to the API server. The session
 * lives in an HttpOnly cookie, so no token ever touches JavaScript.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly data: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
}

let onUnauthorized: (() => void) | null = null;

/** Registered by AuthProvider: called when a non-auth endpoint answers 401. */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function errorMessage(data: unknown, status: number): string {
  if (isRecord(data)) {
    if (typeof data.error === "string" && data.error) return data.error;
    if (typeof data.message === "string" && data.message) return data.message;
  }
  return `Request failed (${status})`;
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, signal } = options;
  const response = await fetch(path, {
    method,
    signal,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    // Empty or non-JSON body.
  }

  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/api/auth/")) onUnauthorized?.();
    throw new ApiError(errorMessage(data, response.status), response.status, data);
  }
  return data as T;
}

/** POST a single file as multipart/form-data under `field`. */
export async function uploadFile<T>(path: string, field: string, file: Blob, filename: string): Promise<T> {
  const form = new FormData();
  form.append(field, file, filename);
  const response = await fetch(path, {
    method: "POST",
    credentials: "same-origin",
    headers: { Accept: "application/json" },
    body: form,
  });
  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    // Empty or non-JSON body.
  }
  if (!response.ok) throw new ApiError(errorMessage(data, response.status), response.status, data);
  return data as T;
}

/** Message suitable for showing to the user. */
export function toMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong.";
}
