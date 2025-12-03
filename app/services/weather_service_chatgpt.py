# app/services/weather_service_chatgpt.py
from typing import Dict, Any, Optional
import httpx

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"


class WeatherServiceChatGPT:
    """
    Responsible for:
      - turning lat/lon requests into Open-Meteo calls
      - optional geocoding (city -> lat/lon) using Nominatim (OpenStreetMap)
    """

    async def geocode(self, location: str) -> Optional[Dict[str, float]]:
        """
        Use Nominatim to resolve a free-text location -> lat/lon.
        Returns dict {'lat': float, 'lon': float} or None.
        NOTE: Nominatim has usage policies; for production use a proper geocoding service.
        """
        params = {"q": location, "format": "json", "limit": 1}
        async with httpx.AsyncClient() as client:
            r = await client.get(NOMINATIM_BASE, params=params, timeout=10.0)
            r.raise_for_status()
            data = r.json()
            if not data:
                return None
            item = data[0]
            return {"lat": float(item["lat"]), "lon": float(item["lon"])}

    async def fetch_open_meteo(
        self, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "timezone": "UTC",  # or adjust as needed
        }
        async with httpx.AsyncClient() as client:
            r = await client.get(OPEN_METEO_BASE, params=params, timeout=10.0)
            r.raise_for_status()
            return r.json()
