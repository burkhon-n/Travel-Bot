from database import Base
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, ForeignKey, DateTime, Index, UniqueConstraint
from datetime import datetime
import enum

class PaymentStatus(enum.Enum):
    not_paid = "not_paid"
    half_paid = "half_paid"
    full_paid = "full_paid"

class TripMember(Base):
    __tablename__ = "trip_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey('trips.id'), nullable=False, index=True)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.not_paid, nullable=False, index=True)
    payment_receipt_file_id = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Composite indexes for common queries and constraints
    __table_args__ = (
        Index('ix_trip_payment_status', 'trip_id', 'payment_status'),  # For seat counting
        Index('ix_user_payment_status', 'user_id', 'payment_status'),  # For finding unpaid members
        Index('ix_user_joined', 'user_id', 'joined_at'),  # For finding recent registrations
        UniqueConstraint('user_id', 'trip_id', name='uq_user_trip'),  # Prevent duplicate registrations
    )