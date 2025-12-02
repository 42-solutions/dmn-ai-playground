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
