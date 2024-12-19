from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from config.models import User
from config.schemas import UserCreate, UserResponse
from .auth import get_hashed_password,validate_password,create_jwt_token
from config.schemas import UserRole,UserResponse,UserCreate,UserLogin,EmailVerificationResponse
from config.database import get_db
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from .email import get_email_body,send_email
load_dotenv()



router = APIRouter()
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = get_hashed_password(user.password)
        user_role = user.role.upper()

        if user_role not in UserRole.__members__:
            raise HTTPException(status_code=400, detail=f"Invalid role: {user_role}")

        new_user = User(
            email=user.email,
            password=hashed_password,
            role=user_role,
            is_verified=False,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        verification_url = f"http://localhost:8000/verify-email/{new_user.id}"
        
        email_body = get_email_body(new_user,verification_url)
        send_email_ = send_email(new_user,email_body)
        print(send_email_)

        return new_user
    except Exception as e:
        return {"error":str(e)}




@router.get("/verify-email/{user_id}", response_model=EmailVerificationResponse)
def verify_email(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.is_verified:
            return {"message": "User already verified", "email_verified": True}

        user.is_verified = True
        db.commit()
        return {"message": "Email verified successfully", "email_verified": True}
    except Exception as e:
        return {"message": f"Erro :{e}", "email_verified": False}


@router.post("/login")
def login(form_data:UserLogin , db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="User account is not verified")
    if not validate_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    jwt_token = create_jwt_token({"sub":str(user.id)})

    return jwt_token

