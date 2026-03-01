from pydantic import BaseModel , Field , EmailStr
from datetime import datetime 
from enum import Enum

class UserSignUpModel(BaseModel):
    username: str = Field(..., min_length=6, max_length=20)
    password: str = Field(..., min_length=6, max_length=20)

class UserLoginModel(BaseModel):
    username: str = Field(..., min_length=6, max_length=20)
    password: str = Field(..., min_length=6, max_length=20)




