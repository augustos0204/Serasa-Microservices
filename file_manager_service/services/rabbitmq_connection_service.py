import os
import json
import aio_pika
from datetime import datetime
from typing import Optional

class RabbitMQConnectionService:
    def __init__(self):
        self.host = os.getenv("RABBITMQ_HOST")
        self.port = int(os.getenv("RABBITMQ_PORT"))
        self.user = os.getenv("RABBITMQ_USER")
        self.password = os.getenv("RABBITMQ_PASSWORD")
        self.url = os.getenv("RABBITMQ_URL")

    async def test_connection(self) -> bool:
        try:
            connection = await aio_pika.connect_robust(self.url)

            channel = await connection.channel()
            await channel.close()
            await connection.close()

            print("✅ RabbitMQ connection successful!")
            return True

        except Exception as e:
            print(f"❌ RabbitMQ connection failed")
            return False

    async def get_connection_info(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "status": "checking..."
        }

    async def publish_file_download_message(self, file_metadata: dict) -> bool:
        try:
            connection = await aio_pika.connect_robust(self.url)
            channel = await connection.channel()

            queue_name = os.getenv("DOWNLOAD_QUEUE_NAME", "file_downloads")

            queue = await channel.declare_queue(queue_name, durable=True)

            message_data = {
                "file_id": file_metadata.get("file_id"),
                "filename": file_metadata.get("filename"),
                "file_path": file_metadata.get("file_path"),
                "user_id": file_metadata.get("user_id"),
                "download_timestamp": datetime.utcnow().isoformat(),
                "file_size_bytes": file_metadata.get("file_size_bytes"),
                "event_type": "file_download"
            }

            await channel.default_exchange.publish(
                aio_pika.Message(
                    json.dumps(message_data).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue_name,
            )

            await connection.close()
            print(f"✅ File download message published to queue: {queue_name}")
            return True

        except Exception as e:
            print(f"❌ Failed to publish file download message: {str(e)}")
            return False