from fastapi import FastAPI

from app.controllers.order_controller import router as order_router
from app.controllers.admin_controller import router as admin_router

from app.db import Database

from app.errors import OrderRejected
from app.exception_handlers import order_rejected_handler
from app.controllers.option_controller import (
    router as option_router
)

app = FastAPI()

Database.init_pool()

app.add_exception_handler(
    OrderRejected,
    order_rejected_handler
)

app.include_router(order_router)
app.include_router(admin_router)
app.include_router(option_router)