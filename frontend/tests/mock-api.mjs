// Synthetic contract server only. Never connects to a database or external service.
import http from "node:http";
import { randomBytes } from "node:crypto";
const sessions = new Map();
let failure;
const permissions = { admin: ["report:read", "customer:read", "asset:read", "service:read", "inventory:read", "billing:read", "expense:read"], technician: ["customer:read", "asset:read", "service:read", "inventory:read"] };
http.createServer(async (req, res) => {
  res.setHeader("Content-Type", "application/json");
  if (req.url === "/health") return res.end('{"status":"ok"}');
  if (req.url === "/test/failure") {
    let body = ""; for await (const chunk of req) body += chunk;
    failure = JSON.parse(body); return res.end("{}");
  }
  if (failure?.path === req.url) {
    if (failure.status === "network") return req.socket.destroy();
    if (failure.status === "timeout") return;
    res.statusCode = failure.status; return res.end('{"detail":"Synthetic failure"}');
  }
  if (req.url === "/api/v1/auth/sessions/logout") {
    sessions.delete(req.headers.authorization?.slice(7)); res.statusCode = 204; return res.end();
  }
  if (req.url === "/api/v1/auth/sessions") {
    let body = ""; for await (const chunk of req) body += chunk;
    const data = new URLSearchParams(body); const name = data.get("username");
    if (data.get("password") !== "synthetic-password" || !["admin@example.test", "technician@example.test"].includes(name)) { res.statusCode = 401; return res.end('{"detail":"Incorrect email or password"}'); }
    const credential = "axs_" + randomBytes(32).toString("base64url");
    sessions.set(credential, name.startsWith("admin") ? "admin" : "technician");
    return res.end(JSON.stringify({ access_token: credential, token_type: "bearer" }));
  }
  if (req.url === "/api/v1/auth/me") {
    const role = sessions.get(req.headers.authorization?.slice(7));
    if (!role) { res.statusCode = 401; return res.end('{"detail":"Invalid or expired access token"}'); }
    return res.end(JSON.stringify({ id: role === "admin" ? "11111111-1111-4111-8111-111111111111" : "22222222-2222-4222-8222-222222222222", company_id: "33333333-3333-4333-8333-333333333333", email: `${role}@example.test`, full_name: role === "admin" ? "Synthetic Admin" : "Synthetic Technician", role, is_active: true, permissions: permissions[role] }));
  }
  if (req.url === "/api/v1/customers") { res.statusCode = 403; return res.end('{"detail":"Insufficient permissions"}'); }
  if (req.method === "GET" && ["assets", "work-orders", "service-requests", "service-visits", "service-history", "invoices", "schedules", "inventory", "technician-directory"].some(resource => req.url === `/api/v1/${resource}`)) return res.end("[]");
  res.statusCode = 404; res.end('{"detail":"Not found"}');
}).listen(8109, "127.0.0.1");
