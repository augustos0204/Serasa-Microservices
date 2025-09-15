from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .base import Base


class FileInconsistencies(Base):
    """Model for storing file processing inconsistencies and validation errors"""
    __tablename__ = "file_inconsistencies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    file_id = Column(Integer, nullable=False, comment="ID do arquivo que originou este erro")

    line_number = Column(Integer, nullable=True, comment="Número da linha com erro (null para erros estruturais)")

    field_name = Column(String(100), nullable=True, comment="Nome do campo com erro (null para erros estruturais)")

    invalid_value = Column(Text, nullable=True, comment="Valor inválido encontrado (null para erros estruturais)")
    error_message = Column(Text, nullable=False, comment="Mensagem descritiva do erro")
    error_type = Column(String(50), nullable=False, comment="Tipo do erro: file_invalid, missing_columns, data_validation")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Data e hora da criação do registro")

    def __repr__(self):
        return f"<FileInconsistencies(id={self.id}, file_id={self.file_id}, error_type='{self.error_type}', line={self.line_number})>"