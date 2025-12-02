# app/core/ai_client.py - IMPROVED VERSION
from app.config import get_settings
from app.core.ai_client_anthropic import anthropic_client
from app.core.ai_client_google import gemini_client
from app.core.ai_base_client import AbstractAIClient
from typing import Optional

settings = get_settings()


class AIClientManager:
    """Manages AI client instances and provides dynamic switching"""

    _clients = {
        "claude": anthropic_client,
        "gemini": gemini_client,
    }

    def get_client(self, model_name: Optional[str] = None) -> AbstractAIClient:
        """Get client for specific model or default"""
        if model_name is None:
            model_name = settings.default_model

        model_lower = model_name.lower()

        for prefix, client in self._clients.items():
            if model_lower.startswith(prefix):
                return client

        raise ValueError(
            f"Unsupported model: {model_name}. Available: {list(self._clients.keys())}"
        )

    @property
    def default_client(self) -> AbstractAIClient:
        """Get the default client based on settings"""
        return self.get_client()


# Create singleton manager
ai_client_manager = AIClientManager()

# For backward compatibility
ai_client = ai_client_manager.default_client
