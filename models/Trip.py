from database import Base
from sqlalchemy import Column, Integer, String, BigInteger, Enum as SQLEnum
import enum

class TripStatus(enum.Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    group_id = Column(BigInteger, nullable=False, unique=True, index=True)
    participant_limit = Column(Integer, nullable=True)
    price = Column(Integer, nullable=False)  # Price in UZS
    card_info = Column(String, nullable=True)
    agreement_text = Column(String, nullable=True)
    participant_invite_link = Column(String, nullable=True)
    guest_invite_link = Column(String, nullable=True)
    status = Column(SQLEnum(TripStatus), default=TripStatus.active, nullable=False)