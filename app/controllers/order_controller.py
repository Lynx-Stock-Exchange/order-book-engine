from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)
from uuid import uuid4
from decimal import Decimal
from datetime import datetime
from app.order_book import OrderBook
from app.order_book_service import OrderBookService
from app.repositories.trade_repository import TradeRepository
from app.market_stats_service import MarketStatsService

from app.order import (
    Order,
    OrderType,
    Side,
)

from app.repositories.order_repository import OrderRepository
from app.order_submission_service import OrderSubmissionService
from app.errors import OrderRejected
from app.auth import get_platform_id
from app.kafka.producer import publish

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
def create_order(
    payload: dict,
    platform_id: str = Depends(get_platform_id),
):
    order = Order(
        order_id=str(uuid4()),
        platform_id=platform_id,
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
        client_order_id=payload.get("client_order_id"),
    )

    result = submission_service.submit_order(order)

    if result.get("status") == "DUPLICATE":
        existing = order_repo.find_by_order_id(result["order_id"])
        return {
            "order_id": existing.order_id,
            "client_order_id": existing.client_order_id,
            "status": "DUPLICATE",
        }

    return {
        "order_id": order.order_id,
        "client_order_id": order.client_order_id,
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
def get_orders(
    platform_id: str = Depends(get_platform_id),
    platform_user_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    from datetime import datetime as dt

    orders = order_repo.find_orders(
        platform_id=platform_id,
        platform_user_id=platform_user_id,
        status=status,
        from_date=dt.fromisoformat(from_date) if from_date else None,
        to_date=dt.fromisoformat(to_date) if to_date else None,
        page=page,
        page_size=page_size,
    )

    return [
        {
            "order_id": order.order_id,
            "platform_id": order.platform_id,
            "platform_user_id": order.platform_user_id,
            "instrument_type": order.instrument_type,
            "instrument_id": order.instrument_id,
            "order_type": order.order_type,
            "side": order.side,
            "quantity": str(order.quantity),
            "limit_price": str(order.limit_price) if order.limit_price else None,
            "status": order.status,
            "filled_quantity": str(order.filled_quantity),
            "average_fill_price": str(order.average_fill_price) if order.average_fill_price else None,
            "exchange_fee": str(order.exchange_fee),
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "expires_at": order.expires_at.isoformat() if order.expires_at else None,
        }
        for order in orders
    ]


@router.get("/orders/{order_id}")
def get_order(
    order_id: str,
    platform_id: str = Depends(get_platform_id),
):
    order = order_repo.find_by_order_id(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.platform_id != platform_id:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order.order_id,
        "platform_id": order.platform_id,
        "platform_user_id": order.platform_user_id,
        "status": order.status,
        "instrument_id": order.instrument_id,
        "instrument_type": order.instrument_type,
        "side": order.side,
        "quantity": str(order.quantity),
        "filled_quantity": str(order.filled_quantity),
        "average_fill_price": str(order.average_fill_price) if order.average_fill_price is not None else None,
        "exchange_fee": str(order.exchange_fee),
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "expires_at": order.expires_at.isoformat() if order.expires_at else None,
    }


@router.delete("/orders/{order_id}")
def cancel_order(
    order_id: str,
    platform_id: str = Depends(get_platform_id),
):
    order = order_repo.find_by_order_id(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.platform_id != platform_id:
        raise HTTPException(status_code=404, detail="Order not found")

    book_service.cancel_order(order_id)

    return {
        "status": "CANCELLED",
        "order_id": order_id,
    }


@router.get("/market/stats")
def get_market_stats():
    return MarketStatsService.get_market_stats()
