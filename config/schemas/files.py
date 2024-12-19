from pydantic import BaseModel
from datetime import datetime

# File Response Schema
class FileResponse(BaseModel):
    id: int
    filename: str
    uploaded_by: str  # Username of the uploader
    upload_time: datetime

    class Config:
        orm_mode = True

# File List Schema
class FileListResponse(BaseModel):
    files: list[FileResponse]


class SecureURLResponse(BaseModel):
    download_link: str  # The URL for downloading the file
    message: str        # A status or success message
