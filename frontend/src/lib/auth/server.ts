import "server-only";
import { cookies } from "next/headers";
export const SESSION_COOKIE = "axyrel_session";
export function backendUrl(path: string): string {
  const root = new URL(process.env.AXYREL_BACKEND_URL ?? "http://127.0.0.1:8000");
  if (!["http:", "https:"].includes(root.protocol) || root.username || root.password) throw new Error("Invalid backend configuration.");
  return new URL(`/api/v1/${path}`, root).toString();
}
export async function token(): Promise<string | undefined> { return (await cookies()).get(SESSION_COOKIE)?.value; }
function publicOrigin(request: Request): string {
  const configured = process.env.AXYREL_FRONTEND_ORIGIN;
  return configured ? new URL(configured).origin : new URL(`${new URL(request.url).protocol}//${request.headers.get("host")}`).origin;
}
export function sameOrigin(request: Request): boolean {
  try { return request.headers.get("origin") === publicOrigin(request); }
  catch { return false; }
}
export function cookieOptions(request: Request) {
  return { httpOnly: true, sameSite: "strict" as const, secure: publicOrigin(request).startsWith("https:"), path: "/" };
}
