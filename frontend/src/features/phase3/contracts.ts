import { formatDateTime, formatDate } from "@/lib/datetime";
import type { Row } from "@/features/phase2/screens";
import { label } from "@/features/phase2/screens";
import { ApiError } from "@/lib/api/client";

export const serviceModules = ["Requests", "Work Orders", "Schedule", "Service Visits", "Service History"] as const;
export type ServiceModule = typeof serviceModules[number];
export const resourceFor = { Requests: "service-requests", "Work Orders": "work-orders", Schedule: "schedules", "Service Visits": "service-visits", "Service History": "service-history" } as const;
export const singular = { Requests: "Request", "Work Orders": "Work Order", Schedule: "Schedule", "Service Visits": "Service Visit", "Service History": "Service History" };
export const orderTransitions: Record<string, string[]> = { Open: ["Open", "In Progress", "Completed", "Cancelled"], "In Progress": ["Open", "In Progress", "Completed", "Cancelled"], Completed: ["Completed", "Cancelled"], Cancelled: ["Cancelled"] };
export const visitTransitions: Record<string, string[]> = { Planned: ["Planned", "In Progress", "Completed", "Cancelled"], "In Progress": ["In Progress", "Completed", "Cancelled"], Completed: ["Completed", "Cancelled"], Cancelled: ["Cancelled"] };
const cairo = new Intl.DateTimeFormat("en-GB", { timeZone: "Africa/Cairo", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23", timeZoneName: "longOffset" });
function instant(value: string) { return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`); }
export function eventInput(value?: string | number | null) {
  if (!value) return { local: "", offset: "" };
  const date = instant(String(value)); if (Number.isNaN(date.valueOf())) return { local: "", offset: "" };
  const parts = Object.fromEntries(cairo.formatToParts(date).map(p => [p.type, p.value]));
  return { local: `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`, offset: parts.timeZoneName.replace("GMT", "") || "Z" };
}
export const eventLabel = formatDateTime;
export const scheduleEventLabel = formatDateTime;
export const calendarDateLabel = formatDate;
export function dayKey(value: string) { return eventInput(value).local.slice(0, 10); }
export function addDays(day: string, amount: number) { const date = new Date(`${day}T12:00:00Z`); date.setUTCDate(date.getUTCDate() + amount); return date.toISOString().slice(0, 10); }
export function currentWeek() { const today = dayKey(new Date().toISOString()); const weekday = new Date(`${today}T12:00:00Z`).getUTCDay(); return addDays(today, -((weekday + 6) % 7)); }
export function serviceLabel(module: ServiceModule, row: Row, orders: Row[]) {
  if (module === "Requests" || module === "Work Orders") return label(row);
  if (module === "Service History") return String(row.summary || row.service_type || "Service history");
  const order = orders.find(o => o.id === row.work_order_id);
  return `${module === "Schedule" ? "Schedule" : "Visit"} · ${label(order)} · ${(module === "Schedule" ? scheduleEventLabel : eventLabel)(row.start_at || row.actual_start_at || row.created_at)}`;
}
export function errorMessage(error: unknown) {
  if (!(error instanceof ApiError)) return "The action could not be completed. Please try again.";
  if (error.status === 403 || error.status === 401) return error.message;
  const detail = typeof error.detail === "string" ? error.detail : error.status === 422 ? "Please check required fields, quantities and time ranges." : error.message;
  return detail.replace(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, "related record");
}
