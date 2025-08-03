from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = "luggixx_secret_key_2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app without a prefix
app = FastAPI(title="Luggixx API", description="Porter/Coolie Ride Booking System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    phone: str
    role: str  # "customer" or "porter"
    is_available: bool = True  # for porters
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    phone: str
    role: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: str
    role: str
    is_available: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class RideRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    pickup_location: str
    destination: str
    porter_id: Optional[str] = None
    status: str = "pending"  # pending, assigned, in_progress, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class RideRequestCreate(BaseModel):
    pickup_location: str
    destination: str

class RideResponse(BaseModel):
    id: str
    customer_id: str
    pickup_location: str
    destination: str
    porter_id: Optional[str] = None
    porter_name: Optional[str] = None  
    porter_phone: Optional[str] = None
    status: str
    created_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# Helper Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    email = verify_token(credentials.credentials)
    user = await db.users.find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Initialize static porter accounts
async def init_static_porters():
    porter_accounts = [
        {"email": "porter1@luggixx.com", "name": "Raj Kumar", "phone": "+91-9876543210", "password": "password123"},
        {"email": "porter2@luggixx.com", "name": "Amit Singh", "phone": "+91-9876543211", "password": "password123"},
        {"email": "porter3@luggixx.com", "name": "Vikram Yadav", "phone": "+91-9876543212", "password": "password123"},
        {"email": "porter4@luggixx.com", "name": "Suresh Patel", "phone": "+91-9876543213", "password": "password123"},
        {"email": "porter5@luggixx.com", "name": "Ramesh Gupta", "phone": "+91-9876543214", "password": "password123"},
    ]
    
    for porter_data in porter_accounts:
        existing_porter = await db.users.find_one({"email": porter_data["email"]})
        if not existing_porter:
            porter = User(
                email=porter_data["email"],
                name=porter_data["name"],
                phone=porter_data["phone"],
                role="porter",
                is_available=True
            )
            porter_dict = porter.dict()
            porter_dict["password"] = hash_password(porter_data["password"])
            await db.users.insert_one(porter_dict)

# Routes
@api_router.post("/auth/register", response_model=Token)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        role=user_data.role,
        is_available=True if user_data.role == "porter" else False
    )
    
    user_dict = user.dict()
    user_dict["password"] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    user_response = UserResponse(**user.dict())
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.post("/auth/login", response_model=Token)
async def login_user(login_data: UserLogin):
    # Find user
    user_data = await db.users.find_one({"email": login_data.email})
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(login_data.password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data["email"]}, expires_delta=access_token_expires
    )
    
    user = User(**user_data)
    user_response = UserResponse(**user.dict())
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

@api_router.post("/rides/request", response_model=RideResponse)
async def create_ride_request(ride_data: RideRequestCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can request rides")
    
    # Create ride request
    ride = RideRequest(
        customer_id=current_user.id,
        pickup_location=ride_data.pickup_location,
        destination=ride_data.destination
    )
    
    # Auto-assign to available porter
    available_porters = await db.users.find({"role": "porter", "is_available": True}).to_list(100)
    if not available_porters:
        raise HTTPException(status_code=400, detail="No porters available at the moment")
    
    # Select random porter
    selected_porter = random.choice(available_porters)
    ride.porter_id = selected_porter["id"]
    ride.status = "assigned"
    ride.assigned_at = datetime.utcnow()
    
    # Save ride
    await db.rides.insert_one(ride.dict())
    
    # Prepare response with porter info
    return RideResponse(
        id=ride.id,
        customer_id=ride.customer_id,
        pickup_location=ride.pickup_location,
        destination=ride.destination,
        porter_id=ride.porter_id,
        porter_name=selected_porter["name"],
        porter_phone=selected_porter["phone"],
        status=ride.status,
        created_at=ride.created_at,
        assigned_at=ride.assigned_at,
        completed_at=ride.completed_at
    )

@api_router.get("/rides/my-rides", response_model=List[RideResponse])
async def get_user_rides(current_user: User = Depends(get_current_user)):
    if current_user.role == "customer":
        rides = await db.rides.find({"customer_id": current_user.id}).to_list(100)
    else:  # porter
        rides = await db.rides.find({"porter_id": current_user.id}).to_list(100)
    
    # Enrich rides with porter/customer info
    enriched_rides = []
    for ride_data in rides:
        ride_response = RideResponse(**ride_data)
        
        # Add porter info if available
        if ride_data.get("porter_id"):
            porter = await db.users.find_one({"id": ride_data["porter_id"]})
            if porter:
                ride_response.porter_name = porter["name"]
                ride_response.porter_phone = porter["phone"]
        
        enriched_rides.append(ride_response)
    
    return enriched_rides

@api_router.put("/rides/{ride_id}/status")
async def update_ride_status(ride_id: str, status: str, current_user: User = Depends(get_current_user)):
    # Find ride
    ride = await db.rides.find_one({"id": ride_id})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # Check permissions
    if current_user.role == "porter" and ride["porter_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your assigned rides")
    elif current_user.role == "customer" and ride["customer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own rides")
    
    # Update status
    update_data = {"status": status}
    if status == "completed":
        update_data["completed_at"] = datetime.utcnow()
    
    await db.rides.update_one({"id": ride_id}, {"$set": update_data})
    
    return {"message": "Ride status updated successfully"}

@api_router.get("/porters/available", response_model=List[UserResponse])
async def get_available_porters():
    porters = await db.users.find({"role": "porter", "is_available": True}).to_list(100)
    return [UserResponse(**porter) for porter in porters]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_static_porters()
    logger.info("Static porter accounts initialized")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()