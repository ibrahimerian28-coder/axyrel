import { expect,test } from '@playwright/test';
import { calendarDateLabel,eventInput,eventLabel,scheduleEventLabel,serviceLabel } from '../../src/features/phase3/contracts';

for(const scenario of [
  {name:'Cairo summer UTC instant',value:'2026-10-06T07:00:00Z',display:'06 Oct 2026 · 10:00 AM',local:'2026-10-06T10:00',offset:'+03:00'},
  {name:'Cairo winter UTC instant',value:'2026-01-06T08:00:00Z',display:'06 Jan 2026 · 10:00 AM',local:'2026-01-06T10:00',offset:'+02:00'},
  {name:'explicit offset same instant',value:'2026-10-06T10:00:00+03:00',display:'06 Oct 2026 · 10:00 AM',local:'2026-10-06T10:00',offset:'+03:00'},
  {name:'existing naive API UTC output',value:'2026-10-06T07:00:00',display:'06 Oct 2026 · 10:00 AM',local:'2026-10-06T10:00',offset:'+03:00'},
])test(`Schedule display: ${scenario.name}`,()=>{
  expect(scheduleEventLabel(scenario.value)).toBe(scenario.display);
  expect(eventInput(scenario.value)).toEqual({local:scenario.local,offset:scenario.offset});
  expect(serviceLabel('Schedule',{id:'schedule',work_order_id:'order',start_at:scenario.value},[{id:'order',title:'Linked order'}])).toContain(scenario.display);
});

test('calendar header uses a two-digit day, textual month and year',()=>{
  expect(calendarDateLabel('2026-10-06')).toBe('06 Oct 2026');
  expect(calendarDateLabel('2026-01-08')).toBe('08 Jan 2026');
});
test('missing/invalid display values retain controlled fallbacks',()=>{
  expect(scheduleEventLabel(undefined)).toBe('Not recorded');expect(scheduleEventLabel('not a date')).toBe('Time unavailable');
});
test('all event displays share the owner-approved standard',()=>{
  expect(eventLabel('2026-10-06T07:00:00Z')).toBe('06 Oct 2026 · 10:00 AM');
});

import {formatDate,formatDateTime,formatAppointment} from '../../src/lib/datetime';
test('shared display dates, afternoon times and overnight ranges',()=>{
 expect(formatDate('2026-10-07')).toBe('07 Oct 2026');
 expect(formatDateTime('2026-10-07T10:30:00Z')).toBe('07 Oct 2026 · 01:30 PM');
 expect(formatAppointment('2026-10-07T07:00:00Z','2026-10-07T08:00:00Z')).toBe('07 Oct 2026 · 10:00 AM – 11:00 AM');
 expect(formatAppointment('2026-10-07T20:00:00Z','2026-10-07T22:00:00Z')).toBe('07 Oct 2026 · 11:00 PM – 08 Oct 2026 · 01:00 AM');
});
