from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from sqlalchemy import text
from . import model
from .schemas import Registration, Login,profileresponse, update_profile
from .model import User
from .auth import hash_password, verify_password, create_access_token, verify_access_token,get_current_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware
from .auth import router as auth_router
import os
from .product import router as product_router, get_optional_user
app = FastAPI()
app.include_router(auth_router)
app.include_router(product_router)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("AUTH0_SECRET", "my-secret-key-change-this")
)

Base.metadata.create_all(bind=engine)

SECURITY = HTTPBearer()

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
        password = hash_password(user_data.password),
        role = user_data.role
        
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
@app.post("/login")
def login(user_data:Login, db:Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid Email and Password"
        )
    password = verify_password(
        user_data.password,
        existing_user.password
    )
    if not password:
        raise HTTPException(
            status_code=401,
            detail="Invalid Email and Password"
        )
    access_token = create_access_token(
        {"user_id": existing_user.id,
    "email": existing_user.email,
    "role": existing_user.role}
    )

    return {
        "message":"Login Successful",
        "user_id":existing_user.id,
        "user":existing_user.name,
        "Role":existing_user.role,
        "Email":existing_user.email,
        "Access Token":access_token
    }
@app.get("/prfile")
def profile(current_user : User=Depends(get_current_user)):
    return {
        "message":"Profile details",
        "user_id":current_user.id,
        "username":current_user.name,
        "email":current_user.email,
        "role":current_user.role
    }
@app.post("/logout")
def logout(credentials:HTTPAuthorizationCredentials = Depends(SECURITY)):
    token = credentials.credentials

    return {
        "message":"Logout Successfully",
        "details":"Please remove the access token from the client"
    }
@app.put("/update-profile/{user_id}", response_model=profileresponse)
def update_profile(user_id : int,user_data:update_profile,db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    
    if current_user.role != "ADMIN" and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can update only your own profile"
        )
    user = db.query(User).filter(
        User.id == user_id
    ).first()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not exists"
        )
    
    email_exists = db.query(User).filter(
        User.email == user_data.email,
        User.id != user.id
    ).first()

    if email_exists:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    user.name = user_data.name
    user.email = user_data.email
    if current_user.role == 'ADMIN':
        user.role = user_data.role

    db.commit()
    db.refresh(user)

    return user
