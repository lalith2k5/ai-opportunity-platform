"""Phase 10.4 -- promote Organization to a first-class model.

Creates organizations table; adds problem_profiles.organization_id FK.
Idempotent.
"""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate_d3b] organizations table")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS organizations ("
            "  id SERIAL PRIMARY KEY,"
            "  name VARCHAR(300) NOT NULL,"
            "  canonical_name VARCHAR(200) NOT NULL,"
            "  industry_domain VARCHAR(120),"
            "  source VARCHAR(64),"
            "  created_at TIMESTAMPTZ DEFAULT NOW()"
            ")"
        ))
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_organizations_canonical "
            "ON organizations (canonical_name)"
        ))
        conn.execute(text(
            "ALTER TABLE problem_profiles "
            "ADD COLUMN IF NOT EXISTS organization_id INTEGER "
            "REFERENCES organizations(id) ON DELETE SET NULL"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_problem_profiles_org_id "
            "ON problem_profiles (organization_id)"
        ))
    print("[migrate_d3b] done")


if __name__ == "__main__":
    main()
