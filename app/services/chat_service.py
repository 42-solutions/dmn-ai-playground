from app.models.chat import ChatRequest, ChatResponse, SystemChatRequest
from app.core.ai_client import ai_client

class ChatService:
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return a response"""
        messages = self._build_messages(request.conversation_history, request.message)
        
        response = ai_client.generate_response(messages)
        
        return ChatResponse(
            response=response.content[0].text,
            model=response.model
        )
    
    async def process_system_chat(self, request: SystemChatRequest) -> ChatResponse:
        """Process a chat request with a system prompt"""
        messages = self._build_messages(request.conversation_history, request.message)
        
        response = ai_client.generate_response(
            messages=messages,
            system_prompt=request.system_prompt
        )
        
        return ChatResponse(
            response=response.content[0].text,
            model=response.model
        )
    
    def _build_messages(self, history, new_message):
        """Build messages list from history and new message"""
        messages = []
        
        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        messages.append({
            "role": "user",
            "content": new_message
        })
        
        return messages

# Singleton instance
chat_service = ChatService()
