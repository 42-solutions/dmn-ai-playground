# app/core/tools/weather_tool.py
from typing import Dict, Any, Optional
from app.services.weather_service_chatgpt import fetch_open_meteo, geocode
from app.core.weather_response_chatgpt import WeatherResponseChatGPT


async def get_weather_by_coords(latitude: float, longitude: float) -> Dict[str, Any]:
    raw = await fetch_open_meteo(latitude, longitude)
    parsed = WeatherResponseChatGPT(raw)
    return {
        "raw": raw,
        "current": parsed.current(),
        "today": parsed.today_summary(),
        "hourly_sample": parsed.hourly_zipped()[:12],  # first 12 hours
    }


async def get_weather_by_place(place: str) -> Dict[str, Any]:
    coords = await geocode(place)
    if not coords:
        return {"error": f"Could not find coordinates for '{place}'"}
    return await get_weather_by_coords(coords["lat"], coords["lon"])
