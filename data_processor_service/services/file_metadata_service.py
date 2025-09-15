import os
import httpx
from typing import Optional


class FileMetadataService:
    @staticmethod
    async def mark_file_as_processed(file_id: int, token: str) -> bool:
        """
        Mark a file as processed by calling the File Manager Service

        Args:
            file_id: ID of the file to mark as processed
            token: JWT token for authentication

        Returns:
            bool: Success status
        """
        try:
            file_manager_url = os.getenv("FILE_MANAGER_SERVICE_URL")
            if not file_manager_url:
                print("❌ FILE_MANAGER_SERVICE_URL not configured")
                return False

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{file_manager_url}/files/{file_id}/mark-processed",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )

                if response.status_code == 200:
                    print(f"✅ File {file_id} marked as processed successfully")
                    return True
                else:
                    print(f"❌ Failed to mark file as processed: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Error marking file as processed: {str(e)}")
            return False