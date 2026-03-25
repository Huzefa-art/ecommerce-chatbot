"""Products router — GET /api/products"""

from fastapi import APIRouter, Query
from typing import Optional
from services.data_service import get_data_service

router = APIRouter()


@router.get("/products")
async def get_products(
    category: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    min_price: Optional[float] = Query(None),
    sort_by: Optional[str] = Query(None),
    limit: int = Query(12, le=50),
):
    """Fetch products with optional filters."""
    data_service = get_data_service()
    products = await data_service.search_products_structured(
        category=category,
        max_price=max_price,
        min_price=min_price,
        sort_by=sort_by,
        limit=limit,
    )
    return {"products": products, "total": len(products)}


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    data_service = get_data_service()
    product = await data_service.get_product_by_id(product_id)
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    return product
