from datetime import date
from typing import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from main.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

LEGACY_INTERVENTION_NAME = "Legacy (unassigned)"


def _backfill_legacy_rows(connection) -> None:
    """Attach rows logged before interventions were linked to a visible placeholder."""
    has_metrics = connection.execute(
        text("SELECT 1 FROM metrics WHERE intervention_id IS NULL LIMIT 1")
    ).first()
    has_events = connection.execute(
        text("SELECT 1 FROM events WHERE intervention_id IS NULL LIMIT 1")
    ).first()
    if not has_metrics and not has_events:
        return

    row = connection.execute(
        text("SELECT id FROM interventions WHERE name = :name"),
        {"name": LEGACY_INTERVENTION_NAME},
    ).first()
    if row is None:
        result = connection.execute(
            text(
                "INSERT INTO interventions (name, start_date, notes) "
                "VALUES (:name, :start_date, :notes)"
            ),
            {
                "name": LEGACY_INTERVENTION_NAME,
                "start_date": date.today().isoformat(),
                "notes": "Created by the schema migration to hold rows logged before "
                         "interventions were linked.",
            },
        )
        intervention_id = result.lastrowid
    else:
        intervention_id = row[0]

    connection.execute(
        text("UPDATE metrics SET intervention_id = :id WHERE intervention_id IS NULL"),
        {"id": intervention_id},
    )
    connection.execute(
        text("UPDATE events SET intervention_id = :id WHERE intervention_id IS NULL"),
        {"id": intervention_id},
    )


def ensure_schema(target_engine=None) -> None:
    """Create missing tables and add columns introduced after the first release."""
    from main.core import models  # noqa: F401 - register every table on Base.metadata

    target = target_engine or engine
    Base.metadata.create_all(bind=target)
    if target.dialect.name != "sqlite":
        return

    additions = {
        "interventions": (("projected_end_date", "DATE"),),
        "metrics": (("intervention_id", "INTEGER REFERENCES interventions(id)"),),
        "events": (("intervention_id", "INTEGER REFERENCES interventions(id)"),),
    }
    with target.begin() as connection:
        inspector = inspect(connection)
        for table, columns in additions.items():
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, sql_type in columns:
                if name not in existing:
                    connection.execute(
                        text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {sql_type}')
                    )
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_metrics_intervention_id ON metrics (intervention_id)"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_events_intervention_id ON events (intervention_id)"
        ))
        _backfill_legacy_rows(connection)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
