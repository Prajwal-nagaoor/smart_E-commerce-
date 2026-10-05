from sqlalchemy import Column, String, Integer, DECIMAL, Boolean, DateTime, ForeignKey
from decimal import Decimal
from .database import Base
from datetime import timezone, datetime
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(30), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False, default="customer")

class Product(Base):
    __tablename__ = "Product"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    product_desc = Column(String(400), nullable=False)
    product_price = Column(DECIMAL(10,2), nullable=False, default=0)
    category = Column(String(200), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    popularity = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship(User)