from pydantic import BaseModel
from typing import Optional, List


class DeliveryProvider(BaseModel):
    """Represents a delivery provider (DoorDash, Uber Eats, etc.)"""
    name: str
    url: str


class Restaurant(BaseModel):
    """Represents a restaurant from Google Maps search"""
    name: str
    address: str
    kgmid: str
    place_id: str
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    lat: float
    lng: float
    doordash_url: Optional[str] = None
    delivery_providers: List[DeliveryProvider] = []
    distance_km: Optional[float] = None
