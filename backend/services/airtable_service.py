"""
Airtable Service
- Fetches products/orders from Airtable with filterByFormula
- Falls back to demo data when not configured
- Python-side complex filters for queries too nuanced for Airtable
- Pagination, caching, and multi-client support
"""

import asyncio
import httpx
import time
import logging
from typing import Optional
from config import settings
from demo_data import DEMO_PRODUCTS, DEMO_ORDERS

logger = logging.getLogger(__name__)


class AirtableService:
    def __init__(self):
        self._cache: dict = {}
        self._cache_timestamps: dict = {}
        self.base_url = "https://api.airtable.com/v0"

    @property
    def is_configured(self) -> bool:
        return bool(settings.airtable_api_key and settings.airtable_base_id)

    def _cache_key(self, table: str, formula: str = "") -> str:
        return f"{settings.airtable_base_id}:{table}:{formula}"

    def _is_cache_valid(self, key: str) -> bool:
        ts = self._cache_timestamps.get(key, 0)
        return (time.time() - ts) < settings.cache_ttl_seconds

    def _set_cache(self, key: str, data):
        self._cache[key] = data
        self._cache_timestamps[key] = time.time()

    async def warm_cache(self):
        """Pre-warm product cache on startup."""
        if self.is_configured:
            await self.get_all_products()
        else:
            logger.info("Running in DEMO MODE — Airtable not configured")

    async def _fetch_airtable_records(
        self,
        table: str,
        formula: str = "",
        fields: Optional[list] = None,
    ) -> list[dict]:
        """
        Fetch all records from an Airtable table with pagination support.
        Handles 100-record pages automatically.
        """
        headers = {
            "Authorization": f"Bearer {settings.airtable_api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/{settings.airtable_base_id}/{table}"
        records = []
        offset = None

        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                params: dict = {"pageSize": 100}
                if formula:
                    params["filterByFormula"] = formula
                if fields:
                    params["fields[]"] = fields
                if offset:
                    params["offset"] = offset

                try:
                    resp = await client.get(url, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    records.extend(data.get("records", []))
                    offset = data.get("offset")
                    if not offset:
                        break
                except Exception as e:
                    logger.error(f"Airtable fetch error: {e}")
                    raise

        # Flatten: merge id + fields
        return [{"id": r["id"], **r["fields"]} for r in records]

    async def get_all_products(self) -> list[dict]:
        """Fetch all products — cached."""
        cache_key = self._cache_key(settings.airtable_products_table)
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        if not self.is_configured:
            return DEMO_PRODUCTS

        products = await self._fetch_airtable_records(settings.airtable_products_table)
        self._set_cache(cache_key, products)
        return products

    async def get_product_by_id(self, product_id: str) -> Optional[dict]:
        products = await self.get_all_products()
        return next((p for p in products if p.get("id") == product_id), None)

    async def search_products_structured(
        self,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        color: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        min_rating: Optional[float] = None,
        sort_by: Optional[str] = None,  # "price_asc", "price_desc", "rating"
        limit: int = 6,
    ) -> list[dict]:
        """
        Structured product search.
        Simple conditions → Airtable filterByFormula
        Complex conditions → Python-side filtering on cached data
        """
        all_products = await self.get_all_products()

        # ── Python-side filters (handles all complexity) ──────────────────
        results = all_products

        if category:
            cat_lower = category.lower()
            results = [
                p for p in results
                if cat_lower in (p.get("category", "") + " " + p.get("subcategory", "")).lower()
            ]

        if color:
            color_lower = color.lower()
            results = [
                p for p in results
                if color_lower in p.get("color", "").lower()
            ]

        if max_price is not None:
            results = [p for p in results if p.get("price", 0) <= max_price]

        if min_price is not None:
            results = [p for p in results if p.get("price", 0) >= min_price]

        if min_rating is not None:
            results = [p for p in results if p.get("rating", 0) >= min_rating]

        if keywords:
            def matches_keywords(product: dict) -> bool:
                searchable = " ".join([
                    product.get("name", ""),
                    product.get("description", ""),
                    product.get("category", ""),
                    " ".join(product.get("tags", [])),
                ]).lower()
                return any(kw.lower() in searchable for kw in keywords)

            results = [p for p in results if matches_keywords(p)]

        # ── Sorting ───────────────────────────────────────────────────────
        if sort_by == "price_asc":
            results.sort(key=lambda p: p.get("price", 0))
        elif sort_by == "price_desc":
            results.sort(key=lambda p: p.get("price", 0), reverse=True)
        elif sort_by == "rating":
            results.sort(key=lambda p: p.get("rating", 0), reverse=True)
        else:
            # Default: rating-weighted
            results.sort(key=lambda p: p.get("rating", 0), reverse=True)

        return results[:limit]

    async def get_order(self, order_id: str) -> Optional[dict]:
        """Look up an order by ID."""
        # Demo mode
        if not self.is_configured:
            return DEMO_ORDERS.get(order_id.upper())

        try:
            formula = f"{{OrderID}} = '{order_id}'"
            records = await self._fetch_airtable_records(
                settings.airtable_orders_table, formula=formula
            )
            return records[0] if records else None
        except Exception as e:
            logger.error(f"Order lookup error: {e}")
            return None

    # ── Client configuration API ──────────────────────────────────────────
    def configure_client(self, api_key: str, base_id: str):
        """
        Swap Airtable config per-request (multi-tenant support).
        In production, this would come from a per-client config store.
        """
        import os
        os.environ["AIRTABLE_API_KEY"] = api_key
        os.environ["AIRTABLE_BASE_ID"] = base_id
        # Force settings reload
        settings.__init__()
        # Clear cache for new client
        self._cache.clear()
        self._cache_timestamps.clear()


airtable_service = AirtableService()
