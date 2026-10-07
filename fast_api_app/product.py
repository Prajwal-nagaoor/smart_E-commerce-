from fastapi import APIRouter, Depends, HTTPException, Form,UploadFile, File
import os
import shutil
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
@router.post("/create-product")
def create_product(
    product_name: str = Form(...),
    product_desc: str = Form(...),
    product_price: float = Form(...),
    category: str = Form(...),
    stock: int = Form(...),
    popularity: bool = Form(True),
    image: UploadFile = File(...),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Only seller can create product
    if current_user.role != "SELLER":
        raise HTTPException(
            status_code=403,
            detail="Only sellers can create products"
        )

    # Validate product data using your existing schema
    try:
        product_data = Product_create(
            product_name=product_name,
            product_desc=product_desc,
            product_price=product_price,
            category=category,
            stock=stock,
            popularity=popularity
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # Check image
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed"
        )

    # Create folder if it doesn't exist
    upload_dir = "media/products"
    os.makedirs(upload_dir, exist_ok=True)

    # Create image path
    file_path = os.path.join(upload_dir, image.filename)

    # Save image
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Create product
    new_product = Product(
        user_id=current_user.id,
        product_name=product_data.product_name,
        product_desc=product_data.product_desc,
        product_price=product_data.product_price,
        category=product_data.category,
        stock=product_data.stock,
        popularity=product_data.popularity,
        image=file_path
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {
        "message": "Product created successfully",
        "product_id": new_product.id,
        "product_name": new_product.product_name,
        "image": new_product.image
    }
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
@router.get("/search",response_model=list[Product_response])
def search_product(product_name:str,
                   db:Session=Depends(get_db)):
    products = db.query(Product).filter(
        Product.product_name.ilike(f"%{product_name}%")
    ).all()
    if products is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    return products
@router.get("/category/{category_name}", response_model=list[Product_response])
def get_product_by_category(
    category_name: str,
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(
        Product.category.ilike(f"%{category_name}%")
    ).all()

    if not products:
        raise HTTPException(
            status_code=404,
            detail="No product found in this category"
        )

    return products

@router.get("/price", response_model=list[Product_response])
def get_product_by_price(
    min_price:float,
    max_price:float,
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(
        Product.product_price >= min_price,
        Product.product_price <= max_price
    ).all()

    if not products:
        raise HTTPException(
            status_code=404,
            detail="No product found in this price range"
        )

    return products
@router.get("/papular", response_model=list[Product_response])
def get_product_by_papularity(db:Session=Depends(get_db)):
    products = db.query(Product).filter(
        Product.popularity == True
    ).all()

    if not products:
        raise HTTPException(
            status_code=404,
            detail="No papular products found"
        )

    return products
@router.get("/{product_id}", response_model=Product_response)
def get_single_product(product_id : int,
                       db:Session=Depends(get_db)):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    return product
