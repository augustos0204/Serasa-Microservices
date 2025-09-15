import os
import pandas as pd
import aiofiles
from pathlib import Path
from typing import Dict, List, Any
from fastapi import HTTPException


class CSVProcessorService:
    @staticmethod
    async def process_csv_file(file_path: str) -> Dict[str, Any]:
        try:
            if not Path(file_path).exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {file_path}"
                )

            df = pd.read_csv(file_path, sep=None, engine='python')

            total_rows = len(df)
            total_columns = len(df.columns)

            df_sample = df.head(100)
            csv_data = df_sample.where(pd.notnull(df_sample), None).to_dict('records')

            columns_info = []
            for col in df.columns:
                col_info = {
                    "name": col,
                    "type": str(df[col].dtype),
                    "non_null_count": int(df[col].count()),
                    "null_count": int(df[col].isnull().sum())
                }
                columns_info.append(col_info)

            result = {
                "file_path": file_path,
                "total_rows": total_rows,
                "total_columns": total_columns,
                "columns": columns_info,
                "data": csv_data,
                "processing_status": "success",
                "message": f"Successfully processed {total_rows} rows and {total_columns} columns"
            }

            print(f"✅ CSV file processed successfully: {file_path}")
            return result

        except pd.errors.EmptyDataError:
            raise HTTPException(
                status_code=400,
                detail="CSV file is empty"
            )
        except pd.errors.ParserError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error parsing CSV file: {str(e)}"
            )
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_path}"
            )
        except Exception as e:
            print(f"❌ Error processing CSV file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing CSV file: {str(e)}"
            )

    @staticmethod
    async def validate_csv_structure(file_path: str) -> Dict[str, Any]:
        try:
            df_sample = pd.read_csv(file_path, nrows=10)

            issues = []

            empty_cols = [col for col in df_sample.columns if df_sample[col].isnull().all()]
            if empty_cols:
                issues.append(f"Empty columns found: {empty_cols}")

            if len(df_sample.columns) != len(set(df_sample.columns)):
                issues.append("Duplicate column names detected")

            unnamed_cols = [col for col in df_sample.columns if col.startswith('Unnamed:')]
            if unnamed_cols:
                issues.append(f"Unnamed columns found: {unnamed_cols}")

            return {
                "file_path": file_path,
                "validation_status": "passed" if not issues else "warning",
                "issues": issues,
                "sample_columns": list(df_sample.columns),
                "sample_row_count": len(df_sample)
            }

        except Exception as e:
            return {
                "file_path": file_path,
                "validation_status": "failed",
                "issues": [f"Validation failed: {str(e)}"],
                "sample_columns": [],
                "sample_row_count": 0
            }