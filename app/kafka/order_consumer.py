import json
import os
from decimal import Decimal
from datetime import datetime

from kafka import KafkaConsumer

from app.order import Order, OrderType, Side
from app.order_submission_service import OrderSubmissionService
from app.repositories.order_repository import OrderRepository


def start_order_consumer():
    order_repo = OrderRepository()
    submission_service = OrderSubmissionService(order_repo)

    consumer = KafkaConsumer(
        "orders.requests",
        bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="order-book-engine-orders",
    )

    print("[order-consumer] listening on orders.requests")

    for message in consumer:
        try:
            data = message.value

            order = Order(
                order_id=data["order_id"],
                platform_id=data.get("platform_id", "unknown"),
                platform_user_id=data["platform_user_id"],
                instrument_type=data["instrument_type"],
                instrument_id=data["instrument_id"],
                order_type=OrderType(data["order_type"]),
                side=Side(data["side"]),
                quantity=Decimal(str(data["quantity"])),
                limit_price=Decimal(str(data["limit_price"]))
                if data.get("limit_price") is not None
                else None,
                expires_at=datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None,
            )

            submission_service.submit_order(order)
            print(f"[order-consumer] submitted order {order.order_id} "
                  f"({order.side.value} {order.quantity} {order.instrument_id})")

        except Exception as e:
            print(f"[order-consumer] error processing order: {e}")
