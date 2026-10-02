# Task 53 — Service Visit Event-Time Migration Review

Authority: OD-14 and OD-15, 2026-10-02. Migration: migrations/013_service_visit_event_timezone.sql.

Only service_visits.actual_start_at and actual_end_at change from nullable TIMESTAMP WITHOUT TIME ZONE / DateTime to nullable TIMESTAMPTZ / DateTime(timezone=True). Historical values convert with `AT TIME ZONE 'Africa/Cairo'`; NULL remains NULL. Equal start/end instants remain valid under the accepted Service Visit range contract. No Schedule, Work Order, audit timestamp, DATE field or timezone metadata changes.

The historical source types are recorded in migration 001 and the pre-task ORM. The existing API/service/repository passed supplied actual event values through; the API-backed maintenance UI does not write these timestamps. Inspection found no definitive contradictory historical timezone writer. OD-14 authorizes Cairo interpretation; actual production writer/data review remains a deployment prerequisite.

Aware input preserves its instant and normalizes to UTC. Naive input represents Cairo wall time. Gaps and overlaps require explicit offsets. Both CREATE and effective PATCH ranges compare normalized instants. API output includes an explicit UTC offset; query bounds follow the same input policy.

## Deployment and safety

1. Back up the target database, confirm schema/search_path and both original column types, and review actual historical writer evidence. Stop if it contradicts Cairo interpretation.
2. Review historical Cairo DST gaps/overlaps and ranges. Unresolved historical offsets require evidence or an explicit owner decision; do not guess.
3. Schedule maintenance and coordinate old/new application versions. The one-time migration takes an exclusive table lock and may rewrite table/index data. Apply it before serving the changed Service Visit model.
4. The transaction checks original types, skips NULL wall clocks, rejects nonexistent/ambiguous local timestamps and reversed ranges, then converts both columns atomically. Repeated conversion is refused.
5. Verify representative winter/summer instants and offset-aware reads after deployment. Retain backup and rollback plan. No production migration was performed in Task 53.

The DST guard reuses the reviewed Task 52 algorithm: offsets sampled two days before, at and two days after each wall clock produce candidate instants; exact Cairo round trips require exactly one candidate. This includes historical non-hour Cairo offset changes.

## Verification

tests/test_task53_schedule_service_visit.py creates a uniquely named local PostgreSQL database and drops only that generated database after closing connections. The configured application database is never connected to or modified. Separate disposable historical schemas execute the actual SQL migration.

Coverage includes winter/summer conversion under a different session timezone, unchanged created_at and nullability, nullable/equal ranges, DST gap/overlap and reversed-range atomic rejection, repeat-conversion refusal and empty-table conversion. ORM/API tests verify instants survive PostgreSQL reload under another session timezone.

## Rollback

Before COMMIT, any error requires ROLLBACK and preserves original types/data. After commit, prefer restoring the reviewed backup with matching old application code in the maintenance window.

A reviewed reverse conversion would use `actual_start_at AT TIME ZONE 'Africa/Cairo'` and `actual_end_at AT TIME ZONE 'Africa/Cairo'` back to TIMESTAMP WITHOUT TIME ZONE under exclusive locking. It loses explicit instant information for overlapping hours, particularly for new writes. No automatic reverse migration or production operation is supplied or executed.
