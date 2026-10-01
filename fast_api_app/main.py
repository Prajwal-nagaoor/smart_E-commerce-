from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import get_db
from sqlalchemy import text

app = FastAPI()
@app.get("/")
def main():
    return {
        "message":"fastapi server is running successfully"
    }
@app.get("/test-db")
def test_db(db:Session=Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "message":"the database connect successfully"
    }