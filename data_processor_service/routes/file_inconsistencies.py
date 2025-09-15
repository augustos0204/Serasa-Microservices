from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from models.database import get_db
from models.file_inconsistencies import FileInconsistencies
from schemas import FileInconsistencyResponse
from dependencies.user_deps import get_current_user_from_request
from services.user_service import UserData

router = APIRouter(prefix="/file-inconsistencies", tags=["file-inconsistencies"])


@router.get("/", response_model=List[FileInconsistencyResponse])
async def get_file_inconsistencies(
    file_id: Optional[int] = Query(None, description="Filter by specific file ID"),
    error_type: Optional[str] = Query(None, description="Filter by error type (file_invalid, missing_columns, data_validation)"),
    line_number: Optional[int] = Query(None, description="Filter by specific line number"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):

    try:
        query = select(FileInconsistencies)

        conditions = []

        if file_id is not None:
            conditions.append(FileInconsistencies.file_id == file_id)

        if error_type is not None:
            valid_types = ['file_invalid', 'missing_columns', 'data_validation']
            if error_type not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid error_type. Must be one of: {valid_types}"
                )
            conditions.append(FileInconsistencies.error_type == error_type)

        if line_number is not None:
            conditions.append(FileInconsistencies.line_number == line_number)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(
            FileInconsistencies.file_id.asc(),
            FileInconsistencies.line_number.asc().nulls_first(),
            FileInconsistencies.created_at.desc()
        )
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        inconsistencies = result.scalars().all()

        return [
            FileInconsistencyResponse(
                id=inc.id,
                file_id=inc.file_id,
                line_number=inc.line_number,
                field_name=inc.field_name,
                invalid_value=inc.invalid_value,
                error_message=inc.error_message,
                error_type=inc.error_type,
                created_at=inc.created_at
            )
            for inc in inconsistencies
        ]

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching file inconsistencies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching file inconsistencies: {str(e)}"
        )


@router.get("/{file_id}", response_model=List[FileInconsistencyResponse])
async def get_inconsistencies_by_file_id(
    file_id: int,
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    line_number: Optional[int] = Query(None, description="Filter by specific line number"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):

    try:
        query = select(FileInconsistencies).where(
            FileInconsistencies.file_id == file_id
        )

        if error_type is not None:
            valid_types = ['file_invalid', 'missing_columns', 'data_validation']
            if error_type not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid error_type. Must be one of: {valid_types}"
                )
            query = query.where(FileInconsistencies.error_type == error_type)

        if line_number is not None:
            query = query.where(FileInconsistencies.line_number == line_number)

        query = query.order_by(
            FileInconsistencies.line_number.asc().nulls_first(),
            FileInconsistencies.created_at.desc()
        )
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        inconsistencies = result.scalars().all()

        if not inconsistencies:
            count_query = select(FileInconsistencies).where(
                FileInconsistencies.file_id == file_id
            )
            count_result = await db.execute(count_query)
            if not count_result.scalars().first():
                return []

        return [
            FileInconsistencyResponse(
                id=inc.id,
                file_id=inc.file_id,
                line_number=inc.line_number,
                field_name=inc.field_name,
                invalid_value=inc.invalid_value,
                error_message=inc.error_message,
                error_type=inc.error_type,
                created_at=inc.created_at
            )
            for inc in inconsistencies
        ]

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching inconsistencies for file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching inconsistencies for file {file_id}: {str(e)}"
        )


@router.get("/summary/{file_id}")
async def get_file_inconsistencies_summary(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):

    try:
        from sqlalchemy import func

        query = select(
            FileInconsistencies.error_type,
            func.count(FileInconsistencies.id).label('count')
        ).where(
            FileInconsistencies.file_id == file_id
        ).group_by(FileInconsistencies.error_type)

        result = await db.execute(query)
        error_counts = {row.error_type: row.count for row in result.fetchall()}

        total_query = select(func.count(FileInconsistencies.id)).where(
            FileInconsistencies.file_id == file_id
        )
        total_result = await db.execute(total_query)
        total_count = total_result.scalar() or 0

        line_errors_query = select(func.count(FileInconsistencies.id)).where(
            and_(
                FileInconsistencies.file_id == file_id,
                FileInconsistencies.line_number.isnot(None)
            )
        )
        line_errors_result = await db.execute(line_errors_query)
        line_errors_count = line_errors_result.scalar() or 0

        return {
            "file_id": file_id,
            "total_inconsistencies": total_count,
            "line_level_errors": line_errors_count,
            "structural_errors": total_count - line_errors_count,
            "error_counts_by_type": {
                "file_invalid": error_counts.get('file_invalid', 0),
                "missing_columns": error_counts.get('missing_columns', 0),
                "data_validation": error_counts.get('data_validation', 0)
            },
            "has_structural_issues": error_counts.get('file_invalid', 0) > 0 or error_counts.get('missing_columns', 0) > 0,
            "has_data_issues": error_counts.get('data_validation', 0) > 0
        }

    except Exception as e:
        print(f"❌ Error getting summary for file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting summary for file {file_id}: {str(e)}"
        )