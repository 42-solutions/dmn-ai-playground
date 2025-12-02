from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    response: str
    model: str

class SystemChatRequest(BaseModel):
    system_prompt: str
    message: str
    conversation_history: Optional[List[Message]] = []
