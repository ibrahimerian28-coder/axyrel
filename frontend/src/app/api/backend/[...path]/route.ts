import { NextResponse } from "next/server";
import { backendUrl, token, sameOrigin, cookieOptions, SESSION_COOKIE } from "@/lib/auth/server";
const resources = new Set(["customers", "assets", "service-requests", "work-orders", "schedules", "service-visits", "service-history", "inventory", "technician-stock", "inventory-transactions", "invoices", "service-contracts", "expenses", "profitability", "notifications", "audit-logs", "technician-directory"]);
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function allowed(parts: string[], method: string) {
  if (parts.join("/") === "auth/me") return method === "GET";
  if (parts[0] === "imports") return parts.length === 2 && ((parts[1] === "template" && method === "GET") || (["upload", "preview", "commit"].includes(parts[1]) && method === "POST"));
  const [resource, id, action] = parts;
  if (!resources.has(resource) || parts.length > 3) return false;
  if (resource === "assets" && id === "import") return parts.length === 3 && ((action === "template" && method === "GET") || (["validate", "commit"].includes(action) && method === "POST"));
  if (resource === "technician-directory") return parts.length === 1 && method === "GET";
  if (resource === "profitability") return parts.length === 2 && ["summary", "expenses"].includes(id) && method === "GET";
  if (!id) return ["GET", "POST"].includes(method) && !(resource === "technician-directory" && method !== "GET");
  if (parts.length === 2 && id === "summary") return method === "GET" && ["inventory", "work-orders", "expenses", "profitability"].includes(resource);
  if (parts.length === 2 && resource === "profitability" && id === "expenses") return method === "GET";
  if (!uuid.test(id)) return false;
  if (action === "image" && ["customers", "assets"].includes(resource)) return ["GET", "PUT", "DELETE"].includes(method);
  if (!action) return ["audit-logs", "inventory-transactions"].includes(resource) ? method === "GET" : resource === "technician-stock" || resource === "notifications" ? ["GET", "PATCH"].includes(method) : ["GET", "PATCH", "DELETE"].includes(method);
  return method === "POST" && ((resource === "service-visits" && action === "parts") || (resource === "notifications" && action === "read"));
}
async function forward(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!allowed(path, request.method)) return NextResponse.json({ detail: "Unavailable API route." }, { status: 404 });
  if (request.method !== "GET" && !sameOrigin(request)) return NextResponse.json({ detail: "Invalid request origin." }, { status: 403 });
  const session = await token();
  if (!session) return NextResponse.json({ detail: "Authentication required." }, { status: 401 });
  try {
    const url = backendUrl(path.join("/")) + new URL(request.url).search;
    const image = path[2] === "image";
    if (image) {
      let upload: Uint8Array | undefined;
      if (request.method === "PUT") {
        const limit = 5 * 1024 * 1024;
        const reader = request.body?.getReader();
        const chunks: Uint8Array[] = []; let length = 0;
        if (reader) {
          try {
            while (true) {
              const { done, value } = await reader.read(); if (done) break;
              length += value.byteLength;
              if (length > limit) { await reader.cancel(); return NextResponse.json({ detail: "Image must be 5 MB or smaller." }, { status: 413 }); }
              chunks.push(value);
            }
          } finally { reader.releaseLock(); }
        }
        upload = new Uint8Array(length); let offset = 0;
        for (const chunk of chunks) { upload.set(chunk, offset); offset += chunk.length; }
      }
      const upstream = await fetch(url, { method: request.method, headers: { Authorization: `Bearer ${session}`, "Content-Type": request.headers.get("content-type") || "application/octet-stream" }, body: upload as BodyInit | undefined, cache: "no-store", redirect: "error", signal: AbortSignal.timeout(20000) });
      const body = upstream.status >= 500 ? JSON.stringify({ detail: "The service could not complete the request." }) : await upstream.arrayBuffer();
      const response = new NextResponse(upstream.status === 204 ? null : body, { status: upstream.status, headers: { "Content-Type": upstream.ok && request.method === "GET" ? "image/webp" : "application/json", "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff" } });
      if (upstream.status === 401) response.cookies.set(SESSION_COOKIE, "", { ...cookieOptions(request), maxAge: 0 });
      return response;
    }
    let requestBody: string | undefined;
    if (request.method !== "GET") {
      if (path[1] === "import" || path[0] === "imports") {
        const reader = request.body?.getReader(); const chunks: Uint8Array[] = []; let size = 0;
        if (reader) try { while (true) { const { done, value } = await reader.read(); if (done) break; size += value.byteLength; if (size > 7 * 1024 * 1024) { await reader.cancel(); return NextResponse.json({ detail: "Import request is too large." }, { status: 413 }); } chunks.push(value); } } finally { reader.releaseLock(); }
        const bytes = new Uint8Array(size); let offset = 0; for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; } requestBody = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
      } else requestBody = await request.text();
    }
    const upstream = await fetch(url, { method: request.method, headers: { Authorization: `Bearer ${session}`, "Content-Type": "application/json" }, body: requestBody, cache: "no-store", redirect: "error", signal: AbortSignal.timeout(20000) });
    const body = upstream.status >= 500 ? JSON.stringify({ detail: "The service could not complete the request." }) : await upstream.text();
    const response = new NextResponse(upstream.status === 204 ? null : body, { status: upstream.status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
    if (upstream.status === 401) response.cookies.set(SESSION_COOKIE, "", { ...cookieOptions(request), maxAge: 0 });
    return response;
  } catch { return NextResponse.json({ detail: "The service is unavailable." }, { status: 502 }); }
}
export { forward as GET, forward as POST, forward as PATCH, forward as DELETE, forward as PUT };
