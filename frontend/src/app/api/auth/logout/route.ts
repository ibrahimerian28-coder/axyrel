import { NextResponse } from "next/server";
import { backendUrl, token, sameOrigin, cookieOptions, SESSION_COOKIE } from "@/lib/auth/server";
export async function POST(request: Request) {
  if (!sameOrigin(request)) return NextResponse.json({ detail: "Invalid request origin." }, { status: 403 });
  const session = await token();
  if (session) {
    try {
      const upstream = await fetch(backendUrl("auth/sessions/logout"), { method: "POST", headers: { Authorization: `Bearer ${session}` }, cache: "no-store", redirect: "error", signal: AbortSignal.timeout(20000) });
      if (!upstream.ok) return NextResponse.json({ detail: "Sign-out could not be completed. Please retry." }, { status: upstream.status });
    } catch { return NextResponse.json({ detail: "Sign-out service is unavailable. Please retry." }, { status: 502 }); }
  }
  const response = NextResponse.json({ ok: true }, { headers: { "Cache-Control": "no-store" } });
  response.cookies.set(SESSION_COOKIE, "", { ...cookieOptions(request), maxAge: 0 });
  return response;
}
