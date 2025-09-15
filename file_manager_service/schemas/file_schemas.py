from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FileUploadResponse(BaseModel):
    id: int
    file_path: str
    filename: str = Field(..., alias="original_filename")
    file_size_bytes: int
    user_id: int
    is_processed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class FileListResponse(BaseModel):
    id: int
    file_path: str
    filename: str = Field(..., alias="original_filename")
    file_size_bytes: int
    user_id: int
    is_processed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class FileMetadataResponse(BaseModel):
    id: int
    file_path: str
    filename: str = Field(..., alias="original_filename")
    file_size_bytes: int
    user_id: int
    is_processed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True