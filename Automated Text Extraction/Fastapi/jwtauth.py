from fastapi import FastAPI, HTTPException, status, Depends, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
import hmac, hashlib, jwt
from typing import Dict
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI()
router = APIRouter()

# Enable CORS
origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secret key for JWT encoding
SECRET_KEY = os.getenv("SECRET_KEY")

# Initialize HTTPBearer for secured routes
security = HTTPBearer() 

# Database Configuration
DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}


# Database connection function
def create_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

# Password hashing function
def hash_password(password: str) -> str:
    return hmac.new(SECRET_KEY.encode(), msg=password.encode(), digestmod=hashlib.sha256).hexdigest()

# JWT Token creation
def create_jwt_token(data: dict):
    expiration = datetime.now(timezone.utc) + timedelta(minutes=50)
    token_payload = {"exp": expiration, **data}
    token = jwt.encode(token_payload, SECRET_KEY, algorithm="HS256")
    return token, expiration

# Decode JWT token
def decode_jwt_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Fetch user from database
def get_user_from_db(username: str):
    connection = create_db_connection()
    if connection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"Error fetching user from database: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Get current user based on JWT
def get_current_user(authorization: HTTPAuthorizationCredentials = Depends(security)):
    token = authorization.credentials
    payload = decode_jwt_token(token)
    username = payload.get("username")
    user = get_user_from_db(username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# Pydantic models for request bodies
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

# Register a new user
@router.post("/register")
def register(user: UserRegister):
    connection = create_db_connection()
    if connection is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        hashed_password = hash_password(user.password)
        
        query_check = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query_check, (user.username,))
        
        if cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

        query_insert = "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s)"
        
        cursor.execute(query_insert, (user.username, user.email, hashed_password))
        
        connection.commit()
        
        return {"message": "User registered successfully"}
    
    except Error as e:
        print(f"Error registering user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user")
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Login an existing user
@router.post("/login")
def login(user: UserLogin):
    db_user = get_user_from_db(user.username)
    
    if db_user and db_user["hashed_password"] == hash_password(user.password):
        token, expiration = create_jwt_token({"username": user.username})
        return {"access_token": token, "token_type": "bearer", "expires": expiration.isoformat()}
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

# Protected route
@router.get("/protected")
def protected_route(current_user: Dict = Depends(get_current_user)):
    return {"message": f"Hello, {current_user['username']}!"}

# Include router with a prefix to match the routes defined in the frontend
app.include_router(router, prefix="/auth")