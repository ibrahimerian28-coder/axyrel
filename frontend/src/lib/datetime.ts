// Display only: naive event timestamps retain the existing UTC interpretation.
export function displayInstant(value: string) { return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`); }
const dateFormat = new Intl.DateTimeFormat("en-GB", {timeZone:"Africa/Cairo",day:"2-digit",month:"short",year:"numeric"});
const timeFormat = new Intl.DateTimeFormat("en-US", {timeZone:"Africa/Cairo",hour:"2-digit",minute:"2-digit",hour12:true});
export function formatDate(value?: string | number | null): string {
  if (!value) return "Not recorded";
  const raw=String(value), date=/^\d{4}-\d{2}-\d{2}$/.test(raw)?new Date(`${raw}T12:00:00Z`):displayInstant(raw);
  return Number.isNaN(date.valueOf())?"Date unavailable":dateFormat.format(date);
}
export function formatDateTime(value?: string | number | null): string {
  if (!value) return "Not recorded";
  const date=displayInstant(String(value));
  return Number.isNaN(date.valueOf())?"Time unavailable":`${dateFormat.format(date)} · ${timeFormat.format(date)}`;
}
export function formatAppointment(start?: string | number | null,end?: string | number | null): string {
  if (!end) return formatDateTime(start);
  const finish=displayInstant(String(end));
  if (Number.isNaN(finish.valueOf())) return formatDateTime(start);
  return `${formatDateTime(start)} – ${formatDate(start)===formatDate(end)?timeFormat.format(finish):formatDateTime(end)}`;
}
