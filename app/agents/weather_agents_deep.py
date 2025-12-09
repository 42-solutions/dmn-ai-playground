from typing import Dict, Any, List
from app.services.weather_service_deep import weather_service
from app.core.ai_client import ai_client
import logging

logger = logging.getLogger(__name__)

class WeatherAgentDeep:
    """
    Specialized agent for handling weather queries
    """

    SYSTEM_PROMPT = """You are WeatherGPT, a friendly weather assistant.

YOUR ROLE:
1. Answer questions about weather in various cities
2. Provide current conditions, forecasts, and recommendations
3. Interpret weather data in human-friendly language
4. Give practical advice based on weather conditions

AVAILABLE CITIES:
- Berlin, London, New York, Tokyo, Paris
- Sydney, Mumbai, Beijing, San Francisco, Singapore
- Dubai, Moscow

RESPONSE FORMAT:
- Start with a greeting or acknowledgment
- Present weather information clearly
- Use emojis when appropriate
- Include recommendations if relevant
- Keep it conversational and helpful

If you don't know a city's weather, say so and suggest an available city."""

    async def handle_weather_query(self, user_message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Handle weather-related queries using AI
        """
        try:
            # Build messages for AI
            messages = []

            if conversation_history:
                messages.extend(conversation_history)

            messages.append({
                "role": "user",
                "content": user_message
            })

            # Get AI response
            response = ai_client.generate_response(
                messages=messages,
                system_prompt=self.SYSTEM_PROMPT
            )

            # Extract city from response (simple implementation)
            city = self._extract_city(user_message)

            if city:
                # Get weather data
                weather_result = await weather_service.get_weather_by_city(city)

                if weather_result["success"]:
                    # Format the data
                    current_weather = weather_service.format_current_weather(weather_result)
                    today_forecast = weather_service.format_today_forecast(weather_result)
                    recommendations = weather_service.get_recommendations(weather_result)

                    # Combine all information
                    full_report = f"{current_weather}\n\n{today_forecast}"
                    if recommendations:
                        full_report += f"\n\n{recommendations}"

                    # Let AI incorporate the data into a natural response
                    follow_up_messages = messages.copy()
                    follow_up_messages.append({
                        "role": "assistant",
                        "content": f"Here's the weather data I found:\n\n{full_report}"
                    })
                    follow_up_messages.append({
                        "role": "user",
                        "content": "Please incorporate this weather data into a helpful, conversational response to my original question."
                    })

                    final_response = ai_client.generate_response(
                        messages=follow_up_messages,
                        system_prompt=self.SYSTEM_PROMPT
                    )

                    return {
                        "success": True,
                        "type": "weather_report",
                        "response": final_response["text"],
                        "city": city,
                        "raw_data": weather_result["data"]
                    }
                else:
                    return {
                        "success": False,
                        "type": "error",
                        "response": f"Sorry, I couldn't fetch weather data for {city}. Please try another city.",
                        "error": weather_result.get("error")
                    }
            else:
                # No city detected, just return AI response
                return {
                    "success": True,
                    "type": "general_chat",
                    "response": response["text"]
                }

        except Exception as e:
            logger.error(f"Weather agent error: {e}")
            return {
                "success": False,
                "type": "error",
                "response": f"An error occurred: {str(e)}"
            }

    def _extract_city(self, text: str) -> str:
        """
        Simple city extraction from text
        """
        text_lower = text.lower()

        city_mapping = {
            "berlin": "berlin",
            "london": "london",
            "new york": "new york",
            "nyc": "new york",
            "tokyo": "tokyo",
            "paris": "paris",
            "sydney": "sydney",
            "mumbai": "mumbai",
            "beijing": "beijing",
            "san francisco": "san francisco",
            "sf": "san francisco",
            "singapore": "singapore",
            "dubai": "dubai",
            "moscow": "moscow"
        }

        for keyword, city in city_mapping.items():
            if keyword in text_lower:
                return city

        return None

# Singleton instance
weather_agent = WeatherAgentDeep()