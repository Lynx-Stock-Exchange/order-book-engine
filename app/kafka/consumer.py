import json
import os
from kafka import KafkaConsumer
from app.db import Database
from app.execution_service import ExecutionService

consumer = KafkaConsumer(
    os.getenv("KAFKA_STOCK_PRICES_TOPIC", "stock.prices"),
    bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    group_id="order-book-engine",
)

execution_service = ExecutionService()


def start_consumer():

    for message in consumer:

        try:
            data = message.value

            instrument_id = data["ticker"]
            current_price = data["price"]

            trades = execution_service.execute_tick(
                instrument_id=instrument_id,
                current_price=current_price,
            )

            print("TRADES:", trades)

        except Exception as e:
            print(f"ERROR processing tick (topic={message.topic} partition={message.partition} offset={message.offset}): {e}")


if __name__ == "__main__":
    Database.init_pool()
    start_consumer()
