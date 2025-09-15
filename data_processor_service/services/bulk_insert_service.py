from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from typing import List, Dict, Any
from models.file_processed_data import FileProcessedData
from services.csv_validation_service import ValidationResult


class BulkInsertService:

    @staticmethod
    async def bulk_insert_processed_data(db: AsyncSession, valid_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        result = {
            'success': False,
            'records_inserted': 0,
            'errors': [],
            'duplicate_errors': 0
        }

        try:
            if not valid_records:
                result['success'] = True
                return result

            bulk_data = []
            for record in valid_records:
                clean_record = {k: v for k, v in record.items() if not k.startswith('_')}
                bulk_data.append(clean_record)

            batch_size = 1000
            total_inserted = 0
            duplicate_count = 0

            for i in range(0, len(bulk_data), batch_size):
                batch = bulk_data[i:i + batch_size]

                try:
                    await db.execute(
                        insert(FileProcessedData).values(batch)
                    )
                    total_inserted += len(batch)

                except Exception as batch_error:
                    await db.rollback()
                    print(f"❌ Batch insert failed, transaction rolled back: {str(batch_error)}")

                    raise Exception(f"Bulk insert failed: {str(batch_error)}")

            await db.commit()

            result['success'] = True
            result['records_inserted'] = total_inserted
            result['duplicate_errors'] = duplicate_count

            print(f"✅ Bulk insert completed: {total_inserted} records inserted, {duplicate_count} duplicates skipped")

        except Exception as e:
            await db.rollback()
            result['errors'].append({
                'general_error': str(e)
            })
            print(f"❌ Bulk insert failed: {str(e)}")

        return result

    @staticmethod
    async def prepare_bulk_data(validation_result: ValidationResult) -> List[Dict[str, Any]]:
        try:
            if not validation_result.valid_records:
                return []

            prepared_records = []

            for record in validation_result.valid_records:
                clean_record = {}

                required_fields = ['nome', 'documento', 'telefone', 'endereco', 'file_id']

                for field in required_fields:
                    if field in record:
                        clean_record[field] = record[field]

                if len(clean_record) == len(required_fields):
                    prepared_records.append(clean_record)
                else:
                    print(f"⚠️ Skipping record with missing fields: {record}")

            print(f"📝 Prepared {len(prepared_records)} records for bulk insert")
            return prepared_records

        except Exception as e:
            print(f"❌ Error preparing bulk data: {str(e)}")
            return []

    @staticmethod
    async def insert_validation_result(db: AsyncSession, validation_result: ValidationResult) -> Dict[str, Any]:
        try:
            prepared_records = await BulkInsertService.prepare_bulk_data(validation_result)

            if not prepared_records:
                return {
                    'success': True,
                    'records_inserted': 0,
                    'errors': [],
                    'message': 'No valid records to insert'
                }

            insert_result = await BulkInsertService.bulk_insert_processed_data(db, prepared_records)

            return insert_result

        except Exception as e:
            print(f"❌ Error inserting validation result: {str(e)}")
            return {
                'success': False,
                'records_inserted': 0,
                'errors': [{'general_error': str(e)}],
                'message': f'Error during insertion: {str(e)}'
            }

    @staticmethod
    def get_insert_statistics(insert_result: Dict[str, Any], validation_result: ValidationResult) -> Dict[str, Any]:
        return {
            'total_rows_processed': validation_result.total_rows,
            'valid_rows': validation_result.valid_count,
            'invalid_rows': validation_result.invalid_count,
            'records_inserted': insert_result.get('records_inserted', 0),
            'duplicate_records_skipped': insert_result.get('duplicate_errors', 0),
            'insertion_errors': len(insert_result.get('errors', [])),
            'insertion_success': insert_result.get('success', False),
            'validation_errors_count': len(validation_result.errors),
            'processing_success_rate': (
                (insert_result.get('records_inserted', 0) / validation_result.total_rows * 100)
                if validation_result.total_rows > 0 else 0
            )
        }