from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import redis.asyncio as redis
from langchain.globals import set_llm_cache

from app.config import settings
from app.database import engine, Base, get_db, init_db
from app.api import chat, venues, admin, users
from app.llm.cache import CustomSemanticCache
from app.rag.chroma_manager import ChromaManager


Base.metadata.create_all(bind=engine)

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    #print("Initializing database...")
    init_db()

    app.state.redis = await redis.from_url(settings.REDIS_URL)
    app.state.chroma_manager = ChromaManager()
    app.state.llm_cache = CustomSemanticCache()
    set_llm_cache(app.state.llm_cache)
    
    yield
    
    await app.state.redis.close()

app = FastAPI(
    title="Venue Recommendation API",
    description="Personalized entertainment venue recommendations",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(venues.router, prefix="/api/venues", tags=["venues"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Venue Recommendation API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/docs")
async def get_docs():
    """API documentation endpoint"""
    return {
        "message": "API Documentation",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "auth": "/api/auth",
            "chat": "/api/chat",
            "venues": "/api/venues",
            "admin": "/api/admin",
            "users": "/api/users"
        }
    }