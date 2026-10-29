import sqlite3

from sqlalchemy import create_engine, inspect

from main.core.database import ensure_schema
from main.core.settings_manager import SettingsManager


def _old_database(path):
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE interventions (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            dosage VARCHAR,
            notes VARCHAR
        );
        CREATE TABLE metrics (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            metric_name VARCHAR NOT NULL,
            value FLOAT NOT NULL
        );
        CREATE TABLE events (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            event_name VARCHAR NOT NULL,
            severity INTEGER,
            notes VARCHAR
        );
        INSERT INTO interventions (id, name, start_date) VALUES (1, 'Legacy', '2026-01-01');
        INSERT INTO metrics (id, date, metric_name, value) VALUES (1, '2026-01-02', 'Sleep', 8.0);
        """
    )
    connection.commit()
    connection.close()


def test_ensure_schema_upgrades_an_old_sqlite_database(tmp_path):
    path = tmp_path / "legacy.db"
    _old_database(path)
    engine = create_engine(f"sqlite:///{path.as_posix()}")

    ensure_schema(engine)

    inspector = inspect(engine)
    assert "projected_end_date" in {column["name"] for column in inspector.get_columns("interventions")}
    assert "intervention_id" in {column["name"] for column in inspector.get_columns("metrics")}
    assert "intervention_id" in {column["name"] for column in inspector.get_columns("events")}
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT COUNT(*) FROM interventions").scalar() == 1
        assert connection.exec_driver_sql("SELECT COUNT(*) FROM metrics").scalar() == 1


def test_save_settings_reports_failure(tmp_path):
    manager = SettingsManager(settings_file=str(tmp_path / "settings.json"))
    assert manager.save_settings() is True

    unwritable = SettingsManager(settings_file=str(tmp_path))
    assert unwritable.save_settings() is False
