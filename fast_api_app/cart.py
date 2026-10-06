from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .database import get_db
from .model import User, Product, Cart
from .schemas import add_cart, cart_response
from .auth import get_current_user
cart = APIRouter(prefix="/cart", tags=["cart"])
    
@cart.post("/add-cart/", response_model=cart_response)
def add_cart(cart_data:add_cart,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role in ['SELLER', 'ADMIN']:
        raise HTTPException(
            status_code=400,
            detail="Only customers can add the products in the cart"
        )
    get_product = db.query(Product).filter(
        Product.id == cart_data.product_id
    ).first()
    if not get_product:
        raise HTTPException(
            status_code=400,
            detail="Product not found"
        )
    if cart_data.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantitu must be grater than zero"

        )
    if cart_data.quantity > get_product.stock:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity is greater then available stock"
        )
    existing_item =  db.query(Cart).filter(
        Cart.product_id == cart_data.product_id,
        Cart.user_id == current_user.id
    ).first()

    if existing_item:
        new_quantity = existing_item.quentity + cart_data.quantity
        if new_quantity > get_product.stock:
            raise HTTPException(
                status_code=400,
                detail="Total quantity is greater than available stock"
            )
        existing_item.quentity = new_quantity
        db.commit()
        db.refresh(existing_item)

        return existing_item
    
    new_item = Cart(
        user_id = current_user.id,
        product_id =cart_data.product_id,
        quentity = cart_data.quantity
        )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item
@cart.get("/view-cart", response_model=list[cart_response])
def view_cart(db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    if current_user.role in ['SELLER','ADMIN']:
        raise HTTPException(
            status_code=401,
            detail="You are allowed to view the cart only customer can we the cart"
        )
    cart_items = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Empty Cart"
        )
    return cart_items
@cart.delete("/delete-cart/{cart_id}")
def delete_item_cart(cart_id:int,db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    if current_user.role in ['SELLER','ADMIN']:
        raise HTTPException(
            status_code=400,
            detail="Only customer can delete the cart"
        )
    item = db.query(Cart).filter(
        Cart.id == cart_id,
        Cart.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(
            status_code=404,
            detail="item not found"
        )
    db.delete(item)
    db.commit()

    return {
        "message":"Item deleted successfully"
    }

    

