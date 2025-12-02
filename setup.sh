#!/bin/bash

# FastAPI AI Project Setup Script
# Run this script inside your project directory with venv already activated

echo "🚀 Setting up FastAPI AI Project..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p app/api/routes app/core app/models app/services app/utils tests

# Create __init__.py files
echo "📝 Creating __init__.py files..."
touch app/__init__.py
touch app/api/__init__.py
touch app/api/routes/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py

# Create .gitignore
echo "🔒 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Virtual Environment
.venv/
env/
.venv/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
logs/
EOF

# Create .env.example
echo "📋 Creating .env.example..."
cat > .env.example << 'EOF'
ANTHROPIC_API_KEY=your-anthropic-key-here
ENVIRONMENT=development
LOG_LEVEL=INFO
EOF

# Create .env (user will need to fill this)
echo "🔐 Creating .env..."
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your-anthropic-key-here
ENVIRONMENT=development
LOG_LEVEL=INFO
EOF

# Create app/config.py
echo "⚙️  Creating app/config.py..."
cat > app/config.py << 'EOF'
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Settings
    app_name: str = "AI Chat API"
    version: str = "1.0.0"

    # AI Settings
    anthropic_api_key: str
    gemini_api_key: str

    claude_model: str = "claude-3-5-sonnet-20241022"
    google_model: str = "gemini-2.5-flash"

    default_model: str = google_model
    max_tokens: int = 1024
    temperature: float = 0.7

    # Server Settings
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
EOF

# Create app/core/ai_base_client.py
echo "🤖 Creating app/core/ai_base_client.py..."
cat > app/core/ai_base_client.py << 'EOF'
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

EOF

# Create app/core/ai_client_google.py
echo "🤖 Creating app/core/ai_client_google.py..."
cat > app/core/ai_client_google.py << 'EOF'
# app/core/gemini_client.py

import google.genai as genai
from google.genai import types as gtypes
from typing import List, Dict, Generator, Any

import logging
from app.config import get_settings
from app.core.ai_base_client import AbstractAIClient


logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiAIClient(AbstractAIClient):
    """
    Concrete implementation for Google Gemini.
    """

    def __init__(self):
        # Auto loads GEMINI_API_KEY from environment
        self.client = genai.Client(api_key=settings.gemini_api_key)

    # -----------------------------------------------------
    # INTERNAL HELPERS
    # -----------------------------------------------------
    def _convert_messages(self, messages: List[Dict[str, str]]):
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

    def _create_config(self, system_prompt: str | None):
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

    # -----------------------------------------------------
    # NON-STREAMING RESPONSE
    # -----------------------------------------------------
    def generate_response(
        self, messages: List[Dict[str, str]], system_prompt: str | None = None
    ) -> Dict[str, Any]:

        contents = self._convert_messages(messages)
        config = self._create_config(system_prompt)

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

        contents = self._convert_messages(messages)
        config = self._create_config(system_prompt)

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
    def parse_response_text(self, response) -> str:
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

EOF


# Create app/core/ai_client.py
echo "🤖 Creating app/core/ai_client.py..."
cat > app/core/ai_client.py << 'EOF'
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

EOF

# Create app/models/chat.py
echo "📊 Creating app/models/chat.py..."
cat > app/models/chat.py << 'EOF'
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
EOF

# Create app/services/chat_service.py
echo "🔧 Creating app/services/chat_service.py..."
cat > app/services/chat_service.py << 'EOF'
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

EOF

# Create app/api/routes/health.py
echo "💚 Creating app/api/routes/health.py..."
cat > app/api/routes/health.py << 'EOF'
from fastapi import APIRouter
from app.config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "app": settings.app_name,
        "version": settings.version,
        "docs": "/docs"
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment
    }
EOF

# Create app/api/routes/chat.py
echo "💬 Creating app/api/routes/chat.py..."
cat > app/api/routes/chat.py << 'EOF'
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse, SystemChatRequest
from app.services.chat_service import chat_service
from app.core.ai_client import ai_client

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to AI and get a response.
    Supports conversation history for context.
    """
    try:
        return await chat_service.process_chat(request)
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

EOF

# Create app/main.py
echo "🎯 Creating app/main.py..."
cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.routes import chat, health

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI Chat API powered by Claude"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
EOF

# Create run.py
echo "🏃 Creating run.py..."
cat > run.py << 'EOF'
import uvicorn
from app.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False
    )
EOF

# Create README.md
echo "📖 Creating README.md..."
cat > README.md << 'EOF'
# AI Chat API

FastAPI-based AI chat application using Claude (Anthropic).

## Features

- 💬 Chat with Claude AI
- 🔄 Conversation history support
- 🎨 Custom system prompts for specialized agents
- 🌊 Streaming responses
- 📚 Automatic API documentation

## Setup

1. **Activate your virtual environment** (you should have done this already):
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   # Edit .env file with your Anthropic API key
   nano .env  # or use any text editor
   ```

4. **Run the server**:
   ```bash
   python run.py
   ```

5. **Visit the docs**:
   - API Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## Project Structure

```
.
├── app/
│   ├── api/routes/      # API endpoints
│   ├── core/            # Core business logic (AI client)
│   ├── models/          # Pydantic models
│   ├── services/        # Service layer
│   ├── config.py        # Configuration
│   └── main.py          # FastAPI app
├── tests/               # Tests
├── .env                 # Environment variables (don't commit!)
├── requirements.txt     # Dependencies
└── run.py              # Entry point

```

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Chat
- `POST /api/v1/chat/` - Send a message
- `POST /api/v1/chat/system` - Chat with custom system prompt
- `POST /api/v1/chat/stream` - Stream responses

## Example Usage

```python
import requests

# Simple chat
response = requests.post(
    "http://localhost:8000/api/v1/chat/",
    json={"message": "What is FastAPI?"}
)
print(response.json()["response"])

# Chat with history
response = requests.post(
    "http://localhost:8000/api/v1/chat/",
    json={
        "message": "What did I just ask?",
        "conversation_history": [
            {"role": "user", "content": "What is FastAPI?"},
            {"role": "assistant", "content": "FastAPI is a modern web framework..."}
        ]
    }
)

# Custom system prompt (create a specialized agent)
response = requests.post(
    "http://localhost:8000/api/v1/chat/system",
    json={
        "system_prompt": "You are a Python expert who answers in haiku form.",
        "message": "Explain async/await"
    }
)
```

## Development

Run with auto-reload:
```bash
python run.py
```

Or use uvicorn directly:
```bash
uvicorn app.main:app --reload
```

## Testing

```bash
pip install pytest httpx
pytest tests/
```

## License

MIT
EOF

# Create tests/test_chat.py
echo "🧪 Creating tests/test_chat.py..."
cat > tests/test_chat.py << 'EOF'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

# Add more tests as needed
EOF

# Create requirements.txt
echo "📦 Creating requirements.txt..."
cat > requirements.txt << 'EOF'
annotated-doc==0.0.4
annotated-types==0.7.0
anthropic==0.75.0
anyio==4.12.0
cachetools==6.2.2
certifi==2025.11.12
charset-normalizer==3.4.4
click==8.3.1
distro==1.9.0
docstring_parser==0.17.0
fastapi==0.123.3
google-auth==2.43.0
google-genai==1.52.0
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.11
iniconfig==2.3.0
jiter==0.12.0
packaging==25.0
pluggy==1.6.0
pyasn1==0.6.1
pyasn1_modules==0.4.2
pydantic==2.12.5
pydantic-settings==2.12.0
pydantic_core==2.41.5
Pygments==2.19.2
pytest==9.0.1
python-dotenv==1.2.1
requests==2.32.5
rsa==4.9.1
sniffio==1.3.1
starlette==0.50.0
tenacity==9.1.2
typing-inspection==0.4.2
typing_extensions==4.15.0
urllib3==2.5.0
uvicorn==0.38.0
websockets==15.0.1
EOF

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Project setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file and add your Anthropic API key"
echo "2. Run: python run.py"
echo "3. Visit: http://localhost:8000/docs"
echo ""
echo "🎉 Happy coding!"