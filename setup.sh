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
venv/
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
    default_model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 1024
    
    # Server Settings
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
EOF

# Create app/core/ai_client.py
echo "🤖 Creating app/core/ai_client.py..."
cat > app/core/ai_client.py << 'EOF'
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
    Send a message to Claude and get a response.
    Supports conversation history for context.
    """
    try:
        return await chat_service.process_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/system", response_model=ChatResponse)
async def chat_with_system(request: SystemChatRequest):
    """
    Chat with a custom system prompt.
    Useful for creating specialized agents.
    """
    try:
        return await chat_service.process_system_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream responses from Claude in real-time.
    """
    async def generate():
        try:
            messages = []
            for msg in request.conversation_history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": request.message})
            
            with ai_client.stream_response(messages) as stream:
                for text in stream.text_stream:
                    yield text
        
        except Exception as e:
            yield f"Error: {str(e)}"
    
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