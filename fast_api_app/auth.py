import bcrypt
from datetime import datetime, timedelta,timezone
from jose import jwt
SECRET_KEY = "my-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
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
