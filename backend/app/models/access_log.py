from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from app.database.db import Base


class AccessLog(Base):
    __tablename__ = "access_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)

    patient_id = Column(
        String(20),
        ForeignKey("patients.patient_id"),
        nullable=False
    )

    location_id = Column(
        String(20),
        ForeignKey("locations.location_id"),
        nullable=False
    )

    enter_time = Column(DateTime, nullable=False)

    exit_time = Column(DateTime)