from decimal import Decimal
import json
from fastapi import Depends, FastAPI, HTTPException, status, WebSocket, Cookie, Query, WebSocketDisconnect, Request, Form, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import app.config as config
from app.db_conn import conn
import time
import aiofiles
import boto3

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin",
        "email": "admin@admin.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", #password = secret
        "disabled": False,
    }
}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

class Lead(BaseModel):
    fullname: Optional[str]
    phone: Optional[str]
    alt_phone: Optional[str]
    pincode: Optional[str]
    address: Optional[str]
    occupation: Optional[str]
    budget: Optional[str]
    timeline: Optional[str]
    purpose: Optional[str]
    other: list[str] = []

def db(table_name: str):
    table = conn(config.Settings()).Table(table_name)
    return table

def insert(data):
    print(data)
    response = db('leads').put_item(
       Item=data
    )
    return response

@app.post("/leads/create")
async def index(token: str = Depends(oauth2_scheme), lead: Lead = Depends(), audio_file: UploadFile = File(...)):
    lead = lead.dict()
    lead['audio_file'] = audio_file.filename
    lead['id'] = str(int(time.time()))
    file_location = f"audio/{int(time.time())}_{audio_file.filename}"
    async with aiofiles.open(file_location, 'wb') as out_file:
        content = await audio_file.read()  # async read
        await out_file.write(content)  # async write
        
        
    return {
        "message": insert(lead)
        }