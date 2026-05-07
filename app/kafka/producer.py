import json
import os
from kafka import KafkaProducer

_producer = None


def _get_producer():
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    return _producer


def publish(topic, payload):
    producer = _get_producer()
    producer.send(topic, payload)
    producer.flush()