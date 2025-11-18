from typing import Union
from pydantic import BaseModel, Field, validator
from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime


app = FastAPI()

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/mydb"

# Database connection setup for PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

# Product model
class Product(BaseModel):
    name: str = Field(..., min_length=1, description="Product name cannot be empty")
    sku: str = Field(..., min_length=3, description="SKU must be at least 3 characters long")
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    stock: int = Field(..., ge=0, description="Stock must be greater than or equal to 0")
    category: str = Field(..., description="Category must be one of ['อาหาร', 'เครื่องดื่ม', 'ของใช้', 'เสื้อผ้า']")

    @validator("category")
    def validate_category(cls, value):
        allowed_categories = ["อาหาร", "เครื่องดื่ม", "ของใช้", "เสื้อผ้า"]
        if value not in allowed_categories:
            raise ValueError(f"Category must be one of {allowed_categories}")
        return value

@app.get("/")
def read_root():
    return {"Hello": "World"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}


@app.post("/api/products")
def create_product(product: Product):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if SKU already exists
    cursor.execute("SELECT COUNT(*) FROM products WHERE sku = %s", (product.sku,))
    if cursor.fetchone()["count"] > 0:
        conn.close()
        raise HTTPException(status_code=400, detail="SKU already exists")

    # Correct INSERT syntax for psycopg2
    cursor.execute(
        """
        INSERT INTO products (name, sku, price, stock, category)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (product.name, product.sku, product.price, product.stock, product.category),
    )

    product_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()

    return {
        "id": product_id,
        "name": product.name,
        "sku": product.sku,
        "price": product.price,
        "stock": product.stock,
        "category": product.category,
        "timestamp": datetime.now().isoformat()
    },

# Add endpoint to get all products
@app.get("/api/products")
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all products from the database
    cursor.execute("SELECT id, name, sku, price, stock, category FROM products")
    products = cursor.fetchall()
    conn.close()

    return {"products": products}



# create
# body
# name string
# sku id string ex.(FOOD001) ห้ามซ้ำ
# price float
# stock int
# category string
# rule create
# name ห้ามว่าง
# SKU ห้ามว่าง ห้ามซ้ำ ยาวอย่างน้อย 3 ตัวอักษร
# price ต้องมากกว่า > 0
# stock ต้องมากกว่าหรือเท่ากับ >= 0
# category ต้องเป็นหนึ่งใน ["อาหาร", "เครื่องดื่ม", "ของใช้", "เสื้อผ้า"]
