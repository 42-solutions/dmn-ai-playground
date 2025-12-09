import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from dateutil import parser

logger = logging.getLogger(__name__)


class WeatherServiceDeep:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    # City coordinates database
    CITY_COORDINATES = {
        "berlin": (52.52, 13.41),
        "london": (51.51, -0.13),
        "new york": (40.71, -74.01),
        "tokyo": (35.68, 139.69),
        "paris": (48.85, 2.35),
        "sydney": (-33.87, 151.21),
        "mumbai": (19.08, 72.88),
        "beijing": (39.90, 116.41),
        "san francisco": (37.77, -122.42),
        "singapore": (1.35, 103.82),
        "dubai": (25.27, 55.31),
        "moscow": (55.76, 37.62)
    }

    async def get_weather(self, latitude: float, longitude: float, city_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetch weather data from Open-Meteo API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,wind_speed_10m,weather_code",
                    "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                    "timezone": "auto",
                    "forecast_days": 7
                }

                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if city_name:
                    data["city"] = city_name
                else:
                    data["city"] = f"{latitude},{longitude}"

                return {"success": True, "data": data}

        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return {"success": False, "error": str(e)}

    async def get_weather_by_city(self, city_name: str) -> Dict[str, Any]:
        """Get weather for a city name"""
        city_lower = city_name.lower()

        if city_lower in self.CITY_COORDINATES:
            lat, lon = self.CITY_COORDINATES[city_lower]
            return await self.get_weather(lat, lon, city_name)
        else:
            # Try to find partial match
            for city_key, coords in self.CITY_COORDINATES.items():
                if city_lower in city_key or city_key in city_lower:
                    lat, lon = coords
                    return await self.get_weather(lat, lon, city_name)

            # Default to Berlin
            return await self.get_weather(52.52, 13.41, "Berlin")

    def format_current_weather(self, weather_data: Dict) -> str:
        """Format current weather into human-readable text"""
        if not weather_data["success"]:
            return "Sorry, I couldn't fetch the weather data at the moment."

        data = weather_data["data"]
        current = data.get("current", {})
        city = data.get("city", "Unknown location")

        temp = current.get("temperature_2m", "N/A")
        wind_speed = current.get("wind_speed_10m", "N/A")
        weather_code = current.get("weather_code", 0)

        weather_desc = self._get_weather_description(weather_code)

        # Format time
        time_str = current.get("time", "")
        if time_str:
            try:
                dt = parser.isoparse(time_str)
                time_str = dt.strftime("%I:%M %p")
            except:
                pass

        return (
            f"Current weather in {city}:\n"
            f"• Temperature: {temp}°C\n"
            f"• Wind Speed: {wind_speed} km/h\n"
            f"• Conditions: {weather_desc}\n"
            f"• Last updated: {time_str}"
        )

    def format_today_forecast(self, weather_data: Dict) -> str:
        """Get forecast for the rest of today"""
        if not weather_data["success"]:
            return "No forecast data available."

        data = weather_data["data"]
        hourly = data.get("hourly", {})

        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        weather_codes = hourly.get("weather_code", [])

        now = datetime.utcnow()
        today_str = now.strftime("%Y-%m-%d")

        today_data = []
        for i, time_str in enumerate(times):
            if time_str.startswith(today_str):
                try:
                    hour = parser.isoparse(time_str).hour
                    if hour >= now.hour:
                        today_data.append({
                            "hour": hour,
                            "temp": temps[i] if i < len(temps) else "N/A",
                            "weather": weather_codes[i] if i < len(weather_codes) else 0
                        })
                except:
                    continue

        if not today_data:
            return "No forecast data for today."

        forecast_lines = ["Rest of today's forecast:"]
        for entry in today_data[:4]:  # Next 4 hours
            hour_str = f"{entry['hour']}:00"
            weather_desc = self._get_weather_description(entry['weather'])
            forecast_lines.append(f"  {hour_str}: {entry['temp']}°C, {weather_desc}")

        return "\n".join(forecast_lines)

    def get_recommendations(self, weather_data: Dict) -> str:
        """Generate clothing recommendations"""
        if not weather_data["success"]:
            return ""

        data = weather_data["data"]
        current = data.get("current", {})
        temp = current.get("temperature_2m", 20)
        weather_code = current.get("weather_code", 0)

        recommendations = []

        # Temperature-based
        if temp < 0:
            recommendations.append("Wear a heavy winter coat, gloves, and a hat")
        elif temp < 10:
            recommendations.append("Wear a warm jacket or coat")
        elif temp < 20:
            recommendations.append("A light jacket or sweater would be comfortable")
        else:
            recommendations.append("Light clothing is recommended")

        # Weather condition-based
        if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            recommendations.append("Bring an umbrella or raincoat")
        elif weather_code in [71, 73, 75, 77, 85, 86]:
            recommendations.append("Wear waterproof boots")

        if recommendations:
            return "Recommendations:\n" + "\n".join([f"• {rec}" for rec in recommendations])
        return ""

    def _get_weather_description(self, code: int) -> str:
        """Convert WMO weather code to description"""
        weather_codes = {
            0: "Clear sky ☀️",
            1: "Mainly clear 🌤️",
            2: "Partly cloudy ⛅",
            3: "Overcast ☁️",
            45: "Foggy 🌫️",
            48: "Rime fog 🌫️",
            51: "Light drizzle 🌦️",
            53: "Moderate drizzle 🌦️",
            55: "Dense drizzle 🌦️",
            61: "Slight rain 🌧️",
            63: "Moderate rain 🌧️",
            65: "Heavy rain 🌧️",
            71: "Slight snow fall ❄️",
            73: "Moderate snow fall ❄️",
            75: "Heavy snow fall ❄️",
            80: "Slight rain showers 🌦️",
            81: "Moderate rain showers 🌦️",
            82: "Violent rain showers 🌧️💨",
            85: "Slight snow showers ❄️",
            86: "Heavy snow showers ❄️",
            95: "Thunderstorm ⛈️",
            96: "Thunderstorm with hail ⛈️",
            99: "Thunderstorm with heavy hail ⛈️"
        }
        return weather_codes.get(code, "Unknown conditions")


# Singleton instance
weather_service = WeatherServiceDeep()
