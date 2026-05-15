import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.controllers.order_controller import router as order_router
from app.controllers.admin_controller import router as admin_router

from app.db import Database

from app.errors import OrderRejected
from app.exception_handlers import order_rejected_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.migrations.run_migration import run_migrations
    run_migrations()
    from app.kafka.consumer import start_consumer
    from app.kafka.admin_consumer import start_admin_consumer
    from app.kafka.order_consumer import start_order_consumer
    threading.Thread(target=start_consumer, daemon=True).start()
    threading.Thread(target=start_admin_consumer, daemon=True).start()
    threading.Thread(target=start_order_consumer, daemon=True).start()
    yield


app = FastAPI(lifespan=lifespan)

Database.init_pool()

app.add_exception_handler(
    OrderRejected,
    order_rejected_handler
)

app.include_router(order_router)
app.include_router(admin_router)