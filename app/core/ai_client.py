import anthropic
from app.config import get_settings

settings = get_settings()

class AIClient:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key
        )
    
    def generate_response(self, messages, system_prompt=None):
        """Generate a response from Claude"""
        kwargs = {
            "model": settings.default_model,
            "max_tokens": settings.max_tokens,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
            
        return self.client.messages.create(**kwargs)
    
    def stream_response(self, messages, system_prompt=None):
        """Stream a response from Claude"""
        kwargs = {
            "model": settings.default_model,
            "max_tokens": settings.max_tokens,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
            
        return self.client.messages.stream(**kwargs)

# Singleton instance
ai_client = AIClient()
