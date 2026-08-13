from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import time

from shared.database import get_db
from user_management.models import User
from user_management.schemas import UserCreate, UserResponse, Token
from user_management.security import hash_password, verify_password, create_access_token
from user_management.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# Simple in-memory rate limiting for login attempts
login_attempts = {}

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé."
        )
    
    new_user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Simple rate limiting: 5 attempts per minute per IP
    client_ip = "client"  # In production, use request.client.host
    current_time = time.time()
    
    # Clean old attempts (older than 1 minute)
    login_attempts[client_ip] = [t for t in login_attempts.get(client_ip, []) if current_time - t < 60]
    
    # Check rate limit
    if len(login_attempts.get(client_ip, [])) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives de connexion. Réessayez dans 1 minute."
        )
    
    # Record this attempt
    login_attempts.setdefault(client_ip, []).append(current_time)
    
    # Authenticate user
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisateur inactif."
        )
    
    # Create JWT access token (use email as subject)
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
