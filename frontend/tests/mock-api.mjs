// Synthetic contract server only. Never connects to a database or external service.
import http from "node:http";
const permissions = { admin: ["report:read", "customer:read", "asset:read", "service:read", "inventory:read", "billing:read", "expense:read"], technician: ["customer:read", "asset:read", "service:read", "inventory:read"] };
http.createServer(async (req, res) => {
  res.setHeader("Content-Type", "application/json");
  if (req.url === "/health") return res.end('{"status":"ok"}');
  if (req.url === "/api/v1/auth/login") {
    let body = ""; for await (const chunk of req) body += chunk;
    const data = new URLSearchParams(body); const name = data.get("username");
    if (data.get("password") !== "synthetic-password" || !["admin@example.test", "technician@example.test"].includes(name)) { res.statusCode = 401; return res.end('{"detail":"Incorrect email or password"}'); }
    return res.end(JSON.stringify({ access_token: name.startsWith("admin") ? "synthetic-admin-token" : "synthetic-technician-token", token_type: "bearer" }));
  }
  if (req.url === "/api/v1/auth/me") {
    const role = req.headers.authorization === "Bearer synthetic-admin-token" ? "admin" : req.headers.authorization === "Bearer synthetic-technician-token" ? "technician" : null;
    if (!role) { res.statusCode = 401; return res.end('{"detail":"Invalid or expired access token"}'); }
    return res.end(JSON.stringify({ id: role === "admin" ? "11111111-1111-4111-8111-111111111111" : "22222222-2222-4222-8222-222222222222", company_id: "33333333-3333-4333-8333-333333333333", email: `${role}@example.test`, full_name: role === "admin" ? "Synthetic Admin" : "Synthetic Technician", role, is_active: true, permissions: permissions[role] }));
  }
  if (req.url === "/api/v1/customers") { res.statusCode = 403; return res.end('{"detail":"Insufficient permissions"}'); }
  res.statusCode = 404; res.end('{"detail":"Not found"}');
}).listen(8109, "127.0.0.1");
