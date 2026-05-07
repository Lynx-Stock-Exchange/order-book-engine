import json
import os
from kafka import KafkaConsumer

from app.execution_service import ExecutionService

consumer = KafkaConsumer(
    "stock.prices",
    bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    group_id="order-book-engine",
)

execution_service = ExecutionService()


def start_consumer():

    for message in consumer:

        data = message.value

        instrument_id = data["ticker"]
        current_price = data["price"]

        trades = execution_service.execute_tick(
            instrument_id=instrument_id,
            current_price=current_price,
        )

        print("TRADES:", trades)