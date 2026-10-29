from typing import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from main.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


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


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
