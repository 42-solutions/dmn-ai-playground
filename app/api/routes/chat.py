from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse
from app.core.ai_client import ai_client
from app.services.chat_service_weather_chatgpt import process_chat

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to AI and get a response.
    Supports conversation history for context.
    """
    try:
        return await process_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream responses from the selected AI model in real-time.
    """

    async def generate():
        try:
            messages = []
            for msg in request.conversation_history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": request.message})

            # FIX: Call the stream_response method which now returns a generator
            # We iterate directly over the generator, which yields text chunks (str)
            stream_generator = ai_client.stream_response(messages)

            # The async generator wrapper is required for StreamingResponse
            for text_chunk in stream_generator:
                yield text_chunk.encode(
                    "utf-8"
                )  # Yield bytes as required by StreamingResponse

        except Exception as e:
            # Handle error during stream generation
            yield f"Error: {str(e)}".encode("utf-8")

    return StreamingResponse(generate(), media_type="text/plain")
