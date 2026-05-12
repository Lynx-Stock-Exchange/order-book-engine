from decimal import Decimal
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    EXCHANGE_FEE_RATE = Decimal(
        os.getenv("EXCHANGE_FEE_RATE", "0.001")
    )

    MAX_ORDER_SIZE = Decimal(
        os.getenv("MAX_ORDER_SIZE", "10000")
    )

    KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
    KAFKA_STOCK_PRICES_TOPIC = os.getenv("KAFKA_STOCK_PRICES_TOPIC", "stock.prices")
    KAFKA_VOLUMES_TOPIC = os.getenv("KAFKA_VOLUMES_TOPIC", "order.volumes")

    INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")