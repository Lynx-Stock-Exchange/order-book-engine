import json
from kafka import KafkaConsumer
from app.db import Database

from app.execution_service import ExecutionService

consumer = KafkaConsumer(
    "stock_prices",
    "option_prices",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    group_id="order-book-engine",
)

execution_service = ExecutionService()


def start_consumer():

    for message in consumer:

        data = message.value

        if message.topic == "stock_prices":

                instrument_id = data["ticker"]

                current_price = data["price"]

        else:

                instrument_id = data["option_id"]

                current_price = data["premium"]


        trades = execution_service.execute_tick(
            instrument_id=instrument_id,
            current_price=current_price,
        )

        print("TRADES:", trades)

if __name__ == "__main__":
    Database.init_pool()
    start_consumer()