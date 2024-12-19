from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import secrets
from enum import Enum as PyEnum
from .database import Base  

class UserRole(PyEnum):
    OPS = "OPS"
    CLIENT = "CLIENT"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)  
    role = Column(Enum(UserRole), nullable=False)  
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploaded_files = relationship("File", back_populates="user")
    download_links = relationship("SecureDownloadLink", back_populates="client")

class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Actual storage path
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="uploaded_files")
    download_links = relationship("SecureDownloadLink", back_populates="file")

class SecureDownloadLink(Base):
    __tablename__ = 'secure_links'

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    secure_token = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(hours=24))  

    file = relationship("File", back_populates="download_links")
    client = relationship("User", back_populates="download_links")

    @staticmethod
    def generate_secure_token():
        return secrets.token_urlsafe(32)

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

