from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from models.database import get_db
from dependencies.user_deps import get_current_user_from_request
from services.file_upload_service import FileUploadService
from services.rabbitmq_connection_service import RabbitMQConnectionService
from services.user_service import UserData
from schemas import FileUploadResponse, FileListResponse, FileMetadataResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    import os
    allowed_extensions_str = os.getenv("ALLOWED_FILE_EXTENSIONS", ".csv,.txt,.json,.xlsx,.xls")
    allowed_extensions = [ext.strip() for ext in allowed_extensions_str.split(",")]

    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''

    if f'.{file_extension}' not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )

    file_metadata = await FileUploadService.upload_file(db, file, user_data)
    return FileUploadResponse.from_orm(file_metadata)


@router.get("/", response_model=List[FileListResponse])
async def list_user_files(
    skip: int = Query(0, ge=0, description="Number of files to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of files to return"),
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):
    files = await FileUploadService.get_user_files(db, user_data, skip, limit)
    return [FileListResponse.from_orm(file) for file in files]


@router.get("/{file_id}", response_model=FileMetadataResponse)
async def get_file_metadata(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):
    file_metadata = await FileUploadService.get_file_by_id(db, file_id, user_data)
    return FileMetadataResponse.from_orm(file_metadata)


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):
    await FileUploadService.delete_file(db, file_id, user_data)


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):
    file_metadata = await FileUploadService.get_file_by_id(db, file_id, user_data)

    if not file_metadata.is_processed:
        message_metadata = {
            "file_id": file_metadata.id,
            "filename": file_metadata.original_filename,
            "file_path": file_metadata.file_path,
            "user_id": file_metadata.user_id,
            "file_size_bytes": file_metadata.file_size_bytes
        }

        try:
            rabbitmq_service = RabbitMQConnectionService()
            await rabbitmq_service.publish_file_download_message(message_metadata)
            print(f"📤 File download message published for unprocessed file: {file_metadata.id}")
        except Exception as e:
            print(f"⚠️ Failed to publish download message: {str(e)}")
    else:
        print(f"⏭️ File already processed, skipping queue: {file_metadata.id}")

    return FileResponse(
        path=file_metadata.file_path,
        filename=file_metadata.original_filename,
        media_type='application/octet-stream'
    )


@router.patch("/{file_id}/mark-processed", status_code=200)
async def mark_file_as_processed(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):
    file_metadata = await FileUploadService.get_file_by_id(db, file_id, user_data)

    await FileUploadService.mark_file_as_processed(db, file_id, user_data)

    return {"message": f"File {file_id} marked as processed successfully"}


@router.post("/{file_id}/process", status_code=202)
async def add_file_to_processing_queue(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):
    file_metadata = await FileUploadService.get_file_by_id(db, file_id, user_data)

    if file_metadata.is_processed:
        raise HTTPException(
            status_code=409,
            detail=f"File {file_id} has already been processed"
        )

    message_metadata = {
        "file_id": file_metadata.id,
        "filename": file_metadata.original_filename,
        "file_path": file_metadata.file_path,
        "user_id": file_metadata.user_id,
        "file_size_bytes": file_metadata.file_size_bytes
    }

    try:
        rabbitmq_service = RabbitMQConnectionService()
        await rabbitmq_service.publish_file_download_message(message_metadata)

        return {
            "message": f"File {file_id} successfully added to processing queue",
            "file_id": file_id,
            "filename": file_metadata.original_filename,
            "queue_status": "queued"
        }
    except Exception as e:
        print(f"❌ Failed to add file to processing queue: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add file to processing queue: {str(e)}"
        )