from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class ActivitySchema(BaseModel):
    id: Optional[int]
    name: str
    description: Optional[str]
    category: Optional[str]
    latitude: float
    longitude: float
    address: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class RouteSchema(BaseModel):
    id: Optional[int]
    start_latitude: float
    start_longitude: float
    end_latitude: Optional[float]
    end_longitude: Optional[float]
    distance: Optional[float]
    duration: Optional[int]
    created_at: Optional[datetime]
    activities: List[ActivitySchema] = []

class RouteActivitySchema(BaseModel):
    route_id: int
    activity_id: int
    distance_from_route: Optional[float]

class DestinationSchema(BaseModel):
    id: Optional[UUID]
    title: str
    type: Optional[str]
    location: Optional[str]
    notes: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    image_path: Optional[List[dict]]
    category_id: Optional[UUID]
    created_at: Optional[datetime]
    starttime: Optional[datetime]
    endtime: Optional[datetime]
    price: Optional[float]

class ReservationCreateSchema(BaseModel):
    user_id: UUID
    destination_id: UUID
    start_date: datetime
    end_date: datetime
    number_of_people: int
    total_price: float

class ReservationUpdateSchema(BaseModel):
    status: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None

class ReservationConfirmationSchema(BaseModel):
    payment_intent_id: str
    status: str

class ReservationSchema(BaseModel):
    id: Optional[UUID]
    user_id: UUID
    destination_id: UUID
    start_date: datetime
    end_date: datetime
    number_of_people: int
    total_price: float
    status: str
    stripe_payment_intent_id: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True 