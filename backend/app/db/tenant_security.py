"""
PostgreSQL Row-Level Security for multi-tenant isolation.

Activate with ``ENABLE_POSTGRES_RLS=true`` in production after schema migration 008
has run (adds organization_id to forensic_packages).

Call ``apply_rls_if_enabled`` once at startup via ``init_database``.
Call ``set_tenant_context`` inside each request that touches tenant-scoped tables.
"""

from __future__ import annotations

from typing import Any

ENABLE_RLS_SQL = """
ALTER TABLE hdrs ENABLE ROW LEVEL SECURITY;
ALTER TABLE missions ENABLE ROW LEVEL SECURITY;
ALTER TABLE forensic_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_hdrs ON hdrs;
CREATE POLICY tenant_isolation_hdrs ON hdrs
    USING (organization_id = current_setting('app.current_organization_id', true));

DROP POLICY IF EXISTS tenant_isolation_missions ON missions;
CREATE POLICY tenant_isolation_missions ON missions
    USING (organization_id = current_setting('app.current_organization_id', true));

DROP POLICY IF EXISTS tenant_isolation_forensic ON forensic_packages;
CREATE POLICY tenant_isolation_forensic ON forensic_packages
    USING (organization_id = current_setting('app.current_organization_id', true));

DROP POLICY IF EXISTS tenant_isolation_agent_configs ON agent_configs;
CREATE POLICY tenant_isolation_agent_configs ON agent_configs
    USING (organization_id = current_setting('app.current_organization_id', true));

DROP POLICY IF EXISTS tenant_isolation_users ON users;
CREATE POLICY tenant_isolation_users ON users
    USING (organization_id = current_setting('app.current_organization_id', true));
"""


def set_tenant_context(conn: Any, organization_id: str) -> None:
    """Set per-session variable consumed by RLS policies.

    ``conn`` must be a ``CompatConnection`` — the execute() wrapper handles
    the ``?`` → ``%s`` placeholder translation for PostgreSQL.
    """
    conn.execute(
        "SELECT set_config('app.current_organization_id', ?, false)",
        (organization_id,),
    )


def apply_rls_if_enabled(conn: Any, *, enabled: bool) -> None:
    if not enabled:
        return
    conn.executescript(ENABLE_RLS_SQL)
