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
