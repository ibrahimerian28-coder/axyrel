-- OD-14: historical Schedule event timestamps represent Africa/Cairo wall clocks.
-- Run only after the reviewed backup/preflight procedure in task52_timezone_migration.md.
-- Atomic, one-time migration; no other event/audit timestamp columns are changed.
BEGIN;
LOCK TABLE schedules IN ACCESS EXCLUSIVE MODE;

DO $$
DECLARE
    wall timestamp without time zone;
    valid_instants integer;
BEGIN
    IF (SELECT count(*) FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'schedules'
          AND column_name IN ('start_at', 'end_at')
          AND data_type = 'timestamp without time zone') <> 2 THEN
        RAISE EXCEPTION 'Expected two naive Schedule event columns; review migration state before proceeding';
    END IF;

    FOR wall IN SELECT start_at FROM schedules UNION SELECT end_at FROM schedules LOOP
        -- Cairo offsets on either side of a transition produce all possible instants.
        -- Round-trip verification rejects gaps; multiple candidates reject overlaps.
        SELECT count(DISTINCT candidate) INTO valid_instants
        FROM (
            SELECT (wall AT TIME ZONE 'UTC') -
                   (((wall + days * interval '1 day') AT TIME ZONE 'UTC')
                    AT TIME ZONE 'Africa/Cairo' - (wall + days * interval '1 day')) AS candidate
            FROM generate_series(-2, 2, 2) AS days
        ) AS candidates
        WHERE candidate AT TIME ZONE 'Africa/Cairo' = wall;
        IF valid_instants <> 1 THEN
            RAISE EXCEPTION 'Unresolved Cairo Schedule wall clock: explicit historical offset required';
        END IF;
    END LOOP;

    IF EXISTS (SELECT 1 FROM schedules
               WHERE end_at AT TIME ZONE 'Africa/Cairo' <= start_at AT TIME ZONE 'Africa/Cairo') THEN
        RAISE EXCEPTION 'Invalid historical Schedule time range; review data before proceeding';
    END IF;
END $$;

ALTER TABLE schedules
    ALTER COLUMN start_at TYPE TIMESTAMPTZ USING start_at AT TIME ZONE 'Africa/Cairo',
    ALTER COLUMN end_at TYPE TIMESTAMPTZ USING end_at AT TIME ZONE 'Africa/Cairo';
COMMIT;
