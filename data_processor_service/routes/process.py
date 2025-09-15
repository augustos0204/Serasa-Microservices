from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from services.rabbitmq_connection_service import RabbitMQConnectionService
from services.csv_validation_service import CSVValidationService
from services.inconsistency_service import InconsistencyService
from services.bulk_insert_service import BulkInsertService
from services.file_metadata_service import FileMetadataService
from schemas import (
    ProcessResponse, QueueMessageInfo, ValidationSummary,
    ProcessingSummary, FileInconsistencyResponse
)
from models.database import get_db
from dependencies.user_deps import get_current_user_from_request
from services.user_service import UserData


router = APIRouter(prefix="/process", tags=["process"])


@router.post("/", response_model=ProcessResponse)
async def process_file_from_queue(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: UserData = Depends(get_current_user_from_request)
):
    file_marked_processed = False

    try:
        rabbitmq_service = RabbitMQConnectionService()
        queue_message = await rabbitmq_service.consume_file_download_message(user_data.id)

        if not queue_message:
            return ProcessResponse(
                success=False,
                message=f"No messages available in the queue for user {user_data.id}",
                queue_message=None
            )

        queue_info = QueueMessageInfo(**queue_message)

        if not queue_info.file_path:
            return ProcessResponse(
                success=False,
                message="No file path found in queue message",
                queue_message=queue_info
            )

        print(f"🔄 Processing file: {queue_info.file_path} (File ID: {queue_info.file_id})")

        validation_result = CSVValidationService.validate_complete_csv(
            queue_info.file_path, queue_info.file_id
        )

        inconsistencies_recorded = 0
        if validation_result.errors:
            inconsistency_success = await InconsistencyService.record_validation_result(
                db, queue_info.file_id, validation_result
            )
            if inconsistency_success:
                inconsistencies_recorded = len(validation_result.errors)
                print(f"📝 Recorded {inconsistencies_recorded} inconsistencies")

        structural_errors = [e for e in validation_result.errors if e['error_type'] in ['file_invalid', 'missing_columns']]

        if structural_errors:
            validation_summary = ValidationSummary(
                total_rows=validation_result.total_rows,
                valid_rows=0,
                invalid_rows=validation_result.total_rows,
                structural_errors=len(structural_errors),
                missing_columns=[e['error_message'] for e in structural_errors if e['error_type'] == 'missing_columns'],
                data_validation_errors=len([e for e in validation_result.errors if e['error_type'] == 'data_validation'])
            )

            processing_summary = ProcessingSummary(
                records_inserted=0,
                duplicate_records_skipped=0,
                inconsistencies_recorded=inconsistencies_recorded,
                file_marked_processed=False,
                processing_success_rate=0.0
            )

            return ProcessResponse(
                success=False,
                message=f"File validation failed: {structural_errors[0]['error_message'] if structural_errors else 'Unknown structural error'}",
                queue_message=queue_info,
                validation_summary=validation_summary,
                processing_summary=processing_summary
            )

        try:
            insert_result = await BulkInsertService.insert_validation_result(db, validation_result)
            insert_stats = BulkInsertService.get_insert_statistics(insert_result, validation_result)

            if not insert_result['success'] or insert_result.get('errors'):
                raise HTTPException(
                    status_code=500,
                    detail=f"Bulk insert failed: {insert_result.get('errors', 'Unknown error')}"
                )

        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Critical error during bulk insert: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Critical error during data insertion: {str(e)}"
            )

        if insert_result['success']:
            try:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    file_metadata_service = FileMetadataService()
                    mark_success = await file_metadata_service.mark_file_as_processed(
                        queue_info.file_id, token
                    )
                    file_marked_processed = mark_success
                    if mark_success:
                        print(f"✅ File {queue_info.file_id} marked as processed")
            except Exception as e:
                print(f"⚠️ Error marking file as processed: {str(e)}")

        validation_summary = ValidationSummary(
            total_rows=validation_result.total_rows,
            valid_rows=validation_result.valid_count,
            invalid_rows=validation_result.invalid_count,
            structural_errors=0,
            missing_columns=[],
            data_validation_errors=validation_result.invalid_count
        )

        processing_summary = ProcessingSummary(
            records_inserted=insert_result.get('records_inserted', 0),
            duplicate_records_skipped=insert_result.get('duplicate_errors', 0),
            inconsistencies_recorded=inconsistencies_recorded,
            file_marked_processed=file_marked_processed,
            processing_success_rate=insert_stats['processing_success_rate']
        )

        file_inconsistencies = await InconsistencyService.get_file_inconsistencies(db, queue_info.file_id)
        inconsistencies_response = [
            FileInconsistencyResponse(**inc) for inc in file_inconsistencies[:100]
        ]

        success_message = f"File processed successfully: {insert_result['records_inserted']} records inserted"
        if validation_result.invalid_count > 0:
            success_message += f", {validation_result.invalid_count} records had validation errors"

        return ProcessResponse(
            success=True,
            message=success_message,
            queue_message=queue_info,
            validation_summary=validation_summary,
            processing_summary=processing_summary,
            inconsistencies=inconsistencies_response
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in process endpoint: {str(e)}")

        try:
            if 'queue_info' in locals() and queue_info.file_id:
                await InconsistencyService.record_file_invalid(
                    db, queue_info.file_id, f"Processing error: {str(e)}"
                )
        except:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"Error processing file from queue: {str(e)}"
        )