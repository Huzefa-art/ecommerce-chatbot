"""
Configuration management - all secrets and settings via environment variables.
Supports multiple client configurations (swap Airtable base per client).
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    # ── OpenAI ──────────────────────────────────────────────────────────────
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL"
    )

    # ── Airtable (per-client overrideable) ──────────────────────────────────
    airtable_api_key: str = Field(default="", env="AIRTABLE_API_KEY")
    airtable_base_id: str = Field(default="", env="AIRTABLE_BASE_ID")
    airtable_products_table: str = Field(
        default="Products", env="AIRTABLE_PRODUCTS_TABLE"
    )
    airtable_orders_table: str = Field(
        default="Orders", env="AIRTABLE_ORDERS_TABLE"
    )
    airtable_faq_table: str = Field(
        default="FAQs", env="AIRTABLE_FAQ_TABLE"
    )

    # ── ChromaDB ────────────────────────────────────────────────────────────
    chroma_persist_dir: str = Field(
        default="./chroma_db", env="CHROMA_PERSIST_DIR"
    )
    chroma_collection_name: str = Field(
        default="ecommerce_rag", env="CHROMA_COLLECTION_NAME"
    )

    # ── App ─────────────────────────────────────────────────────────────────
    demo_mode: bool = Field(
        default=True, env="DEMO_MODE",
        description="Use bundled demo data when Airtable is not configured"
    )
    max_products_per_query: int = Field(default=6, env="MAX_PRODUCTS_PER_QUERY")
    max_rag_results: int = Field(default=4, env="MAX_RAG_RESULTS")
    cache_ttl_seconds: int = Field(default=300, env="CACHE_TTL_SECONDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
