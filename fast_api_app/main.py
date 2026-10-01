from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from sqlalchemy import text
from . import model
from .schemas import Registration
from .model import User
from .auth import hash_password


app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "FastAPI is running"}
@app.get("/test-db")
def test_db(db:Session=Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "message":"the database connect successfully"
    }
@app.post("/register")
def register(user_data:Registration, db:Session=Depends(get_db)):
    existing_email = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code = 400,
            detail="Email already exists"
        )
    new_user = User(
        name = user_data.name,
        email = user_data.email,
        password = hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "detail":{
            "message":"Registration successful",
            "user_id":new_user.id,
            "Username":new_user.name,
            "Email":new_user.email,
            "Role":new_user.role
        }
    }


    