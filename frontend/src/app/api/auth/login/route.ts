import { NextResponse } from "next/server";
import { backendUrl, cookieOptions, sameOrigin, SESSION_COOKIE } from "@/lib/auth/server";
export async function POST(request: Request) {
  if (!sameOrigin(request)) return NextResponse.json({ detail: "Invalid request origin." }, { status: 403 });
  try {
    const body = await request.json();
    if (typeof body.email !== "string" || typeof body.password !== "string") return NextResponse.json({ detail: "Email and password required." }, { status: 422 });
    const upstream = await fetch(backendUrl("auth/sessions"), { method: "POST", body: new URLSearchParams({ username: body.email.trim(), password: body.password }), cache: "no-store", redirect: "error", signal: AbortSignal.timeout(20000) });
    if (!upstream.ok) return NextResponse.json({ detail: upstream.status === 401 ? "Incorrect email or password." : "Sign-in could not be completed." }, { status: upstream.status });
    const data = await upstream.json();
    if (typeof data.access_token !== "string" || !/^axs_[A-Za-z0-9_-]{43}$/.test(data.access_token)) return NextResponse.json({ detail: "Invalid authentication response." }, { status: 502 });
    const response = NextResponse.json({ ok: true }, { headers: { "Cache-Control": "no-store" } });
    response.cookies.set(SESSION_COOKIE, data.access_token, cookieOptions(request));
    return response;
  } catch { return NextResponse.json({ detail: "Sign-in service is unavailable." }, { status: 502 }); }
}
