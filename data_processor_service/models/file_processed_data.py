from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.sql import func
from .base import Base


class FileProcessedData(Base):
    """Model for storing processed CSV file data"""
    __tablename__ = "file_processed_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    nome = Column(String(255), nullable=False, comment="Nome completo do usuário")
    documento = Column(String(50), nullable=False, comment="CPF ou outro documento de identificação", unique=True)
    telefone = Column(String(20), nullable=False, comment="Número de telefone")
    endereco = Column(String(500), nullable=False, comment="Endereço completo")

    file_id = Column(Integer, nullable=False, comment="ID do arquivo que originou este registro")
    processed_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Data e hora do processamento")

    def __repr__(self):
        return f"<FileProcessedData(id={self.id}, nome='{self.nome}', documento='{self.documento}')>"