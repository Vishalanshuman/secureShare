from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from config.models import User
from config.schemas import UserCreate, UserResponse,Token
from .auth import get_hashed_password,validate_password,create_jwt_token
from config.schemas import UserRole,UserResponse,UserCreate,UserLogin,EmailVerificationResponse
from config.database import get_db
from fastapi.security import OAuth2PasswordRequestForm
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from .email_body import get_email_body
load_dotenv()



router = APIRouter()
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = get_hashed_password(user.password)

    # Ensure the role is properly normalized to match the Enum definition
    user_role = user.role.upper() if hasattr(user, 'role') else UserRole.CLIENT.name

    if user_role not in UserRole.__members__:
        raise HTTPException(status_code=400, detail=f"Invalid role: {user_role}")

    # Create a new user
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
    try:
        subject = "Email Verification - File Sharing System"  
        message = MIMEMultipart('alternative', None, [MIMEText(email_body, 'html')])
        message['Subject'] = subject
        message['From'] = os.getenv('MAIL_USERNAME')
        message['To'] = new_user.email

        server = smtplib.SMTP('smtp.gmail.com', 587)  
        server.ehlo()
        server.starttls()
        server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
        server.sendmail(os.getenv('MAIL_USERNAME'), new_user.email, message.as_string())
        server.quit()
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f'Error in sending mail: {e}')

    return new_user



@router.get("/verify-email/{user_id}", response_model=EmailVerificationResponse)
def verify_email(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        return {"message": "User already verified", "email_verified": True}

    user.is_verified = True
    db.commit()
    return {"message": "Email verified successfully", "email_verified": True}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.is_verified or not validate_password(form_data.password,user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    jwt_token = create_jwt_token({"sub":str(user.id)})

    return jwt_token
