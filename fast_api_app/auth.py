import bcrypt
from datetime import datetime, timedelta,timezone
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from .model import User
import os
from fastapi import APIRouter, Request
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = "my-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
sucurity = HTTPBearer()
def hash_password(password: str):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

def verify_password(plane_password:str, hashed_password:str):
    return bcrypt.checkpw(
        plane_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )
def create_access_token(data:dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp":expire

    })

    access_token = jwt.encode(
        to_encode,SECRET_KEY,algorithm=ALGORITHM
    )

    return access_token

def verify_access_token(token:str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if user_id is None:
            return None
        return payload
    except JWTError:
        return None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(sucurity),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user

router = APIRouter()

oauth = OAuth()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")

print("AUTH0_DOMAIN =", AUTH0_DOMAIN)
print("AUTH0_CLIENT_ID =", AUTH0_CLIENT_ID)
print("AUTH0_CLIENT_SECRET loaded =", bool(AUTH0_CLIENT_SECRET))

oauth.register(
    name="auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    server_metadata_url=f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid profile email"
    }
)


@router.get("/login/google")
async def google_login(request: Request):

    redirect_uri = "http://127.0.0.1:8000/callback"

    return await oauth.auth0.authorize_redirect(
        request,
        redirect_uri,
        connection="google-oauth2"
    )


@router.get("/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):

    try:
        token = await oauth.auth0.authorize_access_token(request)

        userinfo = token.get("userinfo")

        if not userinfo:
            raise HTTPException(
                status_code=400,
                detail="Could not get user information"
            )

        email = userinfo.get("email")
        name = userinfo.get("name")

        if not email:
            raise HTTPException(
                status_code=400,
                detail="Google account email not available"
            )

        user = db.query(User).filter(
            User.email == email
        ).first()

        if not user:
            user = User(
                name=name or "Google User",
                email=email,
                password=hash_password(
                    os.urandom(32).hex()
                ),
                role="user"
            )

            db.add(user)
            db.commit()
            db.refresh(user)

        access_token = create_access_token({
            "user_id": user.id,
            "email": user.email,
            "role": user.role
        })

        return {
            "message": "Google login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )