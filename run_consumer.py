from app.db import Database
from app.kafka.consumer import start_consumer

Database.init_pool()

start_consumer()