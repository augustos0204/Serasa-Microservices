import os
import json
import aio_pika
from typing import Optional, Dict, Any

class RabbitMQConnectionService:
    def __init__(self):
        self.host = os.getenv("RABBITMQ_HOST")
        self.port = int(os.getenv("RABBITMQ_PORT"))
        self.user = os.getenv("RABBITMQ_USER")
        self.password = os.getenv("RABBITMQ_PASSWORD")
        self.url = os.getenv("RABBITMQ_URL")

    async def test_connection(self) -> bool:
        """Test RabbitMQ connection and log result"""
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
        """Get connection information for logging"""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "status": "checking..."
        }

    async def consume_file_download_message(self, user_id: int) -> Optional[Dict[Any, Any]]:
        """
        Consume a single message from the file download queue for specific user

        Args:
            user_id: ID of the user requesting the message

        Returns:
            Dict: File metadata from the queue message, or None if no message for user
        """
        connection = None
        try:
            connection = await aio_pika.connect_robust(self.url)
            channel = await connection.channel()

            queue_name = os.getenv("DOWNLOAD_QUEUE_NAME", "file_downloads")

            queue = await channel.declare_queue(queue_name, durable=True)

            max_attempts = 10
            checked_messages = []

            for attempt in range(max_attempts):
                message = await queue.get(no_ack=False)

                if message is None:
                    for checked_msg in checked_messages:
                        await checked_msg.nack(requeue=True)
                    break

                try:
                    message_data = json.loads(message.body.decode())

                    if message_data.get("user_id") == user_id:
                        await message.ack()

                        for checked_msg in checked_messages:
                            await checked_msg.nack(requeue=True)

                        print(f"✅ Consumed message from queue for user {user_id}: {queue_name}")
                        return message_data
                    else:
                        checked_messages.append(message)

                except json.JSONDecodeError:
                    await message.nack(requeue=False)
                    print(f"⚠️ Rejected invalid message from queue: {queue_name}")

            for checked_msg in checked_messages:
                await checked_msg.nack(requeue=True)

            print(f"📭 No messages found for user {user_id} in queue: {queue_name}")
            return None

        except Exception as e:
            print(f"❌ Failed to consume message from queue: {str(e)}")
            return None
        finally:
            if connection:
                await connection.close()