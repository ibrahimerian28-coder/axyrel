-- OD-14: historical Service Visit event timestamps represent Africa/Cairo wall clocks.
-- Run only after the reviewed backup/preflight procedure in task53_timezone_migration.md.
-- Atomic, one-time migration; no other event/audit timestamp columns are changed.
BEGIN;
LOCK TABLE service_visits IN ACCESS EXCLUSIVE MODE;

DO $$
DECLARE
    wall timestamp without time zone;
    valid_instants integer;
BEGIN
    IF (SELECT count(*) FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'service_visits'
          AND column_name IN ('actual_start_at', 'actual_end_at')
          AND data_type = 'timestamp without time zone') <> 2 THEN
        RAISE EXCEPTION 'Expected two naive Service Visit event columns; review migration state before proceeding';
    END IF;

    FOR wall IN SELECT actual_start_at FROM service_visits UNION SELECT actual_end_at FROM service_visits LOOP
        IF wall IS NULL THEN
            CONTINUE;
        END IF;
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
            RAISE EXCEPTION 'Unresolved Cairo Service Visit wall clock: explicit historical offset required';
        END IF;
    END LOOP;

    IF EXISTS (SELECT 1 FROM service_visits
               WHERE actual_end_at AT TIME ZONE 'Africa/Cairo' < actual_start_at AT TIME ZONE 'Africa/Cairo') THEN
        RAISE EXCEPTION 'Invalid historical Service Visit time range; review data before proceeding';
    END IF;
END $$;

ALTER TABLE service_visits
    ALTER COLUMN actual_start_at TYPE TIMESTAMPTZ USING actual_start_at AT TIME ZONE 'Africa/Cairo',
    ALTER COLUMN actual_end_at TYPE TIMESTAMPTZ USING actual_end_at AT TIME ZONE 'Africa/Cairo';
COMMIT;
