"""
AI-Powered Ecommerce Chatbot - FastAPI Backend
Full-stack demo with Airtable, ChromaDB RAG, and LLM integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from routers import chat, products
from services.rag_service import rag_service
from services.airtable_service import airtable_service
from config import settings
from services.data_service import get_data_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    logger.info("🚀 Starting AI Ecommerce Chatbot Backend...")
    
    # Initialize RAG vector store with product/FAQ data
    await rag_service.initialize()
    logger.info("✅ RAG vector store initialized")
    
    # Initialize SQLite if selected
    if settings.data_source.lower() == "sqlite":
        from services.sqlite_service import sqlite_service
        await sqlite_service.initialize()
    
    # Pre-fetch and cache product catalog (for Airtable)
    from services.data_service import get_data_service
    data_service = get_data_service()
    if settings.data_source.lower() == "airtable":
        await data_service.warm_cache()
        logger.info("✅ Airtable cache warmed")
    
    yield
    
    logger.info("🛑 Shutting down...")


app = FastAPI(
    title="AI Ecommerce Chatbot API",
    description="Full-stack AI chatbot with Airtable + ChromaDB RAG + LLM",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow React dev server and production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(products.router, prefix="/api", tags=["Products"])


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "AI Ecommerce Chatbot",
        "version": "1.0.0",
        "endpoints": ["/api/chat", "/api/products", "/api/products/{id}"],
    }


@app.get("/health")
async def health():
    data_service = get_data_service()
    return {
        "status": "healthy", 
        "rag": rag_service.is_ready, 
        "data_source": settings.data_source,
        "is_configured": data_service.is_configured
    }