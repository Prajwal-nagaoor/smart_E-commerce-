from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session

from .database import get_db
from .model import Product,User
from .schemas import Product_create, Product_response,Product_update
from .auth import get_current_user, SECRET_KEY,ALGORITHM
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
router = APIRouter(prefix="/products", tags=["Products"])
security = HTTPBearer(auto_error=False)
def get_optional_user(
        credentials:HTTPAuthorizationCredentials=Depends(security),
        db:Session=Depends(get_db)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = payload.get("user_id")

        if not user_id:
            return None
        user = db.query(User).filter(
            User.id == user_id
        ).first()

        return user
    except JWTError:
        return None
@router.post("/", response_model=Product_response)
def create_product(product_data:Product_create,
                   db:Session=Depends(get_db),
                   current_user:User=Depends(get_current_user)):
    if not product_data.product_name or not product_data.product_desc or not product_data.product_price or not product_data.category or not product_data.stock:
        raise HTTPException(
            status_code=400,
            detail="all fields need to be filled"
        )
    if current_user.role not in ("SELLER","ADMIN"):
        raise HTTPException(
            status_code=400,
            detail="Only seller and admin and add the product"
        )
    new_product = Product(
        user_id = current_user.id,
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
@router.get("/", response_model=list[Product_response])
def get_all_product(db:Session=Depends(get_db),
                    current_user:User=Depends(get_optional_user)):
    if current_user and current_user.role == "SELLER":
        product = db.query(Product).filter(
            Product.user_id == current_user.id
        ).all()

        return product
    else:
        product = db.query(Product).all()

        return product
@router.put("/edit_product/{product_id}", response_model=Product_response)
def update_product(
    product_id: int,
    product_data: Product_update,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["SELLER", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only seller or admin can edit products"
        )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if current_user.role == "SELLER" and product.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can edit only your own products"
        )

    product.product_name = product_data.product_name
    product.product_desc = product_data.product_desc
    product.product_price = product_data.product_price
    product.category = product_data.category
    product.stock = product_data.stock
    product.popularity = product_data.popularity

    db.commit()
    db.refresh(product)

    return product
@router.delete("/delete-product/{product_id}")
def delete_product(product_id:int, current_user : User = Depends(get_optional_user),
                   db:Session=Depends(get_db)):
    if current_user.role not in ['SELLER','ADMIN']:
        raise HTTPException(
            status_code=403,
            detail="Only seller or admin can delete the products"
        )
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()
    if product is None:
        raise HTTPException(
            status_code=401,
            detail="Product not found"
        )
    if current_user.role == 'SELLER' and product.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can delete your own products only"
        )
    db.delete(product)
    db.commit()

    return {
        "message":"Product deleted successfully"
    }
