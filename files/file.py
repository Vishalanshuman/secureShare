from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from config.database import get_db
from Users.auth import get_current_user
from config.models import User, File as FileModel, UserRole, SecureDownloadLink
from config.schemas import SecureURLResponse
from fastapi.responses import FileResponse
import os
import uuid
import datetime
from datetime import timedelta


router = APIRouter(prefix='/files', tags=["File"])

ALLOWED_EXTENSIONS = {"pptx", "docx", "xlsx"}
UPLOAD_DIRECTORY = "static/documents"  

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = File(...), 
    user: User = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    try:
        if user.role != UserRole.OPS:
            raise HTTPException(status_code=403, detail="Only Ops users can upload files")

        file_extension = file.filename.split(".")[-1]
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        if not os.path.exists(UPLOAD_DIRECTORY):
            os.makedirs(UPLOAD_DIRECTORY)

        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())
        new_file = FileModel(
            filename=file.filename,
            file_path=file_path,  
            uploaded_by=user.id,
            uploaded_at=datetime.datetime.utcnow()  
        )
        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        return {"message": f"File {file.filename} uploaded successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.get("/")
def list_files(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if user.role != UserRole.CLIENT:
            raise HTTPException(status_code=403, detail="Only Client users can view files")

        files = db.query(FileModel).all()
        return {"files": files}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch files: {str(e)}")


@router.get("/{file_id}/generate-secure-link", response_model=SecureURLResponse)
def generate_secure_file_link(file_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if user.role != UserRole.CLIENT:
            raise HTTPException(status_code=403, detail="Only Client users can generate secure links")

        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        secure_token = SecureDownloadLink.generate_secure_token()
        expires_at = datetime.datetime.utcnow() + timedelta(hours=24)

        secure_link = SecureDownloadLink(
            file_id=file.id,
            client_id=user.id,
            secure_token=secure_token,
            expires_at=expires_at
        )
        db.add(secure_link)
        db.commit()

        download_url = f"http://localhost:8000/files/download/{secure_token}"
        return {"download_link": download_url, "message": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate secure link: {str(e)}")


@router.get("/download/{secure_token}")
def download_file(
    secure_token: str,
    user:User=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        secure_link = db.query(SecureDownloadLink).filter(SecureDownloadLink.secure_token == secure_token).first()
        if not secure_link:
            raise HTTPException(status_code=404, detail="Invalid or expired secure link")

        if secure_link.expires_at < datetime.datetime.utcnow():
            raise HTTPException(status_code=400, detail="Secure link has expired")

        file = db.query(FileModel).filter(FileModel.id == secure_link.file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        if secure_link.client_id != user.id:
            raise HTTPException(status_code=403, detail="You do not have permission to access this file")

        file_path = file.file_path

        if os.path.exists(file_path):
            return FileResponse(file_path, filename=file.filename, headers={"Content-Disposition": f"attachment; filename={file.filename}"})
        else:
            raise HTTPException(status_code=404, detail="File not found on the server")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")
