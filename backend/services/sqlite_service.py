import sqlite3
import logging
import os
from typing import Optional, List, Dict, Any
from config import settings
from demo_data import DEMO_PRODUCTS, DEMO_ORDERS

logger = logging.getLogger(__name__)

class SqliteService:
    def __init__(self):
        self.db_path = settings.sqlite_db_path

    @property
    def is_configured(self) -> bool:
        return bool(self.db_path)

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def initialize(self):
        """Initialize the SQLite database and seed it if empty."""
        if os.path.exists(self.db_path):
            logger.info(f"SQLite database already exists at {self.db_path}")
            return

        logger.info(f"Initializing SQLite database at {self.db_path}...")
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                price REAL,
                category TEXT,
                subcategory TEXT,
                color TEXT,
                rating REAL,
                stock INTEGER,
                image_url TEXT,
                tags TEXT -- Stored as comma-separated string
            )
        """)

        # Create Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                status TEXT,
                items TEXT, -- Stored as comma-separated string
                total REAL,
                placed_at TEXT,
                delivered_at TEXT,
                estimated_delivery TEXT,
                tracking TEXT
            )
        """)

        # Seed Products
        for p in DEMO_PRODUCTS:
            cursor.execute("""
                INSERT INTO products (id, name, description, price, category, subcategory, color, rating, stock, image_url, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p['id'], p['name'], p['description'], p['price'], p['category'], 
                p.get('subcategory'), p.get('color'), p.get('rating'), p.get('stock'), 
                p.get('image_url'), ",".join(p.get('tags', []))
            ))

        # Seed Orders
        for order_id, o in DEMO_ORDERS.items():
            cursor.execute("""
                INSERT INTO orders (id, status, items, total, placed_at, delivered_at, estimated_delivery, tracking)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                o['id'], o['status'], ",".join(o.get('items', [])), o['total'], 
                o.get('placed_at'), o.get('delivered_at'), o.get('estimated_delivery'), o.get('tracking')
            ))

        conn.commit()
        conn.close()
        logger.info("✅ SQLite database initialized and seeded.")

    async def get_all_products(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            p = dict(row)
            p['tags'] = p['tags'].split(',') if p['tags'] else []
            products.append(p)
        return products

    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            p = dict(row)
            p['tags'] = p['tags'].split(',') if p['tags'] else []
            return p
        return None

    async def search_products_structured(
        self,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        color: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        sort_by: Optional[str] = None,
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM products WHERE 1=1"
        params = []

        if category:
            query += " AND (LOWER(category) LIKE ? OR LOWER(subcategory) LIKE ?)"
            params.extend([f"%{category.lower()}%", f"%{category.lower()}%"])
        
        if color:
            query += " AND LOWER(color) LIKE ?"
            params.append(f"%{color.lower()}%")
            
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
            
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
            
        if min_rating is not None:
            query += " AND rating >= ?"
            params.append(min_rating)
            
        if keywords:
            for kw in keywords:
                query += " AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(tags) LIKE ?)"
                params.extend([f"%{kw.lower()}%", f"%{kw.lower()}%", f"%{kw.lower()}%"])

        if sort_by == "price_asc":
            query += " ORDER BY price ASC"
        elif sort_by == "price_desc":
            query += " ORDER BY price DESC"
        elif sort_by == "rating":
            query += " ORDER BY rating DESC"
        else:
            query += " ORDER BY rating DESC"

        query += " LIMIT ?"
        params.append(limit)

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        products = []
        for row in rows:
            p = dict(row)
            p['tags'] = p['tags'].split(',') if p['tags'] else []
            products.append(p)
        return products

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id.upper(),))
        row = cursor.fetchone()
        conn.close()

        if row:
            o = dict(row)
            o['items'] = o['items'].split(',') if o['items'] else []
            return o
        return None

sqlite_service = SqliteService()
