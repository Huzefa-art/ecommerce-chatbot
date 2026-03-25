"""
LLM Service & Intent Detection
- Detects user intent: product_search | recommendation | order_tracking | faq | general
- Extracts structured filters from natural language
- Generates final user-friendly response from combined structured + semantic results
- Works with OpenAI API (falls back to template responses without API key)
"""

import json
import logging
import re
from typing import Optional
import httpx
from config import settings

logger = logging.getLogger(__name__)


# ── Intent Classification ─────────────────────────────────────────────────────

INTENT_PATTERNS = {
    "order_tracking": [
        r"order\s*(status|track|where|id)",
        r"track\s*my\s*order",
        r"where\s*is\s*my",
        r"ORD-\d+",
        r"delivery\s*status",
        r"when\s*will\s*my\s*order",
        r"has\s*my\s*order\s*shipped",
    ],
    "product_search": [
        r"show\s*me",
        r"find\s*me",
        r"looking\s*for",
        r"search\s*for",
        r"under\s+(?:rs\.?\s*)?\d+",
        r"less\s*than\s*(?:rs\.?\s*)?\d+",
        r"below\s*(?:rs\.?\s*)?\d+",
        r"between\s*(?:rs\.?\s*)?\d+",
        r"(black|white|red|blue|grey|gray|brown|green|orange)\s+(shoes|boots|sneakers|shirt|shorts|jacket)",
        r"in\s+(footwear|apparel|accessories|shoes|clothing)",
    ],
    "recommendation": [
        r"recommend",
        r"suggest",
        r"what\s+should\s+i",
        r"best\s+(shoes|product|item)",
        r"good\s+for\s+(running|hiking|gym|walking|travel)",
        r"comfortable\s+for",
        r"suitable\s+for",
        r"something\s+(for|like|similar)",
        r"ideal\s+for",
    ],
    "faq": [
        r"return\s*polic",
        r"shipping\s*(policy|time|cost|fee)",
        r"how\s+long\s+does\s+shipping",
        r"can\s+i\s+(return|exchange|cancel)",
        r"do\s+you\s+(offer|accept|ship)",
        r"what\s+(payment|methods)",
        r"is\s+it\s+(authentic|genuine|original)",
        r"warranty",
        r"size\s*(guide|chart|exchange)",
        r"cash\s+on\s+delivery",
        r"refund",
    ],
}


def detect_intent(message: str) -> str:
    """Rule-based intent detection with regex patterns."""
    msg_lower = message.lower()

    scores = {intent: 0 for intent in INTENT_PATTERNS}
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                scores[intent] += 1

    best_intent = max(scores, key=scores.get)
    if scores[best_intent] == 0:
        # Heuristic: contains price/color/category → search; else → recommendation
        if any(word in msg_lower for word in ["price", "cost", "cheap", "expensive", "budget"]):
            return "product_search"
        return "recommendation"

    return best_intent


def extract_filters(message: str) -> dict:
    """
    Extract structured filters from natural language query.
    Returns: category, max_price, min_price, color, keywords, sort_by, order_id
    """
    msg_lower = message.lower()
    filters = {}

    # Price extraction
    price_patterns = [
        (r"under\s+(?:rs\.?\s*|pkr\s*)?(\d[\d,]*)", "max_price"),
        (r"below\s+(?:rs\.?\s*|pkr\s*)?(\d[\d,]*)", "max_price"),
        (r"less\s+than\s+(?:rs\.?\s*|pkr\s*)?(\d[\d,]*)", "max_price"),
        (r"above\s+(?:rs\.?\s*|pkr\s*)?(\d[\d,]*)", "min_price"),
        (r"over\s+(?:rs\.?\s*|pkr\s*)?(\d[\d,]*)", "min_price"),
        (r"more\s+than\s+(?:rs\.?\s*|pkr\s*)?(\d[\d,]*)", "min_price"),
    ]
    for pattern, key in price_patterns:
        m = re.search(pattern, msg_lower)
        if m:
            filters[key] = float(m.group(1).replace(",", ""))

    # Category detection
    category_map = {
        "shoes": "Footwear", "footwear": "Footwear", "sneakers": "Footwear",
        "boots": "Footwear", "runners": "Footwear", "running shoes": "Footwear",
        "hiking boots": "Hiking", "trail shoes": "Trail Running",
        "apparel": "Apparel", "clothing": "Apparel", "clothes": "Apparel",
        "shirt": "Apparel", "tee": "Apparel", "jacket": "Apparel",
        "shorts": "Apparel", "pants": "Apparel",
        "accessories": "Accessories", "watch": "Accessories",
        "gloves": "Accessories", "vest": "Accessories", "hydration": "Accessories",
    }
    for keyword, category in category_map.items():
        if keyword in msg_lower:
            filters["category"] = category
            break

    # Color detection
    colors = ["black", "white", "red", "blue", "grey", "gray", "brown", "green",
              "orange", "navy", "cream", "charcoal", "tan"]
    for color in colors:
        if color in msg_lower:
            filters["color"] = color
            break

    # Sort preference
    if any(w in msg_lower for w in ["cheapest", "lowest price", "budget", "affordable"]):
        filters["sort_by"] = "price_asc"
    elif any(w in msg_lower for w in ["expensive", "premium", "highest", "luxury"]):
        filters["sort_by"] = "price_desc"
    elif any(w in msg_lower for w in ["best rated", "top rated", "highest rated", "popular"]):
        filters["sort_by"] = "rating"

    # Order ID
    order_match = re.search(r"(ORD-\d{4}-\d{3})", message.upper())
    if order_match:
        filters["order_id"] = order_match.group(1)

    # Keyword extraction (simple noun phrases)
    activity_keywords = [
        "running", "hiking", "gym", "walking", "travel", "trail", "outdoor",
        "casual", "office", "workout", "cycling", "training", "daily",
        "comfortable", "lightweight", "waterproof", "breathable",
    ]
    found_kw = [kw for kw in activity_keywords if kw in msg_lower]
    if found_kw:
        filters["keywords"] = found_kw

    return filters


# ── LLM Response Generation ───────────────────────────────────────────────────

SYSTEM_PROMPT = """You are ShopBot, a friendly and knowledgeable AI shopping assistant for an athletic and outdoor gear ecommerce store.

Your personality:
- Warm, helpful, and conversational
- Expert in athletic footwear, apparel, and accessories
- Always give specific recommendations with reasoning
- Be concise but thorough

Your capabilities:
- Help users find products matching their needs
- Answer questions about shipping, returns, policies
- Track orders
- Give personalized recommendations

Response format rules:
- Keep responses under 200 words
- When listing products, mention name, key feature, and price (in PKR)
- Always end with a follow-up question or offer to help further
- Never make up product details not provided to you
- If products are found, format them naturally in prose, don't just list specs
"""


async def generate_llm_response(
    user_message: str,
    intent: str,
    products: list[dict],
    rag_context: list[dict],
    order_info: Optional[dict] = None,
) -> str:
    """
    Combine structured results + RAG context and generate a response via LLM.
    Supports OpenAI and Groq providers.
    """
    provider = settings.llm_provider.lower()
    
    # Decide which API to hit
    if provider == "groq" and settings.groq_api_key:
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        api_key = settings.groq_api_key
        model = settings.groq_model
    elif provider == "openai" and settings.openai_api_key:
        api_url = "https://api.openai.com/v1/chat/completions"
        api_key = settings.openai_api_key
        model = settings.openai_model
    else:
        return _template_response(intent, products, rag_context, order_info, user_message)

    context_parts = []
    # ... rest of the context building remains the same ...
    if products:
        product_lines = []
        for p in products[:6]:
            product_lines.append(
                f"- {p['name']} | Rs. {p['price']:,} | {p.get('category','')} | "
                f"Rating: {p.get('rating','N/A')} | Color: {p.get('color','')} | "
                f"ID: {p['id']}"
            )
        context_parts.append("AVAILABLE PRODUCTS:\n" + "\n".join(product_lines))

    faq_hits = [r for r in rag_context if r["metadata"].get("type") in ("faq", "policy")]
    if faq_hits:
        context_parts.append("RELEVANT KNOWLEDGE:\n" + "\n".join(
            f"- {h['text'][:300]}" for h in faq_hits[:3]
        ))

    if order_info:
        context_parts.append(f"ORDER INFO:\n{json.dumps(order_info, indent=2)}")

    context = "\n\n".join(context_parts) if context_parts else "No specific product/FAQ data found."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""User question: {user_message}

Intent detected: {intent}

Context:
{context}

Please provide a helpful, natural response based on the above context. 
If products are available, mention the most relevant ones naturally.
If no products match, say so helpfully and suggest alternatives."""
        }
    ]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 400,
                    "temperature": 0.7,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"{provider.capitalize()} error: {e}")
        return _template_response(intent, products, rag_context, order_info, user_message)


def _template_response(
    intent: str,
    products: list[dict],
    rag_context: list[dict],
    order_info: Optional[dict],
    user_message: str,
) -> str:
    """High-quality template responses as LLM fallback."""

    if intent == "order_tracking":
        if order_info:
            status = order_info.get("status", "Processing")
            items = ", ".join(order_info.get("items", []))
            tracking = order_info.get("tracking") or "not yet assigned"
            eta = order_info.get("estimated_delivery") or order_info.get("delivered_at", "N/A")
            return (
                f"📦 **Order {order_info['id']}** — Status: **{status}**\n\n"
                f"Items: {items}\n"
                f"Tracking number: {tracking}\n"
                f"{'Delivered on' if status == 'Delivered' else 'Estimated delivery'}: {eta}\n\n"
                f"Is there anything else I can help you with?"
            )
        return (
            "I'd be happy to track your order! Please share your Order ID "
            "(format: ORD-YYYY-XXX) and I'll pull up the details right away."
        )

    if intent == "faq":
        faq_hits = [r for r in rag_context if r["metadata"].get("type") in ("faq", "policy")]
        if faq_hits:
            best = faq_hits[0]
            text = best["text"].replace("Q: ", "").replace(" A: ", "\n\n")
            return f"{text}\n\nAnything else I can clarify for you? 😊"
        return (
            "Great question! Here are the key policies:\n\n"
            "• **Returns**: 30-day hassle-free returns\n"
            "• **Shipping**: Free on orders above Rs. 3,000 | 3-5 day delivery\n"
            "• **Payment**: Cards, JazzCash, EasyPaisa, COD\n\n"
            "Need more details on any of these? Just ask!"
        )

    if products:
        count = len(products)
        product_list = "\n".join(
            f"• **{p['name']}** — Rs. {p['price']:,} | ⭐ {p.get('rating', 'N/A')} | {p.get('color', '')}"
            for p in products[:4]
        )
        if intent == "recommendation":
            intro = f"Based on what you're looking for, here are my top picks:\n\n"
        else:
            intro = f"I found **{count} product{'s' if count > 1 else ''}** matching your search:\n\n"

        return (
            intro + product_list + "\n\n"
            "Would you like more details on any of these, or shall I filter by price, color, or category?"
        )

    # No results
    if intent == "product_search":
        return (
            "Hmm, I couldn't find an exact match for your search. "
            "Try broadening your criteria — for example, remove a color or price filter. "
            "Or tell me more about what you're looking for and I'll do my best to help! 🔍"
        )

    return (
        "Thanks for reaching out! I'm your AI shopping assistant. I can help you:\n\n"
        "• 🔍 **Find products** — 'Show me running shoes under Rs. 5,000'\n"
        "• 💡 **Get recommendations** — 'Best shoes for long walks'\n"
        "• 📦 **Track orders** — Share your Order ID\n"
        "• ❓ **Answer questions** — Returns, shipping, sizing\n\n"
        "What can I help you with today?"
    )
