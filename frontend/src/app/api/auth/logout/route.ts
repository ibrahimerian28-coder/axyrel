import { NextResponse } from "next/server";
import { sameOrigin, cookieOptions, SESSION_COOKIE } from "@/lib/auth/server";
export async function POST(request: Request) {
  if (!sameOrigin(request)) return NextResponse.json({ detail: "Invalid request origin." }, { status: 403 });
  const response = NextResponse.json({ ok: true }, { headers: { "Cache-Control": "no-store" } });
  response.cookies.set(SESSION_COOKIE, "", { ...cookieOptions(request), maxAge: 0 });
  return response;
}
