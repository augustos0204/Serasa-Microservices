import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from pydantic import ValidationError
from schemas import FileProcessedDataCreate, CSVValidationSchema


class ValidationResult:
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.valid_records = []
        self.invalid_records = []
        self.total_rows = 0
        self.valid_count = 0
        self.invalid_count = 0
        self.error_details = []

    def add_error(self, line_number: Optional[int], field_name: Optional[str],
                  invalid_value: Optional[str], error_message: str, error_type: str):
        self.errors.append({
            'line_number': line_number,
            'field_name': field_name,
            'invalid_value': invalid_value,
            'error_message': error_message,
            'error_type': error_type
        })
        self.is_valid = False

    def add_valid_record(self, record: Dict[str, Any], line_number: int):
        record['_line_number'] = line_number
        self.valid_records.append(record)
        self.valid_count += 1

    def add_invalid_record(self, record: Dict[str, Any], line_number: int, errors: List[Dict]):
        record['_line_number'] = line_number
        record['_errors'] = errors
        self.invalid_records.append(record)
        self.invalid_count += 1


class CSVValidationService:

    @staticmethod
    def validate_csv_file_structure(file_path: str) -> ValidationResult:
        result = ValidationResult()

        try:
            if not Path(file_path).exists():
                result.add_error(
                    line_number=None,
                    field_name=None,
                    invalid_value=None,
                    error_message=f"File not found: {file_path}",
                    error_type="file_invalid"
                )
                return result

            try:
                df = pd.read_csv(file_path, sep=None, engine='python')
                result.total_rows = len(df)

                if len(df) == 0:
                    result.add_error(
                        line_number=None,
                        field_name=None,
                        invalid_value=None,
                        error_message="CSV file is empty",
                        error_type="file_invalid"
                    )
                    return result

                if len(df.columns) != len(set(df.columns)):
                    result.add_error(
                        line_number=None,
                        field_name=None,
                        invalid_value=None,
                        error_message="Duplicate column names detected",
                        error_type="file_invalid"
                    )

                unnamed_cols = [col for col in df.columns if str(col).startswith('Unnamed:')]
                if unnamed_cols:
                    result.add_error(
                        line_number=None,
                        field_name=None,
                        invalid_value=None,
                        error_message=f"Unnamed columns found: {unnamed_cols}",
                        error_type="file_invalid"
                    )

            except pd.errors.EmptyDataError:
                result.add_error(
                    line_number=None,
                    field_name=None,
                    invalid_value=None,
                    error_message="CSV file is empty",
                    error_type="file_invalid"
                )
            except pd.errors.ParserError as e:
                result.add_error(
                    line_number=None,
                    field_name=None,
                    invalid_value=None,
                    error_message=f"Error parsing CSV file: {str(e)}",
                    error_type="file_invalid"
                )

        except Exception as e:
            result.add_error(
                line_number=None,
                field_name=None,
                invalid_value=None,
                error_message=f"Unexpected error validating file structure: {str(e)}",
                error_type="file_invalid"
            )

        return result

    @staticmethod
    def validate_required_columns(file_path: str) -> ValidationResult:
        result = ValidationResult()

        try:
            df = pd.read_csv(file_path, sep=None, engine='python')
            result.total_rows = len(df)

            df_columns = [col.strip() for col in df.columns]
            missing_columns = CSVValidationSchema.validate_csv_structure(df_columns)

            if missing_columns:
                result.add_error(
                    line_number=None,
                    field_name=None,
                    invalid_value=None,
                    error_message=f"Missing required columns: {missing_columns}",
                    error_type="missing_columns"
                )

        except Exception as e:
            result.add_error(
                line_number=None,
                field_name=None,
                invalid_value=None,
                error_message=f"Error validating required columns: {str(e)}",
                error_type="missing_columns"
            )

        return result

    @staticmethod
    def validate_csv_data(file_path: str, file_id: int) -> ValidationResult:
        result = ValidationResult()

        try:
            df = pd.read_csv(file_path, sep=None, engine='python')
            result.total_rows = len(df)

            original_columns = df.columns.tolist()
            column_mapping = {}

            for original_col in original_columns:
                normalized_col = CSVValidationSchema.normalize_column_name(original_col)
                for required_col in CSVValidationSchema.REQUIRED_COLUMNS:
                    if normalized_col == CSVValidationSchema.normalize_column_name(required_col):
                        column_mapping[original_col] = required_col
                        break
                else:
                    column_mapping[original_col] = original_col

            df = df.rename(columns=column_mapping)

            for index, row in df.iterrows():
                line_number = index + 2
                row_errors = []

                try:
                    record = row.where(pd.notnull(row), None).to_dict()

                    validation_data = {
                        'nome': record.get('nome'),
                        'documento': record.get('documento'),
                        'telefone': record.get('telefone'),
                        'endereco': record.get('endereco'),
                        'file_id': file_id
                    }

                    validated_record = FileProcessedDataCreate(**validation_data)

                    result.add_valid_record(validated_record.dict(), line_number)

                except ValidationError as e:
                    for error in e.errors():
                        field_name = error['loc'][0] if error['loc'] else 'unknown'
                        error_message = error['msg']
                        invalid_value = str(record.get(field_name, '')) if record.get(field_name) is not None else 'null'

                        result.add_error(
                            line_number=line_number,
                            field_name=field_name,
                            invalid_value=invalid_value,
                            error_message=error_message,
                            error_type="data_validation"
                        )

                        row_errors.append({
                            'field_name': field_name,
                            'invalid_value': invalid_value,
                            'error_message': error_message
                        })

                    result.add_invalid_record(record, line_number, row_errors)

                except Exception as e:
                    error_message = f"Unexpected validation error: {str(e)}"

                    result.add_error(
                        line_number=line_number,
                        field_name=None,
                        invalid_value=None,
                        error_message=error_message,
                        error_type="data_validation"
                    )

                    row_errors.append({
                        'field_name': None,
                        'invalid_value': None,
                        'error_message': error_message
                    })

                    result.add_invalid_record(record, line_number, row_errors)

        except Exception as e:
            result.add_error(
                line_number=None,
                field_name=None,
                invalid_value=None,
                error_message=f"Error processing CSV data: {str(e)}",
                error_type="data_validation"
            )

        return result

    @staticmethod
    def validate_complete_csv(file_path: str, file_id: int) -> ValidationResult:
        structure_result = CSVValidationService.validate_csv_file_structure(file_path)
        if not structure_result.is_valid:
            return structure_result

        columns_result = CSVValidationService.validate_required_columns(file_path)
        if not columns_result.is_valid:
            return columns_result

        data_result = CSVValidationService.validate_csv_data(file_path, file_id)

        return data_result