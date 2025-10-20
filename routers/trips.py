"""API routes for trip management."""

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import logging

from database import get_db
from models.Trip import Trip
from bot import bot

router = APIRouter(prefix="/api/trips", tags=["trips"])


class CreateTripRequest(BaseModel):
    """Request model for creating a new trip."""
    name: str = Field(..., description="Trip name")
    group_id: int = Field(..., description="Telegram group ID")
    participant_limit: Optional[int] = Field(None, ge=1)
    price: int = Field(..., gt=0, description="Trip price in UZS")
    card_info: Optional[str] = None
    agreement_text: Optional[str] = None


class TripResponse(BaseModel):
    """Response model for trip data."""
    id: int
    name: str
    group_id: int
    participant_limit: Optional[int]
    price: int
    card_info: Optional[str]
    agreement_text: Optional[str]
    participant_invite_link: Optional[str] = None
    guest_invite_link: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/create", response_model=TripResponse)
async def create_trip(trip_data: CreateTripRequest, db: Session = Depends(get_db)):
    """Create a new trip for a group.
    
    Args:
        trip_data: Trip details including name, group_id, and optional settings
        db: Database session
        
    Returns:
        The created trip data
        
    Raises:
        HTTPException: If trip creation fails or group already has a trip
    """
    logging.info(
        "trip.create request name=%s group_id=%s participant_limit=%s price=%s",
        trip_data.name,
        trip_data.group_id,
        trip_data.participant_limit,
        trip_data.price,
    )

    try:
        # Check if a trip already exists for this group
        existing_trip = db.query(Trip).filter(Trip.group_id == trip_data.group_id).first()
        if existing_trip:
            logging.info(
                "trip.create conflict existing_trip_id=%s group_id=%s",
                existing_trip.id,
                trip_data.group_id,
            )
            raise HTTPException(
                status_code=400,
                detail=f"A trip already exists for this group: {existing_trip.name}",
            )

        # Create new trip
        new_trip = Trip(
            name=trip_data.name,
            group_id=trip_data.group_id,
            participant_limit=trip_data.participant_limit,
            price=trip_data.price,
            card_info=trip_data.card_info,
            agreement_text=trip_data.agreement_text,
        )

        db.add(new_trip)
        db.commit()
        db.refresh(new_trip)
        logging.info(
            "trip.create success id=%s group_id=%s", new_trip.id, new_trip.group_id
        )

        # Create invite links (best-effort; don't fail trip creation if these fail)
        try:
            participant_link = await bot.create_chat_invite_link(
                chat_id=trip_data.group_id,
                name=f"Participants - {trip_data.name}",
                creates_join_request=False,
            )
            new_trip.participant_invite_link = getattr(
                participant_link, "invite_link", None
            )
            logging.info(
                "trip.invite participant link created group_id=%s",
                trip_data.group_id,
            )

            guest_link = await bot.create_chat_invite_link(
                chat_id=trip_data.group_id,
                name=f"Guests - {trip_data.name}",
                creates_join_request=True,
            )
            new_trip.guest_invite_link = getattr(guest_link, "invite_link", None)
            logging.info(
                "trip.invite guest link created group_id=%s", trip_data.group_id
            )

            db.commit()
            db.refresh(new_trip)
        except Exception:
            logging.exception("trip.invite failed group_id=%s", trip_data.group_id)

        return new_trip

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.exception(
            "trip.create failed name=%s group_id=%s",
            trip_data.name,
            trip_data.group_id,
        )
        raise HTTPException(status_code=500, detail=f"Failed to create trip: {str(e)}")


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: int, db: Session = Depends(get_db)):
    """Get trip details by ID.
    
    Args:
        trip_id: The ID of the trip to retrieve
        db: Database session
        
    Returns:
        The trip data
        
    Raises:
        HTTPException: If trip not found
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return trip


@router.get("/group/{group_id}", response_model=TripResponse)
async def get_trip_by_group(group_id: int, db: Session = Depends(get_db)):
    """Get trip details by group ID.
    
    Args:
        group_id: The Telegram group ID
        db: Database session
        
    Returns:
        The trip data for this group
        
    Raises:
        HTTPException: If trip not found for this group
    """
    trip = db.query(Trip).filter(Trip.group_id == group_id).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="No trip found for this group")
    
    return trip
