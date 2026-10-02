export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) {
    super(status === 401 ? "Your session has expired. Please sign in." : status === 403 ? "You do not have permission for this action." : "The request could not be completed.");
  }
}
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/backend/${path}`, { ...init, credentials: "same-origin", cache: "no-store", headers: { "Content-Type": "application/json", ...init.headers } });
  if (!response.ok) {
    let detail: unknown;
    try { detail = (await response.json()).detail; } catch { detail = undefined; }
    throw new ApiError(response.status, detail);
  }
  return response.status === 204 ? undefined as T : response.json();
}
