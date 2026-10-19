"""Create tables for conflict_flags, feedback, license_records, change_events,
limitations (spec 31 + modules 11, 18, 19). Idempotent."""
from sqlalchemy import text
from app.database import engine


def main():
    print("[migrate_m18] creating tables")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conflict_flags (
                id SERIAL PRIMARY KEY,
                target_type VARCHAR(32) NOT NULL,
                target_id VARCHAR(64) NOT NULL,
                severity VARCHAR(16) NOT NULL DEFAULT 'MINOR',
                rule_applied VARCHAR(16) NOT NULL DEFAULT 'UNRESOLVED',
                evidence_ids JSONB DEFAULT '[]'::jsonb,
                raised_at TIMESTAMPTZ DEFAULT NOW(),
                resolved_at TIMESTAMPTZ,
                resolution TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                target_type VARCHAR(32) NOT NULL,
                target_id VARCHAR(64) NOT NULL,
                user_id INTEGER REFERENCES users(id),
                rating INTEGER,
                comment TEXT,
                decision VARCHAR(32),
                rationale TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS license_records (
                id SERIAL PRIMARY KEY,
                source_name VARCHAR(64) UNIQUE NOT NULL,
                status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
                terms_url VARCHAR(500),
                robots_policy VARCHAR(64),
                redistribution VARCHAR(64),
                pii_rules TEXT,
                retention_days INTEGER,
                legal_basis VARCHAR(200),
                next_review_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS change_events (
                id SERIAL PRIMARY KEY,
                entity_type VARCHAR(32) NOT NULL,
                entity_id VARCHAR(64) NOT NULL,
                change_type VARCHAR(64) NOT NULL,
                detected_at TIMESTAMPTZ DEFAULT NOW(),
                significance VARCHAR(16) NOT NULL DEFAULT 'MINOR'
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS limitations (
                id SERIAL PRIMARY KEY,
                paper_id INTEGER NOT NULL REFERENCES problem_papers(id),
                description TEXT NOT NULL,
                category VARCHAR(64),
                limitation_source VARCHAR(16) NOT NULL DEFAULT 'EXPLICIT',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_limitations_paper ON limitations(paper_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_conflict_flags_target ON conflict_flags(target_type, target_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_feedback_target ON feedback(target_type, target_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_change_events_entity ON change_events(entity_type, entity_id)"))

        print("[migrate_m18] seeding LicenseRecord rows for known sources")
        for name in ("github", "arxiv", "news", "rd_cells", "challenge_portal", "patents", "reddit"):
            conn.execute(text("""
                INSERT INTO license_records (source_name, status, robots_policy, redistribution, legal_basis)
                VALUES (:n, 'PENDING', 'honour', 'metadata+snippet', 'legitimate interest')
                ON CONFLICT (source_name) DO NOTHING
            """), {"n": name})
    print("[migrate_m18] done")


if __name__ == "__main__":
    main()
