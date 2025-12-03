from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service_weather_chatgpt import chat_service

router = APIRouter()


@router.post("/gpt", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to AI and get a response.
    Supports conversation history for context.
    """
    try:
        return await chat_service.process_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
