"""
Chat Router — POST /api/chat
Orchestrates: Intent → Airtable structured query → RAG semantic search → LLM response
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
import logging

from services.llm_service import detect_intent, extract_filters, generate_llm_response
from services.airtable_service import airtable_service
from services.rag_service import rag_service
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    # Optional per-client Airtable override
    airtable_api_key: Optional[str] = None
    airtable_base_id: Optional[str] = None


class ProductCard(BaseModel):
    id: str
    name: str
    price: float
    category: str
    color: Optional[str] = None
    rating: Optional[float] = None
    image_url: Optional[str] = None
    description: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    intent: str
    products: list[ProductCard]
    order_info: Optional[dict] = None
    rag_sources: list[str]
    session_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main chat pipeline:
    1. Detect intent
    2. Extract filters
    3. Structured Airtable query (for product_search, order_tracking)
    4. Semantic RAG search (for recommendations, FAQ, ambiguous queries)
    5. Combine results → LLM → final response
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    msg = req.message.strip()
    logger.info(f"Chat [{req.session_id}]: {msg[:100]}")

    # ── 1. Intent detection ───────────────────────────────────────────────
    intent = detect_intent(msg)
    filters = extract_filters(msg)
    logger.info(f"Intent: {intent} | Filters: {filters}")

    products = []
    order_info = None
    rag_hits = []

    # ── 2. Order tracking ─────────────────────────────────────────────────
    if intent == "order_tracking":
        order_id = filters.get("order_id")
        if order_id:
            order_info = await airtable_service.get_order(order_id)

    # ── 3. Structured product search ──────────────────────────────────────
    elif intent == "product_search":
        products = await airtable_service.search_products_structured(
            category=filters.get("category"),
            max_price=filters.get("max_price"),
            min_price=filters.get("min_price"),
            color=filters.get("color"),
            keywords=filters.get("keywords"),
            sort_by=filters.get("sort_by"),
            limit=settings.max_products_per_query,
        )
        # Supplement with semantic search if structured yields < 3 results
        if len(products) < 3:
            rag_hits = await rag_service.semantic_search(
                msg, doc_types=["product"], n_results=6
            )
            if rag_hits:
                all_products = await airtable_service.get_all_products()
                semantic_products = rag_service.enrich_products_with_rag(rag_hits, all_products)
                # Merge, dedup
                existing_ids = {p["id"] for p in products}
                products += [p for p in semantic_products if p["id"] not in existing_ids]

    # ── 4. Semantic search (recommendation / ambiguous) ───────────────────
    elif intent in ("recommendation", "general"):
        # RAG for products first
        rag_hits = await rag_service.semantic_search(
            msg, doc_types=["product"], n_results=8
        )
        if rag_hits:
            all_products = await airtable_service.get_all_products()
            products = rag_service.enrich_products_with_rag(rag_hits, all_products)
        # Apply any explicit filters found alongside natural query
        if filters and products:
            if filters.get("max_price"):
                products = [p for p in products if p.get("price", 0) <= filters["max_price"]]
            if filters.get("category"):
                cat = filters["category"].lower()
                products = [p for p in products if cat in p.get("category", "").lower()]
        products = products[:settings.max_products_per_query]

    # ── 5. FAQ / Policy intent ────────────────────────────────────────────
    elif intent == "faq":
        rag_hits = await rag_service.semantic_search(
            msg, doc_types=["faq", "policy"], n_results=4
        )

    # ── 6. Fallback: do both ──────────────────────────────────────────────
    else:
        rag_hits = await rag_service.semantic_search(msg, n_results=6)
        all_products = await airtable_service.get_all_products()
        products = rag_service.enrich_products_with_rag(rag_hits, all_products)
        products = products[:4]

    # ── 7. LLM response generation ────────────────────────────────────────
    response_text = await generate_llm_response(
        user_message=msg,
        intent=intent,
        products=products,
        rag_context=rag_hits,
        order_info=order_info,
    )

    # ── 8. Build product cards ────────────────────────────────────────────
    product_cards = [
        ProductCard(
            id=p.get("id", ""),
            name=p.get("name", ""),
            price=float(p.get("price", 0)),
            category=p.get("category", ""),
            color=p.get("color"),
            rating=p.get("rating"),
            image_url=p.get("image_url"),
            description=p.get("description", "")[:150] + "..." if len(p.get("description", "")) > 150 else p.get("description"),
        )
        for p in products
    ]

    # ── 9. Collect RAG source labels ──────────────────────────────────────
    rag_sources = []
    for hit in rag_hits:
        meta = hit.get("metadata", {})
        if meta.get("type") == "faq":
            rag_sources.append(f"FAQ: {meta.get('question', '')[:60]}")
        elif meta.get("type") == "policy":
            rag_sources.append(f"Policy: {meta.get('title', '')}")
        elif meta.get("type") == "product":
            rag_sources.append(f"Product: {meta.get('name', '')}")

    return ChatResponse(
        message=response_text,
        intent=intent,
        products=product_cards,
        order_info=order_info,
        rag_sources=list(set(rag_sources))[:5],
        session_id=req.session_id,
    )
