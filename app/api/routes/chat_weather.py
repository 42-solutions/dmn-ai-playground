from typing import Optional

from fastapi import APIRouter, HTTPException

from app.agents.weather_agents_deep import weather_agent
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service_weather_chatgpt import process_chat

router = APIRouter()


@router.post("/gpt", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to AI and get a response.
    Supports conversation history for context.
    """
    try:
        return await process_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/deep", response_model=dict)
async def ask_weather(request: ChatRequest):
    """
    Ask about weather in natural language

    Example requests:
    - {"message": "What's the weather in Berlin?"}
    - {"message": "Should I bring an umbrella in London?"}
    - {"message": "How's the weather in Tokyo today?"}
    """
    try:
        result = await weather_agent.handle_weather_query(
            user_message=request.message,
            conversation_history=request.conversation_history
        )

        return {
            "success": result["success"],
            "type": result["type"],
            "response": result["response"],
            "city": result.get("city"),
            "model": "weather-agent"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
