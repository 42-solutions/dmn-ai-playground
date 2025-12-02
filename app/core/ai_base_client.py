# app/core/ai_client_base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional


class AbstractAIClient(ABC):
    """
    Abstract Base Class defining the contract for all AI client implementations.
    Every concrete client (Anthropic, Gemini) must implement these methods.
    """

    @abstractmethod
    def generate_response(
        self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Returns: {"text": str, "model": str, "raw": Any}
        """
        pass

    @abstractmethod
    def stream_response(
        self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:  # More precise type
        pass

    @abstractmethod
    def parse_response_text(self, response: Dict[str, Any]) -> str:
        """
        Extracts the final response text from the raw SDK response object.
        This is where the provider-specific logic (like .content[0].text) belongs.
        """
        pass
