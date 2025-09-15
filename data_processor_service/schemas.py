from typing import List, Dict, Any, Optional, ClassVar
from datetime import datetime
from pydantic import BaseModel, validator


class ColumnInfo(BaseModel):
    name: str
    type: str
    non_null_count: int
    null_count: int


class CSVProcessResponse(BaseModel):
    file_path: str
    total_rows: int
    total_columns: int
    columns: List[ColumnInfo]
    data: List[Dict[str, Any]]
    processing_status: str
    message: str


class QueueMessageInfo(BaseModel):
    file_id: Optional[int] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
    user_id: Optional[int] = None
    download_timestamp: Optional[str] = None
    file_size_bytes: Optional[int] = None
    event_type: Optional[str] = None


class ValidationIssue(BaseModel):
    file_path: str
    validation_status: str
    issues: List[str]
    sample_columns: List[str]
    sample_row_count: int


class FileInconsistencyCreate(BaseModel):
    file_id: int
    line_number: Optional[int] = None
    field_name: Optional[str] = None
    invalid_value: Optional[str] = None
    error_message: str
    error_type: str


class FileInconsistencyResponse(BaseModel):
    id: int
    file_id: int
    line_number: Optional[int]
    field_name: Optional[str]
    invalid_value: Optional[str]
    error_message: str
    error_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationSummary(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    structural_errors: int
    missing_columns: List[str]
    data_validation_errors: int


class ProcessingSummary(BaseModel):
    records_inserted: int
    duplicate_records_skipped: int
    inconsistencies_recorded: int
    file_marked_processed: bool
    processing_success_rate: float


class ValidationResult(BaseModel):
    is_valid: bool
    error_count: int
    valid_record_count: int
    invalid_record_count: int
    total_rows: int


class FileProcessedDataCreate(BaseModel):
    nome: str
    documento: str
    telefone: str
    endereco: str
    file_id: int

    @validator('nome')
    def validate_nome(cls, v):
        if not v or not v.strip():
            raise ValueError('Nome é obrigatório e não pode estar vazio')

        v_clean = v.strip().lower()
        invalid_values = ['nome', 'name', 'usuario', 'user', 'cliente', 'person']
        if v_clean in invalid_values:
            raise ValueError('Nome não pode ser um valor genérico como "nome"')

        if len(v_clean) < 2 or v_clean.isdigit():
            raise ValueError('Nome deve ter pelo menos 2 caracteres e não pode ser apenas números')

        return v.strip()

    @validator('documento')
    def validate_documento(cls, v):
        if not v or not v.strip():
            raise ValueError('Documento é obrigatório e não pode estar vazio')

        v_clean = v.strip().lower()
        invalid_values = ['documento', 'doc', 'cpf', 'document', 'id']
        if v_clean in invalid_values:
            raise ValueError('Documento não pode ser um valor genérico como "documento"')

        v_numbers = ''.join(filter(str.isdigit, v))
        if len(v_numbers) < 10 or len(v_numbers) > 14:
            raise ValueError('Documento deve ter entre 10 e 14 dígitos')

        return v.strip()

    @validator('telefone')
    def validate_telefone(cls, v):
        if not v or not v.strip():
            raise ValueError('Telefone é obrigatório e não pode estar vazio')

        v_clean = v.strip().lower()
        invalid_values = ['telefone', 'phone', 'tel', 'fone', 'celular']
        if v_clean in invalid_values:
            raise ValueError('Telefone não pode ser um valor genérico como "telefone"')

        v_numbers = ''.join(filter(str.isdigit, v))
        if len(v_numbers) < 8:
            raise ValueError('Telefone deve ter pelo menos 8 dígitos')

        return v.strip()

    @validator('endereco')
    def validate_endereco(cls, v):
        if not v or not v.strip():
            raise ValueError('Endereço é obrigatório e não pode estar vazio')

        v_clean = v.strip().lower()
        invalid_values = ['endereco', 'endereço', 'address', 'addr', 'rua', 'av']
        if v_clean in invalid_values:
            raise ValueError('Endereço não pode ser um valor genérico como "endereço"')

        if len(v_clean) < 5:
            raise ValueError('Endereço deve ter pelo menos 5 caracteres')

        return v.strip()


class FileProcessedDataResponse(BaseModel):
    id: int
    nome: str
    documento: str
    telefone: str
    endereco: str
    file_id: int
    processed_at: datetime

    class Config:
        from_attributes = True


class CSVValidationSchema(BaseModel):
    REQUIRED_COLUMNS: ClassVar[List[str]] = ["nome", "documento", "telefone", "endereco"]

    @classmethod
    def normalize_column_name(cls, column_name: str) -> str:
        import re
        import unicodedata

        normalized = column_name.lower().strip()

        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')

        normalized = re.sub(r'\s+', ' ', normalized)

        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)

        normalized = normalized.replace(' ', '')

        return normalized

    @classmethod
    def validate_csv_structure(cls, df_columns: List[str]) -> List[str]:
        df_columns_normalized = [cls.normalize_column_name(col) for col in df_columns]

        required_normalized = [cls.normalize_column_name(col) for col in cls.REQUIRED_COLUMNS]

        missing_columns = []
        for i, required_col in enumerate(required_normalized):
            if required_col not in df_columns_normalized:
                missing_columns.append(cls.REQUIRED_COLUMNS[i])

        return missing_columns


class ProcessResponse(BaseModel):
    success: bool
    message: str
    queue_message: Optional[QueueMessageInfo] = None
    csv_data: Optional[CSVProcessResponse] = None
    validation_summary: Optional[ValidationSummary] = None
    processing_summary: Optional[ProcessingSummary] = None
    inconsistencies: Optional[List[FileInconsistencyResponse]] = None