# app/core/gemini_client.py

import google.genai as genai
from google.genai import types as gtypes
from typing import List, Dict, Generator, Any

import logging

from google.genai.types import GenerateContentResponse

from app.config import get_settings
from app.core.ai_base_client import AbstractAIClient

logger = logging.getLogger(__name__)
settings = get_settings()


def _convert_messages(messages: List[Dict[str, str]]):
    """
    Converts our internal message format:
    {"role": "user" | "assistant", "content": "..."}
    into Gemini's list of Content objects.
    """
    contents = []

    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"

        contents.append(
            gtypes.Content(
                role=role,
                parts=[
                    # Previous fix: Ensure 'text' is passed as a keyword argument
                    gtypes.Part.from_text(text=msg["content"])
                ],
            )
        )

    return contents


def _create_config(system_prompt: str | None):
    """
    Build Gemini's config object (temperature, tokens, system prompt).
    """
    config = gtypes.GenerateContentConfig(
        max_output_tokens=settings.max_tokens,
        temperature=settings.temperature,
    )

    if system_prompt:
        config.system_instruction = system_prompt

    return config


class GeminiAIClient(AbstractAIClient):
    """
    Concrete implementation for Google Gemini.
    """

    def __init__(self):
        # Autoloads GEMINI_API_KEY from environment
        self.client = genai.Client(api_key=settings.gemini_api_key)

    # -----------------------------------------------------
    # NON-STREAMING RESPONSE
    # -----------------------------------------------------
    def generate_response(
            self, messages: List[Dict[str, str]], system_prompt: str | None = None
    ) -> Dict[str, Any]:

        contents = _convert_messages(messages)
        config = _create_config(system_prompt)

        response = self.client.models.generate_content(
            model=settings.google_model,
            contents=contents,
            config=config,
        )

        text = self.parse_response_text(response)

        # Retaining the fix for 'GenerateContentResponse' object has no attribute 'model'
        return {"text": text, "raw": response, "model": settings.google_model}

    # -----------------------------------------------------
    # STREAMING RESPONSE
    # -----------------------------------------------------
    def stream_response(
            self, messages: List[Dict[str, str]], system_prompt: str | None = None
    ) -> Generator[str, None, None]:

        contents = _convert_messages(messages)
        config = _create_config(system_prompt)

        stream = self.client.models.generate_content_stream(
            model=settings.google_model,
            contents=contents,
            config=config,
        )

        for chunk in stream:
            # chunks arrive as events containing parts
            if not chunk or not chunk.candidates:
                logger.debug("Empty chunk received")
                continue

            candidate = chunk.candidates[0]

            # FIX 1: Add a defensive check for candidate.content
            if not candidate.content or not candidate.content.parts:
                continue  # Skip this chunk if content is missing (e.g., safety block)

            part = candidate.content.parts[0]

            if part.text:
                yield part.text

    # -----------------------------------------------------
    # PARSING RAW RESPONSE
    # -----------------------------------------------------
    def parse_response_text(self, response: GenerateContentResponse) -> str:
        """
        Extracts the text from Gemini's response.
        The preferred way is using the top-level .text accessor on the response object.
        """
        # Use the simple .text accessor provided by the SDK
        if response.text:
            return response.text

        # Fallback to the deep candidates path with defensive checks
        try:
            candidate = response.candidates[0]

            # FIX 2: Add a defensive check for candidate.content
            if candidate.content and candidate.content.parts:
                return candidate.content.parts[0].text
        except (AttributeError, IndexError):
            # This handles cases where candidates list is empty or candidate is malformed
            return ""

        return ""


# Singleton instance
gemini_client = GeminiAIClient()
