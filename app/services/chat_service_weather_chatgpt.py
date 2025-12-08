# app/services/chat_service.py
import json
import re
from typing import List, Dict
from app.models.chat import ChatRequest, ChatResponse
from app.core.ai_client import ai_client
from app.core.tools.weather_tool_ghatgpt import (
    get_weather_by_place,
    get_weather_by_coords,
)

SYSTEM_PROMPT = """
You are WeatherAssistant. When the user asks for real-time or forecast weather,
you MUST return a JSON object with the key "tool_call" describing the tool to run,
in the format:
{
  "tool_call": {
    "name": "<tool_name>",
    "arguments": { ... }
  }
}
Only produce that JSON if you intend the system to fetch live weather.
If you do not need live data, answer normally.
Available tools:
- get_weather_by_place: args { "place": "Berlin" }
- get_weather_by_coords: args { "latitude": 52.52, "longitude": 13.41 }
If you want the backend to fetch weather, return ONLY the JSON described above, and nothing else.
"""


def extract_json(text: str) -> str:
    """
    Removes code fences like ```json ... ``` or ``` ... ```.
    Returns inner JSON string.
    """
    # Remove ```json ... ``` or ``` ... ```
    fenced = re.match(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    return text.strip()


async def process_chat(request: ChatRequest) -> ChatResponse:
    # Build messages
    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    # system
    # conversation history (if any)
    for m in request.conversation_history or []:
        messages.append({"role": m.role, "content": m.content})
    # user message
    messages.append({"role": "user", "content": request.message})

    # 1) Ask model whether it wants to call tool (or answer directly)
    model_resp = ai_client.generate_response(messages=messages)
    # parse provider-specific response text
    text = ai_client.parse_response_text(
        model_resp["raw"]
        if isinstance(model_resp, dict) and "raw" in model_resp
        else model_resp
    )

    # 2) Try to parse the model output as JSON tool_call
    try:
        clean = extract_json(text)
        payload = json.loads(clean)
    except Exception:
        payload = None

    if payload and "tool_call" in payload:
        tool = payload["tool_call"]
        name = tool.get("name")
        args = tool.get("arguments", {})

        # Execute the tool
        if name == "get_weather_by_place" and "place" in args:
            tool_result = await get_weather_by_place(args["place"])
        elif (
            name == "get_weather_by_coords"
            and "latitude" in args
            and "longitude" in args
        ):
            tool_result = await get_weather_by_coords(
                args["latitude"], args["longitude"]
            )
        else:
            tool_result = {"error": f"Unknown tool or missing args: {name}"}

        # 3) Send tool result back to model as tool message
        messages.append(
            {
                "role": "tool",
                "content": json.dumps({"name": name, "result": tool_result}),
            }
        )

        # 4) Ask model to produce final answer
        final_resp = ai_client.generate_response(messages=messages)
        final_text = ai_client.parse_response_text(
            final_resp["raw"]
            if isinstance(final_resp, dict) and "raw" in final_resp
            else final_resp
        )

        return ChatResponse(
            response=final_text, model=getattr(final_resp, "model", "unknown")
        )
    else:
        # Model answered directly
        return ChatResponse(
            response=text, model=getattr(model_resp, "model", "unknown")
        )
