from typing import Dict, List
from app.models.chat import ChatRequest, ChatResponse, Message, SystemChatRequest
from app.core.ai_client import ai_client


class ChatService:
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return a response"""
        messages = self._build_messages(request.conversation_history, request.message)

        # ai_client.generate_response now returns a standardized dict: {"text": str, "model": str, "raw": object}
        result = ai_client.generate_response(messages)

        return ChatResponse(
            # FIX 1: Get the clean text from the standardized result dict
            response=result["text"],
            # FIX 2: Get the model name from the standardized result dict
            model=result["model"],
        )

    async def process_system_chat(self, request: SystemChatRequest) -> ChatResponse:
        """Process a chat request with a system prompt"""
        messages = self._build_messages(request.conversation_history, request.message)

        result = ai_client.generate_response(
            messages=messages, system_prompt=request.system_prompt
        )

        return ChatResponse(
            # FIX 3: Get the clean text from the standardized result dict
            response=result["text"],
            # FIX 4: Get the model name from the standardized result dict
            model=result["model"],
        )

    def _build_messages(
        self, history: List[Message], new_message: str
    ) -> List[Dict[str, str]]:
        """Build messages list from history and new message"""
        messages = []

        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": new_message})

        return messages


# Singleton instance
chat_service = ChatService()
