from sqlalchemy import Column, Integer, String, Date, Float, DateTime, CheckConstraint
from .database import Base

class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    dosage = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    def __repr__(self):
        return f"<Intervention(name='{self.name}', start_date={self.start_date})>"

class MetricEntry(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    metric_name = Column(String, index=True, nullable=False)
    value = Column(Float, nullable=False)

    def __repr__(self):
        return f"<MetricEntry(date={self.date}, metric_name='{self.metric_name}', value={self.value})>"

class EventEntry(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint('severity >= 1 AND severity <= 5', name='check_severity_range'),
    )

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    event_name = Column(String, index=True, nullable=False)
    severity = Column(Integer, nullable=True) # 1-5
    notes = Column(String, nullable=True)

    def __repr__(self):
        return f"<EventEntry(timestamp={self.timestamp}, event_name='{self.event_name}', severity={self.severity})>"
