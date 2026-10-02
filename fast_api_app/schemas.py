from pydantic import BaseModel, EmailStr
from decimal import Decimal
from datetime import datetime
class Registration(BaseModel):
    
    name : str
    email : EmailStr
    password : str


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
    