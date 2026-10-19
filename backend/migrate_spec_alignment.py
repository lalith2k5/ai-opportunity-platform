"""Add spec-alignment columns + tables (Spec sections 31, 33). Idempotent."""
from sqlalchemy import text
from app.database import engine


COLUMNS = [
    ("opportunities", "opportunity_score_spec", "DOUBLE PRECISION DEFAULT 0.0"),
    ("opportunities", "confidence_spec", "INTEGER DEFAULT 0"),
    ("opportunities", "weights_version", "VARCHAR(32) DEFAULT 'v1.0.0'"),
    ("opportunities", "confidence_version", "VARCHAR(32) DEFAULT 'v1.0.0'"),
    ("opportunities", "trend_window", "INTEGER DEFAULT 90"),
    ("opportunities", "status", "VARCHAR(32) DEFAULT 'PROPOSED'"),
    ("research_gaps", "kind", "VARCHAR(16) DEFAULT 'COVERAGE'"),
    ("research_gaps", "gap_status", "VARCHAR(32) DEFAULT 'PROPOSED'"),
    ("research_gaps", "gap_confidence", "INTEGER DEFAULT 0"),
    ("research_gaps", "supporting_limitations", "JSONB DEFAULT '[]'::jsonb"),
    ("opportunity_evidence", "polarity", "VARCHAR(16) DEFAULT 'SUPPORTS'"),
]


def main():
    print("[migrate_spec] adding columns")
    with engine.begin() as conn:
        for table, col, typ in COLUMNS:
            conn.execute(text(
                "ALTER TABLE " + table + " ADD COLUMN IF NOT EXISTS " + col + " " + typ
            ))
            print("  + " + table + "." + col)

    print("[migrate_spec] creating config tables")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS weight_configs (
                id SERIAL PRIMARY KEY,
                version VARCHAR(32) UNIQUE NOT NULL,
                w_problem DOUBLE PRECISION DEFAULT 0.20,
                w_tech DOUBLE PRECISION DEFAULT 0.15,
                w_gap DOUBLE PRECISION DEFAULT 0.20,
                w_trend DOUBLE PRECISION DEFAULT 0.15,
                w_evidence DOUBLE PRECISION DEFAULT 0.15,
                w_feasibility DOUBLE PRECISION DEFAULT 0.10,
                w_recency DOUBLE PRECISION DEFAULT 0.05,
                is_active BOOLEAN DEFAULT TRUE,
                published_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS confidence_configs (
                id SERIAL PRIMARY KEY,
                version VARCHAR(32) UNIQUE NOT NULL,
                beta1 DOUBLE PRECISION DEFAULT 0.30,
                beta2 DOUBLE PRECISION DEFAULT 0.25,
                beta3 DOUBLE PRECISION DEFAULT 0.25,
                beta4 DOUBLE PRECISION DEFAULT 0.20,
                n_max INTEGER DEFAULT 5,
                d_max INTEGER DEFAULT 6,
                conflict_penalty DOUBLE PRECISION DEFAULT 0.50,
                is_active BOOLEAN DEFAULT TRUE,
                published_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trend_configs (
                id SERIAL PRIMARY KEY,
                version VARCHAR(32) UNIQUE NOT NULL,
                window_short INTEGER DEFAULT 30,
                window_mid INTEGER DEFAULT 90,
                window_long INTEGER DEFAULT 365,
                emerging_threshold DOUBLE PRECISION DEFAULT 0.5,
                growing_threshold DOUBLE PRECISION DEFAULT 0.2,
                declining_threshold DOUBLE PRECISION DEFAULT -0.2,
                default_window INTEGER DEFAULT 90,
                is_active BOOLEAN DEFAULT TRUE,
                published_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
    print("[migrate_spec] done")


if __name__ == "__main__":
    main()
