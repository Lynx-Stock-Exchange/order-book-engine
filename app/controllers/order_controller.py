from fastapi import APIRouter, HTTPException, Body
from uuid import uuid4
from decimal import Decimal
from datetime import datetime
from app.order_book import OrderBook
from app.order_book_service import OrderBookService
from app.repositories.trade_repository import TradeRepository

from app.order import (
    Order,
    OrderType,
    Side,
)

from app.repositories.order_repository import OrderRepository
from app.order_submission_service import OrderSubmissionService
from app.errors import OrderRejected

router = APIRouter()

order_repo = OrderRepository()
submission_service = OrderSubmissionService(order_repo)

trade_repo = TradeRepository()

dummy_book = OrderBook("GLOBAL")

book_service = OrderBookService(
    dummy_book,
    order_repo,
    trade_repo
)


@router.post("/orders")
def create_order(payload: dict = Body(...)):


        order = Order(
            order_id=str(uuid4()),
            platform_id=payload.get("platform_id", "demo-platform"),
            platform_user_id=payload["platform_user_id"],
            instrument_type=payload["instrument_type"],
            instrument_id=payload["instrument_id"],
            order_type=OrderType(payload["order_type"]),
            side=Side(payload["side"]),
            quantity=Decimal(str(payload["quantity"])),
            limit_price=Decimal(str(payload["limit_price"]))
            if payload.get("limit_price") is not None
            else None,
            expires_at=datetime.fromisoformat(payload["expires_at"])
            if payload.get("expires_at")
            else None,
        )

        submission_service.submit_order(order)

        return {
            "order_id": order.order_id,
            "platform_id": order.platform_id,
            "platform_user_id": order.platform_user_id,
            "instrument_type": order.instrument_type,
            "instrument_id": order.instrument_id,

            "order_type": (
                order.order_type.value
                if hasattr(order.order_type, "value")
                else order.order_type
            ),

            "side": (
                order.side.value
                if hasattr(order.side, "value")
                else order.side
            ),

            "quantity": str(order.quantity),

            "limit_price": (
                str(order.limit_price)
                if order.limit_price is not None
                else None
            ),

            "status": (
                order.status.value
                if hasattr(order.status, "value")
                else order.status
            ),

            "filled_quantity": str(order.filled_quantity),

            "average_fill_price": (
                str(order.average_fill_price)
                if order.average_fill_price is not None
                else None
            ),

            "exchange_fee": str(order.exchange_fee),

            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),

            "expires_at": (
                order.expires_at.isoformat()
                if order.expires_at is not None
                else None
            )
        }

    

@router.get("/orders")
def list_orders(status: str = "FILLED"):
    orders = order_repo.find_by_status(status.upper())
    return [
        {
            "order_id": o.order_id,
            "platform_id": o.platform_id,
            "platform_user_id": o.platform_user_id,
            "instrument_type": o.instrument_type,
            "instrument_id": o.instrument_id,
            "side": o.side,
            "filled_quantity": int(o.filled_quantity) if o.filled_quantity is not None else 0,
            "average_fill_price": float(o.average_fill_price) if o.average_fill_price is not None else None,
            "exchange_fee": float(o.exchange_fee) if o.exchange_fee is not None else 0.0,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at is not None else None,
        }
        for o in orders
    ]


@router.get("/orders/{order_id}")
def get_order(order_id: str):

    order = order_repo.find_by_order_id(order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return {
        "order_id": order.order_id,
        "status": order.status,
        "instrument_id": order.instrument_id,
        "instrument_type": order.instrument_type,
        "side": order.side,
        "quantity": str(order.quantity),
        "filled_quantity": str(order.filled_quantity),
        "average_fill_price": str(order.average_fill_price)
        if order.average_fill_price is not None
        else None,
    }

@router.delete("/orders/{order_id}")
def cancel_order(order_id: str):

    book_service.cancel_order(order_id)

    return {
        "status": "CANCELLED",
        "order_id": order_id
    }