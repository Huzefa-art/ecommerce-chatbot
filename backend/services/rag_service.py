"""
RAG Service — ChromaDB + OpenAI Embeddings
- Stores product descriptions, FAQs, and policies as embeddings
- Semantic search for complex/natural language queries
- Falls back to keyword search when OpenAI is not configured
"""

import asyncio
import logging
import hashlib
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings
from demo_data import DEMO_PRODUCTS, DEMO_FAQS, DEMO_POLICIES

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self._client: Optional[chromadb.Client] = None
        self._collection = None
        self.is_ready = False

    def _get_chroma_client(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self):
        client = self._get_chroma_client()
        # Use OpenAI embeddings if available, else default (sentence-transformers)
        if settings.openai_api_key:
            from chromadb.utils import embedding_functions
            ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name=settings.openai_embedding_model,
            )
            collection = client.get_or_create_collection(
                name=settings.chroma_collection_name,
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"},
            )
        else:
            # Default: built-in chromadb embedding (no API key needed for demo)
            collection = client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return collection

    async def initialize(self):
        """Build vector index from demo data (or re-index if needed)."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._build_index)
            self.is_ready = True
        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")
            self.is_ready = False

    def _build_index(self):
        """Sync: build/refresh ChromaDB index."""
        collection = self._get_collection()
        self._collection = collection

        docs, metadatas, ids = [], [], []

        # Index products
        for p in DEMO_PRODUCTS:
            doc_id = f"product_{p['id']}"
            text = (
                f"{p['name']}. {p['description']} "
                f"Category: {p['category']}. Tags: {', '.join(p.get('tags', []))}. "
                f"Price: Rs. {p['price']}. Color: {p.get('color', '')}. "
                f"Rating: {p.get('rating', '')} stars."
            )
            docs.append(text)
            metadatas.append({
                "type": "product",
                "product_id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "price": float(p["price"]),
                "rating": float(p.get("rating", 0)),
                "color": p.get("color", ""),
            })
            ids.append(doc_id)

        # Index FAQs
        for faq in DEMO_FAQS:
            doc_id = f"faq_{faq['id']}"
            text = f"Q: {faq['question']} A: {faq['answer']}"
            docs.append(text)
            metadatas.append({
                "type": "faq",
                "faq_id": faq["id"],
                "question": faq["question"],
                "category": faq["category"],
            })
            ids.append(doc_id)

        # Index policies
        for pol in DEMO_POLICIES:
            doc_id = f"policy_{pol['id']}"
            text = f"{pol['title']}: {pol['content']}"
            docs.append(text)
            metadatas.append({
                "type": "policy",
                "policy_id": pol["id"],
                "title": pol["title"],
                "category": pol["category"],
            })
            ids.append(doc_id)

        # Upsert all (idempotent)
        try:
            collection.upsert(documents=docs, metadatas=metadatas, ids=ids)
            logger.info(f"✅ Indexed {len(docs)} documents in ChromaDB")
        except Exception as e:
            logger.error(f"ChromaDB upsert error: {e}")

    async def semantic_search(
        self,
        query: str,
        doc_types: Optional[list[str]] = None,
        n_results: int = None,
    ) -> list[dict]:
        """
        Semantic similarity search.
        doc_types: filter to ["product", "faq", "policy"] or any subset
        """
        if not self.is_ready or self._collection is None:
            logger.warning("RAG not ready, falling back to keyword search")
            return self._keyword_fallback(query, doc_types)

        n_results = n_results or settings.max_rag_results

        try:
            where = None
            if doc_types and len(doc_types) == 1:
                where = {"type": doc_types[0]}
            elif doc_types and len(doc_types) > 1:
                where = {"type": {"$in": doc_types}}

            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self._collection.query(
                    query_texts=[query],
                    n_results=min(n_results, 10),
                    where=where,
                    include=["documents", "metadatas", "distances"],
                )
            )

            hits = []
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                hits.append({
                    "text": doc,
                    "metadata": meta,
                    "relevance_score": round(1 - dist, 3),  # cosine: 1=identical
                })

            # Filter low-relevance results
            hits = [h for h in hits if h["relevance_score"] > 0.3]
            return hits

        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return self._keyword_fallback(query, doc_types)

    def _keyword_fallback(self, query: str, doc_types: Optional[list] = None) -> list[dict]:
        """Simple keyword search fallback when embeddings unavailable."""
        query_lower = query.lower()
        results = []

        all_docs = []
        for p in DEMO_PRODUCTS:
            text = f"{p['name']} {p['description']} {' '.join(p.get('tags', []))}"
            all_docs.append({"text": text, "metadata": {"type": "product", "product_id": p["id"], "name": p["name"]}})
        for faq in DEMO_FAQS:
            text = f"{faq['question']} {faq['answer']}"
            all_docs.append({"text": text, "metadata": {"type": "faq", "question": faq["question"]}})
        for pol in DEMO_POLICIES:
            text = f"{pol['title']} {pol['content']}"
            all_docs.append({"text": text, "metadata": {"type": "policy", "title": pol["title"]}})

        for doc in all_docs:
            if doc_types and doc["metadata"]["type"] not in doc_types:
                continue
            words = query_lower.split()
            score = sum(1 for w in words if w in doc["text"].lower()) / max(len(words), 1)
            if score > 0:
                results.append({**doc, "relevance_score": round(score, 3)})

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:settings.max_rag_results]

    def enrich_products_with_rag(
        self, rag_hits: list[dict], all_products: list[dict]
    ) -> list[dict]:
        """Extract product objects from RAG hits."""
        product_ids = [
            h["metadata"]["product_id"]
            for h in rag_hits
            if h["metadata"].get("type") == "product"
        ]
        products = [p for p in all_products if p["id"] in product_ids]
        return products


rag_service = RAGService()
