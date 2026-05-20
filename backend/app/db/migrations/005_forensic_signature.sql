BEGIN;

ALTER TABLE forensic_packages ADD COLUMN signature_path TEXT;

COMMIT;
