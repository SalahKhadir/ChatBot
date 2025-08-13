from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import User
from schemas import UserCreate, UserLogin, UserResponse, Token
from dependencies import get_current_user
from crud import get_user_by_email, create_user
from auth import verify_password, create_access_token

router = APIRouter()

@router.post("/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        print(f"🔍 Registration attempt for email: {user.email}")
        
        # Check if user already exists
        existing_user = get_user_by_email(db, user.email)
        if existing_user:
            print(f"❌ Email {user.email} already exists")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        db_user = create_user(db, user)
        print(f"✅ User created successfully: {db_user.email}")
        
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            role=db_user.role,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/auth/login", response_model=Token)
async def login_user(user: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    try:
        print(f"🔍 Login attempt for email: {user.email}")
        
        # Verify user credentials
        db_user = get_user_by_email(db, user.email)
        if not db_user:
            print(f"❌ User not found: {user.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not verify_password(user.password, db_user.hashed_password):
            print(f"❌ Invalid password for user: {user.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Update last login time
        db_user.last_login = datetime.now()
        db.commit()
        db.refresh(db_user)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(db_user.id)})
        print(f"✅ Login successful for user: {db_user.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=db_user.id,
                email=db_user.email,
                full_name=db_user.full_name,
                role=db_user.role,
                is_active=db_user.is_active,
                created_at=db_user.created_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
