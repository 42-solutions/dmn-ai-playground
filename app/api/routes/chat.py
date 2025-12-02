from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse, SystemChatRequest
from app.services.chat_service import chat_service
from app.core.ai_client import ai_client

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to Claude and get a response.
    Supports conversation history for context.
    """
    try:
        return await chat_service.process_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/system", response_model=ChatResponse)
async def chat_with_system(request: SystemChatRequest):
    """
    Chat with a custom system prompt.
    Useful for creating specialized agents.
    """
    try:
        return await chat_service.process_system_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream responses from Claude in real-time.
    """
    async def generate():
        try:
            messages = []
            for msg in request.conversation_history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": request.message})
            
            with ai_client.stream_response(messages) as stream:
                for text in stream.text_stream:
                    yield text
        
        except Exception as e:
            yield f"Error: {str(e)}"
    
    return StreamingResponse(generate(), media_type="text/plain")
