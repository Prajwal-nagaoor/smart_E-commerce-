from pydantic import BaseModel, EmailStr

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

    