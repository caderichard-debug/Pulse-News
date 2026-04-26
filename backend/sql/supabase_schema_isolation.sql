-- Pulse Supabase schema isolation bootstrap
-- Run as a privileged/admin role in Supabase SQL editor.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'proj_pulse') THEN
    EXECUTE 'CREATE SCHEMA proj_pulse';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_pulse_rw') THEN
    EXECUTE 'CREATE ROLE app_pulse_rw LOGIN PASSWORD ''J6+8i4jaud9dEMPkZZ9SMvuV4fMoGejlVwyqEMu4r+c=''';
  ELSE
    EXECUTE 'ALTER ROLE app_pulse_rw WITH LOGIN PASSWORD ''J6+8i4jaud9dEMPkZZ9SMvuV4fMoGejlVwyqEMu4r+c=''';
  END IF;
END $$;

GRANT USAGE ON SCHEMA proj_pulse TO app_pulse_rw;
GRANT CREATE ON SCHEMA proj_pulse TO app_pulse_rw;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA proj_pulse TO app_pulse_rw;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA proj_pulse TO app_pulse_rw;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA proj_pulse TO app_pulse_rw;

ALTER ROLE app_pulse_rw IN DATABASE postgres SET search_path = proj_pulse, public;

ALTER DEFAULT PRIVILEGES IN SCHEMA proj_pulse
  GRANT ALL PRIVILEGES ON TABLES TO app_pulse_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA proj_pulse
  GRANT ALL PRIVILEGES ON SEQUENCES TO app_pulse_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA proj_pulse
  GRANT ALL PRIVILEGES ON FUNCTIONS TO app_pulse_rw;

REVOKE ALL ON SCHEMA proj_pulse FROM PUBLIC;
