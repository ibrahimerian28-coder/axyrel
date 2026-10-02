# Task 52 — Schedule Event-Time Migration Review

Authority: owner decision OD-14, 2026-10-02. Only Schedule event fields are included. Task 53 remains responsible for Service Visit event fields.

## Columns and Conversion

| Column | Current SQL / ORM type | Target SQL / ORM type | Historical conversion |
|---|---|---|---|
| schedules.start_at | TIMESTAMP WITHOUT TIME ZONE / DateTime | TIMESTAMPTZ / DateTime(timezone=True) | start_at AT TIME ZONE 'Africa/Cairo' |
| schedules.end_at | TIMESTAMP WITHOUT TIME ZONE / DateTime | TIMESTAMPTZ / DateTime(timezone=True) | end_at AT TIME ZONE 'Africa/Cairo' |

Migration: migrations/012_schedule_event_timezone.sql. The original source types are defined in migration 001 and the pre-task Schedule model. Existing API/service code passed supplied event datetimes through without defining a different historical timezone. No repository evidence establishes a contradictory historical writer. OD-14 supplies the authoritative historical Cairo interpretation; this is not a claim that production rows have been reviewed or migrated.

PostgreSQL stores TIMESTAMPTZ as instants; its session timezone changes display, not stored meaning. Explicit `AT TIME ZONE 'Africa/Cairo'` preserves historical local wall-clock meaning without depending on session timezone. Incoming aware values retain their instant, naive values are interpreted as Cairo, and API event outputs normalize to UTC with an explicit offset.

No work_orders.scheduled_start/scheduled_end, service_visits.actual_start_at/actual_end_at, created_at, updated_at, invoice, expense, contract, or DATE columns change. No company timezone field or new metadata entity is introduced.

## Safety / Deployment Prerequisites

1. Before deployment, back up the database and verify the exact target schema and both source types. Use the intended application schema as the connection search_path. Audit actual historical writer evidence; stop if a different historical semantic is established.
2. Review historical event ranges and Cairo DST boundary rows. Missing offset provenance for overlaps/gaps requires an explicit historical decision; never guess or silently shift those rows.
3. Plan a maintenance window: this migration locks schedules exclusively and can rewrite the table/index. It runs in one transaction, checks both source types, and rejects invalid historical ranges, nonexistent times, and ambiguous times before conversion.
4. Run the reviewed migration before serving the new Schedule code. This is a one-time migration, not a startup hook. A second execution refuses already-converted types rather than converting twice.
5. Verify offset-aware reads and representative winter/summer instants after deployment. Retain backup and rollback plan. **No production migration was executed during Task 52.**

The SQL DST guard derives Cairo offsets from samples two days before, at, and two days after each wall clock. Cairo transition offsets are thereby considered on both sides, including historical non-hour offset changes; candidates must round-trip exactly. Zero candidates rejects a gap; multiple candidates rejects an overlap. The migration never assigns an offset to unresolved historical data.

## Disposable PostgreSQL Verification

tests/test_task52_work_order_scheduling.py creates a uniquely named `axyrel_task52_test_<uuid>` database using the configured local server credentials through the maintenance database. It never connects to or mutates the configured application database. It drops only its generated database after closing test connections. CREATE DATABASE privilege is required; absence is a test failure rather than an unreported skip.

Runtime fixtures use the timezone-aware ORM. Separate disposable historical schemas execute the actual SQL migration against old TIMESTAMP columns. Coverage includes winter/summer conversion under a non-Cairo session timezone, unchanged created_at, gap/overlap/range rejection with unchanged rows/types after rollback, refusal of a second conversion, and an empty historical table. The suite also checks reloaded instants under a different PostgreSQL session timezone.

Run this suite in its own process with the configured PostgreSQL environment; older regression files deliberately install separate SQLite environments and are run in separate processes.

## Rollback Considerations

Any pre-COMMIT error requires ROLLBACK and leaves both columns/data unchanged. No partial column conversion is accepted. After commit, prefer restoring the reviewed backup and matching old application code during the maintenance window.

An intentional reverse conversion would use `start_at AT TIME ZONE 'Africa/Cairo'` and `end_at AT TIME ZONE 'Africa/Cairo'` back to TIMESTAMP WITHOUT TIME ZONE, with exclusive locking and old-code coordination. It preserves Cairo wall-clock display but loses explicit instant/offset information, especially for new rows in overlapping hours. It is not supplied or executed automatically; review post-migration writes and backups before considering it.
