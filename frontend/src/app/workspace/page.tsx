"use client";
import { Suspense, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Dashboard, RecordsScreen } from "@/features/phase2/screens";
import { api, ApiError } from "@/lib/api/client";
import type { User } from "@/lib/api/types";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "@/components/ui/states";
import { text } from "@/locales/en/common";
const modules = [["Dashboard", "report:read"], ["Customers", "customer:read"], ["Assets", "asset:read"], ["Requests", "service:read"], ["Work Orders", "service:read"], ["Schedule", "service:read"], ["Service Visits", "service:read"], ["Inventory", "inventory:read"], ["Invoices", "billing:read"], ["Expenses", "expense:read"], ["Reports", "report:read"]];
export default function Workspace() { return <Suspense fallback={<LoadingState />}><WorkspaceContent /></Suspense>; }
function WorkspaceContent() {
  const router = useRouter(); const params = useSearchParams(); const area = params.get("module") || "Workspace"; const record = params.get("record") || undefined; const cache = useQueryClient(); const [open, setOpen] = useState(false); const [logoutError, setLogoutError] = useState("");
  function navigate(module: string, id?: string) { router.push(`/workspace?module=${encodeURIComponent(module)}${id ? `&record=${encodeURIComponent(id)}` : ""}`); setOpen(false); }
  const user = useQuery({ queryKey: ["session", "me"], queryFn: () => api<User>("auth/me") });
  if (user.isPending) return <LoadingState />;
  if (user.error) return user.error instanceof ApiError && user.error.status === 401 ? <main className="state"><h1>Sign in to continue</h1><a href="/login">Sign in</a></main> : user.error instanceof ApiError && user.error.status === 403 ? <PermissionState /> : <ErrorState message={user.error.message} retry={() => { void user.refetch(); }} />;
  const me = user.data; const available = modules.filter(([, permission]) => me.permissions.includes(permission));
  async function logout() {
    try { const response = await fetch("/api/auth/logout", { method: "POST" }); if (!response.ok) throw new Error(); cache.clear(); router.replace("/login"); }
    catch { setLogoutError("Sign out could not be completed. Please try again."); }
  }
  return <div className="app-shell"><a className="skip-link" href="#workspace">Skip to workspace</a><aside className={`sidebar ${open ? "is-open" : ""}`} aria-label="Main navigation"><img className="brand-image" src="/brand/axyrel-logo.png" alt="Axyrel — Work Smarter. Serve Better." /><nav><button className={area === "Workspace" ? "nav-item active" : "nav-item"} onClick={() => { navigate("Workspace"); }}>Workspace</button>{available.map(([name]) => <button className={area === name ? "nav-item active" : "nav-item"} key={name} aria-current={area === name ? "page" : undefined} onClick={() => { navigate(name); }}><span className="nav-mark" aria-hidden="true">◇</span>{name}</button>)}</nav><footer>© 2026 Axyrel</footer></aside><div className="workspace"><header className="topbar"><button aria-label="Toggle navigation" aria-expanded={open} onClick={() => setOpen(!open)}>☰</button><span className="workspace-caption">Team workspace</span><div className="identity"><strong>{me.full_name}</strong><small>{me.role}</small></div><button onClick={logout}>{text.signOut}</button></header><main id="workspace" className="content">{!["Dashboard", "Customers", "Assets"].includes(area) && <h1>{area}</h1>}{logoutError && <p role="alert">{logoutError}</p>}{!available.length || (area !== "Workspace" && !available.some(([name]) => name === area)) ? <PermissionState /> : area === "Dashboard" ? <Dashboard user={me} go={navigate} /> : area === "Customers" || area === "Assets" ? <RecordsScreen key={`${area}-${record || ""}`} kind={area} user={me} selectedId={record} go={navigate} /> : <EmptyState title={area === "Workspace" ? "Your workspace is ready" : `${area} is planned for a later phase`} description="Dashboard, Customers and Assets are available. Other domains remain for later approved phases." />}</main></div></div>;
}
