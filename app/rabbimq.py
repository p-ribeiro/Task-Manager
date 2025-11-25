import os

import pika
import pika.exceptions
from dotenv import load_dotenv

load_dotenv()


class Rabbitmq:
    _instance = None
    _connection = None
    _channel = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Rabbitmq, cls).__new__(cls)
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASS", "guest")
        host = os.getenv("RABBITMQ_HOST", "localhost")
        port = int(os.getenv("RABBITMQ_PORT", 5672))

        credentials = pika.PlainCredentials(user, password)
        parameters = pika.ConnectionParameters(
            host=host, port=port, credentials=credentials
        )

        try:
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            print("RABBITMQ connection established")
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Failed to connect to RABBITMQ: {e}")
            self._connection = None
            self._instance = None

    def get_channel(self):
        if self._channel is None or self._channel.is_closed:
            print("Reconnecting to RABBITMQ...")
            self._connect()
        return self._channel

    def close_connection(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            self._connection = None
            self._channel = None
            # print("RABBITMQ connection closed.")
