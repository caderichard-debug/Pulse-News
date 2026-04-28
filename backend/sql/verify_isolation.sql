-- Pulse: verify runtime role isolation (run as postgres/superuser).
-- Replace app_pulse_rw / proj_pulse with your runtime role and schema.
-- Expect: zero rows for checks A–D (or review D intentionally).

-- A. Runtime role must NOT have USAGE on any schema other than proj_pulse (+ system catalogs)
SELECT n.nspname AS schema_with_usage
FROM pg_namespace n
WHERE has_schema_privilege('app_pulse_rw', n.nspname, 'USAGE')
  AND n.nspname NOT IN ('proj_pulse', 'pg_catalog', 'information_schema');

-- B. Runtime role must NOT have CREATE on any schema other than proj_pulse
SELECT n.nspname AS schema_with_create
FROM pg_namespace n
WHERE has_schema_privilege('app_pulse_rw', n.nspname, 'CREATE')
  AND n.nspname <> 'proj_pulse';

-- C. Runtime role must NOT have table grants outside proj_pulse
SELECT table_schema, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'app_pulse_rw'
  AND table_schema <> 'proj_pulse';

-- D. Roles that app_pulse_rw is a member of (empty is strictest; review any rows)
SELECT r.rolname AS member_of_group
FROM pg_auth_members m
JOIN pg_roles r ON r.oid = m.roleid
WHERE m.member = (SELECT oid FROM pg_roles WHERE rolname = 'app_pulse_rw');

-- E. Default search_path for the role (expect rolconfig to include search_path=proj_pulse,public)
SELECT rolname, rolconfig
FROM pg_roles
WHERE rolname = 'app_pulse_rw';
