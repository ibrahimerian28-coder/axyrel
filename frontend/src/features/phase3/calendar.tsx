"use client";
import { useState } from "react";
import type { Row } from "@/features/phase2/screens";
import { EmptyState } from "@/components/ui/states";
import { addDays, dayKey, scheduleEventLabel, calendarDateLabel, serviceLabel } from "./contracts";

export function WeekSchedule({ rows, orders, week, setWeek, select }: { rows: Row[]; orders: Row[]; week: string; setWeek: (week: string) => void; select: (row: Row) => void }) {
  const [view, setView] = useState("week");
  const days = Array.from({ length: 7 }, (_, i) => addDays(week, i));
  const overlapping = (row: Row, day: string) => dayKey(String(row.start_at)) <= day && dayKey(String(row.end_at)) >= day;
  const visible = rows.filter(r => days.some(day => overlapping(r, day))).sort((a, b) => String(a.start_at).localeCompare(String(b.start_at)));
  function entry(row: Row) { return <button className="schedule-card" key={row.id} onClick={() => select(row)}><strong>{serviceLabel("Schedule", row, orders)}</strong><span>{scheduleEventLabel(row.start_at)} — {scheduleEventLabel(row.end_at)}</span><span className="badge">{row.status}</span></button>; }
  return <section className="panel calendar-panel" aria-label="Seven-day schedule" data-view={view}><div className="calendar-toolbar"><h2>Seven-day schedule</h2><div className="actions"><button aria-label="Previous seven days" onClick={() => setWeek(addDays(week, -7))}>Previous</button><label>Week starting<input type="date" value={week} onChange={e => { if (e.target.value) setWeek(e.target.value); }} /></label><button aria-label="Next seven days" onClick={() => setWeek(addDays(week, 7))}>Next</button></div><div className="calendar-view-controls"><button aria-pressed={view === "week"} onClick={() => setView("week")}>Week view</button><button aria-pressed={view === "agenda"} onClick={() => setView("agenda")}>Agenda view</button></div></div><p>All times shown in Cairo. {visible.length} schedule records in this window.</p><div className="week-view">{days.map(day => <section className="calendar-day" key={day} aria-label={`Schedule for ${day}`}><h3>{calendarDateLabel(day)}</h3>{rows.filter(r => overlapping(r, day)).sort((a, b) => String(a.start_at).localeCompare(String(b.start_at))).map(entry)}{!rows.some(r => overlapping(r, day)) && <p>No schedules</p>}</section>)}</div><div className="agenda-view">{visible.length ? visible.map(entry) : <EmptyState title="No schedules in these seven days" description="Choose another week or add a schedule." />}</div></section>;
}
