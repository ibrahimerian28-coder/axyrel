"use client";
import { useState } from "react";
import { api } from "@/lib/api/client";
import { label, type Row, useRecords } from "@/features/phase2/screens";
import type { User } from "@/lib/api/types";
import { errorMessage, eventInput, orderTransitions, resourceFor, singular, visitTransitions, type ServiceModule } from "./contracts";

type Data = NonNullable<ReturnType<typeof useRecords>["data"]>;
export function ServiceEditor({ module, row, seed, data, user, close, saved }: { module: ServiceModule; row?: Row; seed?: string; data: Data; user: User; close: () => void; saved: (id: string) => Promise<void> }) {
  const request = module === "Work Orders" ? data["service-requests"].find(r => r.id === seed) : undefined;
  const schedule = module === "Service Visits" && seed?.startsWith("schedule:") ? data.schedules.find(r => r.id === seed.slice(9)) : undefined;
  const seedOrder = module === "Schedule" ? seed : schedule?.work_order_id || (seed?.startsWith("order:") ? seed.slice(6) : undefined);
  const [orderId, setOrderId] = useState(String(row?.work_order_id || seedOrder || ""));
  const order = data["work-orders"].find(o => o.id === orderId);
  const [customerId, setCustomerId] = useState(String(row?.customer_id || request?.customer_id || order?.customer_id || ""));
  const [assetId, setAssetId] = useState(String(row?.asset_id || request?.asset_id || order?.asset_id || ""));
  const [requestId, setRequestId] = useState(String(row?.service_request_id || request?.id || ""));
  const [scheduleId, setScheduleId] = useState(String(row?.schedule_id || schedule?.id || ""));
  const [technicianId, setTechnicianId] = useState(String(row?.assigned_technician_id || row?.technician_id || order?.assigned_technician_id || ""));
  const [error, setError] = useState(""); const [pending, setPending] = useState(false);
  const defaultStatus = module === "Requests" || module === "Work Orders" ? "Open" : module === "Schedule" ? "Scheduled" : "Planned";
  const status = String(row?.status || defaultStatus);
  const statuses = module === "Work Orders" ? orderTransitions[status] || [status] : module === "Service Visits" ? visitTransitions[status] || [status] : undefined;
  const candidates = data.assets.filter(a => a.customer_id === customerId);
  function selectCustomer(id: string) { setCustomerId(id); setAssetId(""); setRequestId(""); }
  function selectOrder(id: string) { const selected = data["work-orders"].find(o => o.id === id); setOrderId(id); setCustomerId(String(selected?.customer_id || "")); setAssetId(String(selected?.asset_id || "")); setScheduleId(""); setTechnicianId(String(selected?.assigned_technician_id || "")); }
  function reference(name: string, text: string, value: string, rows: Row[], onChange: (id: string) => void, required = false, formatter: (row: Row) => string = label) {
    return <label>{text}<select aria-label={text} name={name} value={value} required={required} onChange={e => onChange(e.target.value)}><option value="">{required ? "Select a record" : "None"}</option>{value && !rows.some(r => r.id === value) && <option value={value}>Unavailable existing reference</option>}{rows.map(r => <option key={r.id} value={r.id}>{formatter(r)}</option>)}</select></label>;
  }
  function time(field: string, name: string, required = false) { const initial = eventInput(row?.[field]); return <div className="event-input"><label>{name} (Cairo)<input name={field} type="datetime-local" defaultValue={initial.local} required={required} /></label><label>{name} UTC offset (optional)<input name={`${field}_offset`} defaultValue={initial.offset} placeholder="+03:00 or Z" pattern="Z|[+-](0[0-9]|1[0-4]):[0-5][0-9]" /></label></div>; }
  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPending(true); setError("");
    const form = new FormData(event.currentTarget); const payload: Record<string, string | null> = {};
    for (const [key, value] of form.entries()) { if (key.endsWith("_offset")) continue; payload[key] = String(value).trim() || null; }
    if (module === "Schedule" || module === "Service Visits") {
      for (const field of module === "Schedule" ? ["start_at", "end_at"] : ["actual_start_at", "actual_end_at"]) {
        const offset = String(form.get(`${field}_offset`) || "").trim();
        if (payload[field] && offset) payload[field] += offset;
        // Untouched timestamp inputs preserve the exact API value on PATCH.
        const initial = eventInput(row?.[field]);
        if (row && String(form.get(field) || "") === initial.local && offset === initial.offset) delete payload[field];
      }
    }
    if (row) for (const key of Object.keys(payload)) if (payload[key] === (row[key] ?? null)) delete payload[key];
    try { const record = await api<Row>(`${resourceFor[module]}${row ? `/${row.id}` : ""}`, { method: row ? "PATCH" : "POST", body: JSON.stringify(payload) }); await saved(record.id); }
    catch (e) { setError(errorMessage(e)); } finally { setPending(false); }
  }
  return <section className="panel editor" aria-label={`${row ? "Edit" : "Create"} ${singular[module]}`}><h2>{row ? "Edit" : "Add"} {singular[module]}</h2><form onSubmit={save}><fieldset disabled={pending}><div className="form-grid">
    {(module === "Schedule" || module === "Service Visits") && reference("work_order_id", "Work Order", orderId, data["work-orders"], selectOrder, true)}
    {module !== "Schedule" && <>{reference("customer_id", "Customer", customerId, user.permissions.includes("customer:read") ? data.customers : [], selectCustomer, true)}{reference("asset_id", "Asset (optional)", assetId, candidates, setAssetId)}</>}
    {module === "Work Orders" && reference("service_request_id", "Service Request (optional)", requestId, data["service-requests"].filter(r => r.customer_id === customerId && (!r.asset_id || r.asset_id === assetId)), id => { setRequestId(id); const selected = data["service-requests"].find(r => r.id === id); if (selected?.asset_id) setAssetId(String(selected.asset_id)); })}
    {module === "Service Visits" && reference("schedule_id", "Schedule (optional)", scheduleId, data.schedules.filter(s => s.work_order_id === orderId), id => { setScheduleId(id); const selected = data.schedules.find(s => s.id === id); if (selected?.technician_id) setTechnicianId(String(selected.technician_id)); }, false, r => `${eventInput(r.start_at).local.replace("T", " ")} · ${r.status}`)}
    {module !== "Requests" && <label>Technician (optional)<select aria-label="Technician (optional)" name={module === "Work Orders" ? "assigned_technician_id" : "technician_id"} value={technicianId} onChange={e => setTechnicianId(e.target.value)}><option value="">Unassigned</option>{technicianId && !data.technicians.some(t => t.id === technicianId) && <option value={technicianId}>Unavailable existing technician</option>}{data.technicians.map(t => <option key={t.id} value={t.id}>{t.display_name}</option>)}</select></label>}
    {(module === "Requests" || module === "Work Orders") && <><label>Title<input name="title" required maxLength={300} defaultValue={String(row?.title || request?.title || "")} /></label><label>Description<textarea name="description" defaultValue={String(row?.description || request?.description || "")} /></label><label>Priority<input name="priority" required defaultValue={String(row?.priority || request?.priority || "Normal")} list="service-priorities" /><datalist id="service-priorities">{Array.from(new Set(data[resourceFor[module]].map(r => String(r.priority || "Normal")))).map(p => <option key={p} value={p} />)}</datalist></label></>}
    <label>Status{statuses ? <select aria-label="Status" name="status" defaultValue={status}>{statuses.map(s => <option key={s}>{s}</option>)}</select> : <input name="status" defaultValue={status} required list="service-statuses" /> }<datalist id="service-statuses">{Array.from(new Set(data[resourceFor[module]].map(r => String(r.status)))).map(s => <option key={s} value={s} />)}</datalist></label>
    {module === "Requests" && <label>Source<input name="source" defaultValue={String(row?.source || "")} /></label>}
    {module === "Schedule" && <>{time("start_at", "Start", true)}{time("end_at", "End", true)}</>}
    {module === "Service Visits" && <>{time("actual_start_at", "Actual start")}{time("actual_end_at", "Actual end")}</>}
    <label>Notes<textarea name="notes" defaultValue={String(row?.notes || "")} /></label>
  </div>{(module === "Schedule" || module === "Service Visits") && <p className="scope-note">Times use Cairo. For ambiguous clock changes, enter an explicit UTC offset for each time.</p>}{(module === "Work Orders" || module === "Service Visits") && <p className="scope-note">Cancellation and deletion apply the existing visit and stock reversal rules.</p>}{error && <p role="alert">{error}</p>}<div className="actions"><button className="primary">{pending ? "Saving…" : "Save"}</button><button type="button" onClick={close}>Cancel</button></div></fieldset></form></section>;
}
