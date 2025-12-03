# app/core/weather_response_chatgpt.py
from typing import List, Dict, Any


class WeatherResponseChatGPT:
    def __init__(self, raw: Dict[str, Any]):
        self.raw = raw

    def current(self) -> Dict[str, Any]:
        c = self.raw.get("current", {})
        return {
            "time": c.get("time"),
            "temperature_c": c.get("temperature_2m"),
            "wind_speed_kmh": c.get("wind_speed_10m"),
        }

    def hourly_zipped(self) -> List[Dict[str, Any]]:
        hourly = self.raw.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        hums = hourly.get("relative_humidity_2m", [])
        winds = hourly.get("wind_speed_10m", [])
        out = []
        for i, t in enumerate(times):
            out.append(
                {
                    "time": t,
                    "temperature_c": temps[i] if i < len(temps) else None,
                    "relative_humidity": hums[i] if i < len(hums) else None,
                    "wind_speed_kmh": winds[i] if i < len(winds) else None,
                }
            )
        return out

    def today_summary(self) -> Dict[str, Any]:
        # naive: first 24 entries correspond to today starting from the first timestamp
        hourly = self.hourly_zipped()[:24]
        temps = [h["temperature_c"] for h in hourly if h["temperature_c"] is not None]
        if not temps:
            return {}
        return {
            "min_temp_c": min(temps),
            "max_temp_c": max(temps),
            "avg_temp_c": sum(temps) / len(temps),
        }
