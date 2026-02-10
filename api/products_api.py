from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db import get_db
from db.models import Product

router = APIRouter(tags=["products"])

@router.get("/")
async def list_products(db: AsyncSession = Depends(get_db)):
    stmt = select(Product).where(Product.is_active == True)
    result = await db.execute(stmt)
    products = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "product_number": p.product_number,
            "price": float(p.price) if p.price else None,
            "payments_count": p.payments_count,
        }
        for p in products
    ]
