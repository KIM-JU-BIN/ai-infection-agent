from sqlalchemy import Column, String, Integer

from app.database.db import Base


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(String(20), primary_key=True)
    zone_name = Column(String(100), nullable=False)
    location_type = Column(String(50), nullable=False)
    floor = Column(Integer)