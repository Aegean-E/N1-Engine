import pandas as pd
from sqlalchemy.orm import Session
from typing import Literal
import logging
from pee.core.models import MetricEntry, Intervention, EventEntry
from pee.core.database import SessionLocal

logger = logging.getLogger(__name__)

class DataManager:
    """
    Manages data import and export.
    """
    def __init__(self, db: Session = None):
        self.db = db if db else SessionLocal()

    def import_from_csv(self, filepath: str, data_type: Literal['metrics', 'interventions', 'events']) -> dict:
        """
        Imports data from a CSV file.
        Returns a dictionary with success/failure status and message.
        """
        try:
            df = pd.read_csv(filepath)

            if data_type == 'metrics':
                required_cols = ['date', 'metric_name', 'value']
                if not all(col in df.columns for col in required_cols):
                    return {"success": False, "message": f"CSV must contain columns: {required_cols}"}

                # Use pandas to handle date parsing
                df['date'] = pd.to_datetime(df['date']).dt.date

                entries = []
                for _, row in df.iterrows():
                    entries.append(MetricEntry(
                        date=row['date'],
                        metric_name=row['metric_name'],
                        value=row['value']
                    ))
                self.db.bulk_save_objects(entries)
                self.db.commit()
                return {"success": True, "message": f"Successfully imported {len(entries)} metric entries."}

            elif data_type == 'interventions':
                required_cols = ['name', 'start_date']
                if not all(col in df.columns for col in required_cols):
                    return {"success": False, "message": f"CSV must contain columns: {required_cols}"}

                df['start_date'] = pd.to_datetime(df['start_date']).dt.date
                if 'end_date' in df.columns:
                     df['end_date'] = pd.to_datetime(df['end_date']).dt.date
                else:
                     df['end_date'] = pd.NaT

                entries = []
                for _, row in df.iterrows():
                    end_date = row['end_date'] if pd.notna(row.get('end_date')) else None
                    entries.append(Intervention(
                        name=row['name'],
                        start_date=row['start_date'],
                        end_date=end_date,
                        dosage=row.get('dosage'), # Optional
                        notes=row.get('notes') # Optional
                    ))
                self.db.bulk_save_objects(entries)
                self.db.commit()
                return {"success": True, "message": f"Successfully imported {len(entries)} interventions."}

            elif data_type == 'events':
                 required_cols = ['timestamp', 'event_name']
                 if not all(col in df.columns for col in required_cols):
                    return {"success": False, "message": f"CSV must contain columns: {required_cols}"}

                 df['timestamp'] = pd.to_datetime(df['timestamp'])

                 entries = []
                 for _, row in df.iterrows():
                    entries.append(EventEntry(
                        timestamp=row['timestamp'],
                        event_name=row['event_name'],
                        severity=row.get('severity'), # Optional
                        notes=row.get('notes') # Optional
                    ))
                 self.db.bulk_save_objects(entries)
                 self.db.commit()
                 return {"success": True, "message": f"Successfully imported {len(entries)} events."}

            else:
                return {"success": False, "message": "Invalid data type."}

        except Exception as e:
            self.db.rollback()
            logger.error(f"Import failed: {e}")
            return {"success": False, "message": f"Import failed: {str(e)}"}

    def export_to_csv(self, filepath: str, data_type: Literal['metrics', 'interventions', 'events']) -> dict:
        """
        Exports data to a CSV file.
        Returns a dictionary with success/failure status and message.
        """
        try:
            if data_type == 'metrics':
                query = self.db.query(MetricEntry)
                df = pd.read_sql(query.statement, self.db.bind)
                # Drop id column if present for cleaner export
                if 'id' in df.columns:
                    df = df.drop(columns=['id'])
                df.to_csv(filepath, index=False)
                return {"success": True, "message": f"Successfully exported metrics to {filepath}."}

            elif data_type == 'interventions':
                query = self.db.query(Intervention)
                df = pd.read_sql(query.statement, self.db.bind)
                if 'id' in df.columns:
                     df = df.drop(columns=['id'])
                df.to_csv(filepath, index=False)
                return {"success": True, "message": f"Successfully exported interventions to {filepath}."}

            elif data_type == 'events':
                query = self.db.query(EventEntry)
                df = pd.read_sql(query.statement, self.db.bind)
                if 'id' in df.columns:
                     df = df.drop(columns=['id'])
                df.to_csv(filepath, index=False)
                return {"success": True, "message": f"Successfully exported events to {filepath}."}

            else:
                 return {"success": False, "message": "Invalid data type."}

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {"success": False, "message": f"Export failed: {str(e)}"}
