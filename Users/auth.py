import os
import bcrypt
from jose import jwt,JWTError
from dotenv import load_dotenv
from config.models import User
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta,datetime
from fastapi import Depends,HTTPException,status
from sqlalchemy.orm import Session
from config.database import get_db

load_dotenv()

SECRET_KEY=os.getenv('SECRET_KEY')
ALGORITHM=os.getenv('ALGORITHM')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_hashed_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    # Return the hashed password as a string
    return hashed_password.decode('utf-8')

def validate_password(password,hashed_password):
    password_match = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    return password_match

def create_jwt_token(data:dict,expiry_time:timedelta=None):
    to_encode = data.copy()
    if expiry_time:
        expiry_time = datetime.now()+expiry_time
    else:
        expiry_time=datetime.now()+timedelta(hours=24)
    to_encode.update(
        {"exp":expiry_time}
    )
    encoded_token = jwt.encode(data,SECRET_KEY,ALGORITHM)
    return {
        "access_token":encoded_token,
        "token_type":"Bearer"
    }

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        
        user_id = payload.get("sub")
    except Exception as e:
        print(f"Error in Auth ::: {e}")
        raise credentials_exception  
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
