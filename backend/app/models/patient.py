from sqlalchemy import Column, String, Date, ForeignKey

from app.database.db import Base


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    admission_date = Column(Date, nullable=False)
    diagnosis = Column(String(200))
    current_location_id = Column(
        String(20),
        ForeignKey("locations.location_id")
    )