"""
PostgreSQL Row-Level Security for multi-tenant isolation (opcional).

Activar com ``ENABLE_POSTGRES_RLS=true`` após políticas validadas em staging.
"""

from __future__ import annotations

from typing import Any

ENABLE_RLS_SQL = """
ALTER TABLE hdrs ENABLE ROW LEVEL SECURITY;
ALTER TABLE missions ENABLE ROW LEVEL SECURITY;
ALTER TABLE forensic_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_hdrs ON hdrs
    USING (organization_id = current_setting('app.current_organization_id', true));

CREATE POLICY tenant_isolation_missions ON missions
    USING (organization_id = current_setting('app.current_organization_id', true));

CREATE POLICY tenant_isolation_forensic ON forensic_packages
    USING (true);

CREATE POLICY tenant_isolation_agent_configs ON agent_configs
    USING (organization_id = current_setting('app.current_organization_id', true));

CREATE POLICY tenant_isolation_users ON users
    USING (organization_id = current_setting('app.current_organization_id', true));
"""


def set_tenant_context(conn: Any, organization_id: str) -> None:
    """Set session variable consumed by RLS policies."""

    conn.execute(
        "SELECT set_config('app.current_organization_id', ?, false)",
        (organization_id,),
    )


def apply_rls_if_enabled(conn: Any, *, enabled: bool) -> None:
    if not enabled:
        return
    conn.executescript(ENABLE_RLS_SQL)
