import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models.file_metadata import FileMetadata
from services.user_service import UserData


class FileUploadService:
    @staticmethod
    async def upload_file(
        db: AsyncSession,
        file: UploadFile,
        user: UserData
    ) -> FileMetadata:
        try:
            upload_dir = os.getenv("UPLOAD_DIR", "/app/files")
            upload_dir_abs = Path(upload_dir)

            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix if file.filename else ""
            filename = f"{file_id}{file_extension}"

            user_dir = upload_dir_abs / "original" / str(user.id)
            try:
                user_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise HTTPException(status_code=500, detail=f"Permission denied creating upload directory: {e}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create upload directory: {e}")

            file_path = user_dir / filename

            file_content = await file.read()
            file_size = len(file_content)

            max_size = int(os.getenv("MAX_FILE_SIZE_MB", "10")) * 1024 * 1024
            if file_size > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds maximum allowed size of {max_size // (1024*1024)}MB"
                )

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_content)

            file_metadata = FileMetadata(
                file_path=str(file_path),
                original_filename=file.filename,
                file_size_bytes=file_size,
                user_id=user.id
            )

            db.add(file_metadata)
            await db.commit()
            await db.refresh(file_metadata)

            return file_metadata

        except Exception as e:
            if 'file_path' in locals() and Path(file_path).exists():
                Path(file_path).unlink()

            if isinstance(e, HTTPException):
                raise e

            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {str(e)}"
            )

    @staticmethod
    async def get_user_files(
        db: AsyncSession,
        user: UserData,
        skip: int = 0,
        limit: int = 100
    ) -> list[FileMetadata]:
        from sqlalchemy import select

        query = select(FileMetadata).where(
            FileMetadata.user_id == user.id
        ).offset(skip).limit(limit).order_by(FileMetadata.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_all_files(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> list[FileMetadata]:
        from sqlalchemy import select

        query = select(FileMetadata).offset(skip).limit(limit).order_by(FileMetadata.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_file_by_id(
        db: AsyncSession,
        file_id: int,
        user: UserData
    ) -> FileMetadata:
        from sqlalchemy import select

        query = select(FileMetadata).where(
            FileMetadata.id == file_id,
            FileMetadata.user_id == user.id
        )

        result = await db.execute(query)
        file_metadata = result.scalar_one_or_none()

        if not file_metadata:
            raise HTTPException(
                status_code=404,
                detail="File not found or access denied"
            )

        return file_metadata

    @staticmethod
    async def delete_file(
        db: AsyncSession,
        file_id: int,
        user: UserData
    ) -> bool:
        from sqlalchemy import select

        query = select(FileMetadata).where(
            FileMetadata.id == file_id,
            FileMetadata.user_id == user.id
        )

        result = await db.execute(query)
        file_metadata = result.scalar_one_or_none()

        if not file_metadata:
            raise HTTPException(
                status_code=404,
                detail="File not found or access denied"
            )

        file_path = Path(file_metadata.file_path)
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete physical file: {str(e)}"
            )

        await db.delete(file_metadata)
        await db.commit()

        return True

    @staticmethod
    async def get_file_for_download(
        db: AsyncSession,
        file_id: int
    ) -> FileMetadata:
        from sqlalchemy import select

        query = select(FileMetadata).where(FileMetadata.id == file_id)
        result = await db.execute(query)
        file_metadata = result.scalar_one_or_none()

        if not file_metadata:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        file_path = Path(file_metadata.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Physical file not found on server"
            )

        return file_metadata

    @staticmethod
    async def mark_file_as_processed(
        db: AsyncSession,
        file_id: int,
        user: UserData
    ) -> bool:
        from sqlalchemy import select

        query = select(FileMetadata).where(
            FileMetadata.id == file_id,
            FileMetadata.user_id == user.id
        )

        result = await db.execute(query)
        file_metadata = result.scalar_one_or_none()

        if not file_metadata:
            raise HTTPException(
                status_code=404,
                detail="File not found or access denied"
            )

        file_metadata.is_processed = True
        await db.commit()
        await db.refresh(file_metadata)

        print(f"✅ File {file_id} marked as processed")
        return True