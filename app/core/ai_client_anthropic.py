import anthropic
from app.config import get_settings
from app.core.ai_base_client import AbstractAIClient

settings = get_settings()

class AIClient(AbstractAIClient):
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
    
    def parse_response_text(self, response) -> str:
        """Extracts text from Anthropic Message object."""
        # This moves the hard-coded logic OUT of the ChatService
        return response.content[0].text

# Singleton instance
anthropic_client = AIClient()
