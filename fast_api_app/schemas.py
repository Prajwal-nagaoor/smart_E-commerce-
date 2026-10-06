from pydantic import BaseModel, EmailStr, ConfigDict
from decimal import Decimal
from datetime import datetime
class Registration(BaseModel):
    
    name : str
    email : EmailStr
    password : str
    role : str

class update_profile(BaseModel):
    name : str
    email : EmailStr
    password : str
    role : str

class Login(BaseModel):
    email : EmailStr
    password : str

class profileresponse(BaseModel):
    id : int
    name:str
    email : str

class Product_create(BaseModel):
    product_name : str
    product_desc : str
    product_price : Decimal
    category : str
    stock : int
    popularity : int=0
class Product_response(BaseModel):
    id: int
    product_name: str
    product_desc: str
    product_price: Decimal
    category: str
    stock: int
    popularity: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Product_update(BaseModel):
    product_name: str | None=None
    product_desc: str | None=None
    product_price: Decimal | None=None
    category: str | None=None
    stock: int | None=None
    popularity: bool | None=None
class add_cart(BaseModel):
    product_id : int
    quantity : int
class cart_response(BaseModel):
    id : int
    user_id : int
    product_id : int
    quentity : int
   
class OrderItemResponse(BaseModel):
    id :int
    order_id : int
    product_id :int
    quantity : int
    price : Decimal

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id : int
    user_id : int
    total_amount :Decimal
    payment_status : str
    order_status : str
    created_at : datetime

    model_config=ConfigDict(from_attributes=True)

class PaymentRequest(BaseModel):
    order_id :int
    payment_method : str
    transaction_id : str | None = None
    status : str
    
class PaymentResponse(BaseModel):
    id : int
    order_id :int
    amount : Decimal
    payment_method : str
    transaction_id :str | None= None
    status : str
    created_at : datetime

    model_config=ConfigDict(from_attributes=True)

    