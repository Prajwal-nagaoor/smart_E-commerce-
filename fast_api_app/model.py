from sqlalchemy import Column, String, Integer
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(30), nullable=False, unique=True)
    password = Column(String(20), nullable=False)
    role = Column(String(10), nullable=False, default="customer")