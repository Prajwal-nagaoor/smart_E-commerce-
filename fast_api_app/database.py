from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus
password = quote_plus("Prajwal@123")
DATABASE_URL = f"mysql+pymysql://root:{password}@localhost:3306/smart_ecommerce"

engine = create_engine(
    DATABASE_URL
)
SessionLocal = sessionmaker(
    autocommit = False,
    autoflush= False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

