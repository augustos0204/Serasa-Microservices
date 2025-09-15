from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from typing import List, Dict, Any
from models.file_inconsistencies import FileInconsistencies
from services.csv_validation_service import ValidationResult


class InconsistencyService:

    @staticmethod
    async def record_file_invalid(db: AsyncSession, file_id: int, error_message: str) -> bool:
        try:
            inconsistency = FileInconsistencies(
                file_id=file_id,
                line_number=None,
                field_name=None,
                invalid_value=None,
                error_message=error_message,
                error_type="file_invalid"
            )

            db.add(inconsistency)
            await db.commit()
            return True

        except Exception as e:
            await db.rollback()
            print(f"❌ Error recording file invalid: {str(e)}")
            return False

    @staticmethod
    async def record_missing_columns(db: AsyncSession, file_id: int, missing_columns: List[str]) -> bool:
        try:
            error_message = f"Missing required columns: {', '.join(missing_columns)}"

            inconsistency = FileInconsistencies(
                file_id=file_id,
                line_number=None,
                field_name=None,
                invalid_value=None,
                error_message=error_message,
                error_type="missing_columns"
            )

            db.add(inconsistency)
            await db.commit()
            return True

        except Exception as e:
            await db.rollback()
            print(f"❌ Error recording missing columns: {str(e)}")
            return False

    @staticmethod
    async def record_data_validation_errors(db: AsyncSession, file_id: int, validation_errors: List[Dict[str, Any]]) -> bool:
        try:
            if not validation_errors:
                return True

            bulk_data = []
            for error in validation_errors:
                bulk_data.append({
                    'file_id': file_id,
                    'line_number': error.get('line_number'),
                    'field_name': error.get('field_name'),
                    'invalid_value': error.get('invalid_value'),
                    'error_message': error.get('error_message'),
                    'error_type': error.get('error_type', 'data_validation')
                })

            if bulk_data:
                await db.execute(
                    insert(FileInconsistencies).values(bulk_data)
                )
                await db.commit()

            return True

        except Exception as e:
            await db.rollback()
            print(f"❌ Error recording data validation errors: {str(e)}")
            return False

    @staticmethod
    async def record_validation_result(db: AsyncSession, file_id: int, validation_result: ValidationResult) -> bool:
        try:
            if not validation_result.errors:
                return True

            file_errors = []
            missing_column_errors = []
            data_validation_errors = []

            for error in validation_result.errors:
                error_type = error.get('error_type')

                if error_type == 'file_invalid':
                    file_errors.append(error)
                elif error_type == 'missing_columns':
                    missing_column_errors.append(error)
                elif error_type == 'data_validation':
                    data_validation_errors.append(error)

            for error in file_errors:
                await InconsistencyService.record_file_invalid(
                    db, file_id, error['error_message']
                )

            for error in missing_column_errors:
                await InconsistencyService.record_file_invalid(
                    db, file_id, error['error_message']
                )

            if data_validation_errors:
                await InconsistencyService.record_data_validation_errors(
                    db, file_id, data_validation_errors
                )

            return True

        except Exception as e:
            await db.rollback()
            print(f"❌ Error recording validation result: {str(e)}")
            return False

    @staticmethod
    async def bulk_insert_inconsistencies(db: AsyncSession, file_id: int, inconsistencies: List[Dict[str, Any]]) -> bool:
        try:
            if not inconsistencies:
                return True

            bulk_data = []
            for inconsistency in inconsistencies:
                record = {
                    'file_id': file_id,
                    'line_number': inconsistency.get('line_number'),
                    'field_name': inconsistency.get('field_name'),
                    'invalid_value': inconsistency.get('invalid_value'),
                    'error_message': inconsistency.get('error_message'),
                    'error_type': inconsistency.get('error_type', 'data_validation')
                }
                bulk_data.append(record)

            batch_size = 1000
            for i in range(0, len(bulk_data), batch_size):
                batch = bulk_data[i:i + batch_size]
                await db.execute(
                    insert(FileInconsistencies).values(batch)
                )

            await db.commit()
            print(f"✅ Successfully recorded {len(bulk_data)} inconsistencies for file {file_id}")
            return True

        except Exception as e:
            await db.rollback()
            print(f"❌ Error bulk inserting inconsistencies: {str(e)}")
            return False

    @staticmethod
    async def get_file_inconsistencies(db: AsyncSession, file_id: int) -> List[Dict[str, Any]]:

        try:
            from sqlalchemy import select

            result = await db.execute(
                select(FileInconsistencies).where(FileInconsistencies.file_id == file_id)
            )
            inconsistencies = result.scalars().all()

            return [
                {
                    'id': inc.id,
                    'file_id': inc.file_id,
                    'line_number': inc.line_number,
                    'field_name': inc.field_name,
                    'invalid_value': inc.invalid_value,
                    'error_message': inc.error_message,
                    'error_type': inc.error_type,
                    'created_at': inc.created_at.isoformat() if inc.created_at else None
                }
                for inc in inconsistencies
            ]

        except Exception as e:
            print(f"❌ Error retrieving file inconsistencies: {str(e)}")
            return []