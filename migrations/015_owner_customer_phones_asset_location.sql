-- Additive Owner Acceptance Round 1. Legacy columns/values remain untouched.
-- NULL phones means legacy phone/phone_1..4 remain the source until explicitly edited.
-- No guessed Customer-to-Asset location transfer and no assumed legacy warranty duration.
BEGIN;
ALTER TABLE customers ADD COLUMN phones JSONB;
ALTER TABLE assets ADD COLUMN country VARCHAR(2);
ALTER TABLE assets ADD COLUMN state VARCHAR(150);
ALTER TABLE assets ADD COLUMN area VARCHAR(150);
ALTER TABLE assets ADD COLUMN address VARCHAR(500);
ALTER TABLE assets ADD COLUMN location_url VARCHAR(1000);
ALTER TABLE assets ADD COLUMN maintenance_cycle INTEGER;
ALTER TABLE assets ADD COLUMN warranty_years INTEGER;
ALTER TABLE assets ADD CONSTRAINT assets_maintenance_cycle_nonnegative CHECK (maintenance_cycle IS NULL OR maintenance_cycle BETWEEN 1 AND 1200);
ALTER TABLE assets ADD CONSTRAINT assets_warranty_years_nonnegative CHECK (warranty_years IS NULL OR warranty_years BETWEEN 0 AND 100);
COMMIT;
