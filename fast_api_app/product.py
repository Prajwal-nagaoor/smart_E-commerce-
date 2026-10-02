from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .model import Product
from .schemas import Product_create, Product_response
router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=Product_response)
def create_product(product_data:Product_create,
                   db:Session=Depends(get_db)):
    if not product_data.product_name or not product_data.product_desc or not product_data.product_price or not product_data.category or not product_data.stock:
        raise HTTPException(
            status_code=400,
            detail="all fields need to be filled"
        )
    new_product = Product(
        product_name = product_data.product_name,
        product_desc = product_data.product_desc,
        product_price = product_data.product_price,
        category = product_data.category,
        stock = product_data.stock,
        popularity = product_data.popularity
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product