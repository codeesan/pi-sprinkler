from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from pg_database import Base

class Pins(Base):
    __tablename__ = "pins"
    pi_version = Column(Integer,nullable=False)
    pin = Column(Integer,nullable=False)
    bcm = Column(Integer,nullable=False)
    unique_id = Column(UUID(as_uuid=True), primary_key=True)

