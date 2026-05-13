import json
import os
from decimal import Decimal, InvalidOperation

from kafka import KafkaConsumer

from app.fee_rate import set_fee_rate


def start_admin_consumer():
    consumer = KafkaConsumer(
        "admin.commands",
        bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="order-book-engine-admin",
    )

    for message in consumer:
        try:
            data = message.value
            action = str(data.get("action", "")).upper()

            if action == "UPDATE_FEE":
                raw = data.get("fee_rate")
                if raw is None:
                    print("[admin_consumer] UPDATE_FEE missing fee_rate field, skipping")
                    continue
                try:
                    new_rate = Decimal(str(raw))
                    set_fee_rate(new_rate)
                    print(f"[admin_consumer] Fee rate updated to {new_rate}")
                except InvalidOperation:
                    print(f"[admin_consumer] Invalid fee_rate value: {raw}")

        except Exception as e:
            print(f"[admin_consumer] Error processing admin command: {e}")
