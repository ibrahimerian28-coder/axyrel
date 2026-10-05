"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { text } from "@/locales/en/common";
export default function Login() {
  const router = useRouter(); const cache = useQueryClient();
  const [error, setError] = useState(""); const [pending, setPending] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPending(true); setError("");
    const data = new FormData(event.currentTarget);
    try {
      const response = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: data.get("email"), password: data.get("password") }) });
      if (!response.ok) { const body = await response.json(); setError(body.detail); return; }
      cache.clear(); router.replace("/workspace?module=Dashboard");
    } catch { setError("Sign-in service is unavailable. Please try again."); }
    finally { setPending(false); }
  }
  return <main className="login-page"><section className="login-brand"><img src="/brand/axyrel-logo.png" alt="Axyrel — Work Smarter. Serve Better." /><p>One workspace for your field service team.</p></section><section className="login-panel"><p className="eyebrow">TEAM WORKSPACE</p><h1>Welcome to Axyrel</h1><p>Sign in with your existing team account.</p><form onSubmit={submit}><label>Email<input name="email" type="email" autoComplete="username" required /></label><label>Password<input name="password" type="password" autoComplete="current-password" required /></label>{error && <p role="alert">{error}</p>}<button className="primary" disabled={pending}>{pending ? "Signing in…" : text.signIn}</button></form><small>Customer self-service is not enabled.</small></section></main>;
}
