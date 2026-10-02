import type { RecordRef } from "@/lib/api/types";
export function recordLabel(record?: RecordRef): string {
  if (!record) return "Related record unavailable";
  const label = record.name || record.title || record.invoice_number || record.serial_number;
  return label ? `${record.display_id ? `#${record.display_id} · ` : ""}${label}` : record.display_id ? `#${record.display_id}` : "Related record unavailable";
}
