from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from config.database import get_db
from Users.auth import get_current_user
from config.models import User, File as FileModel, UserRole,SecureDownloadLink
from config.schemas import FileListResponse,SecureURLResponse
import os
import datetime
from datetime import timedelta
router = APIRouter()

ALLOWED_EXTENSIONS = {"pptx", "docx", "xlsx"}
UPLOAD_DIRECTORY = "static/documents"  

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = File(...), 
    user: User = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    if user.role != UserRole.OPS:
        raise HTTPException(status_code=403, detail="Only Ops users can upload files")

    file_extension = file.filename.split(".")[-1]
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)
    
    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    new_file = FileModel(filename=file.filename, uploaded_by=user.id)
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return {"message": f"File {file.filename} uploaded successfully"}

@router.get("/files", response_model=FileListResponse)
def list_files(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Only Client users can view files")

    files = db.query(FileModel).all()
    return {"files": files}


@router.post("/files/{file_id}/generate-secure-link", response_model=SecureURLResponse)
def generate_secure_file_link(file_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Only Client users can generate secure links")

    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    secure_token = SecureDownloadLink.generate_secure_token()
    expires_at = datetime.utcnow() + timedelta(hours=24)

    secure_link = SecureDownloadLink(
        file_id=file.id,
        client_id=user.id,
        secure_token=secure_token,
        expires_at=expires_at
    )
    db.add(secure_link)
    db.commit()

    download_url = f"https://yourdomain.com/files/download/{secure_token}"
    return {"download_link": download_url, "message": "success"}
