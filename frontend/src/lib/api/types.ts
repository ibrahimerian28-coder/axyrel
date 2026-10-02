export type User = { id: string; company_id: string; email: string; full_name: string; role: string; is_active: boolean; permissions: string[] };
export type Technician = { id: string; display_name: string };
export type RecordRef = { id: string; display_id?: number | null; name?: string; title?: string; invoice_number?: string; serial_number?: string | null };
