from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WeatherRequestDeep(BaseModel):
    city: Optional[str] = Field(None, description="City name for weather query")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    query_type: str = Field("current", description="Type of query: current, today, tomorrow, weekly")

class WeatherResponseDeep(BaseModel):
    city: str
    temperature: Optional[float] = None
    conditions: str
    wind_speed: Optional[float] = None
    humidity: Optional[float] = None
    forecast: Optional[List[dict]] = None
    recommendations: Optional[List[str]] = None
    raw_data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class CityListResponseDeep(BaseModel):
    available_cities: List[str]
    count: int