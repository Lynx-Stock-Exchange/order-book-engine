from fastapi import APIRouter
from app.market_state import MarketState
from app.order_book import OrderBook
from app.order_book_service import OrderBookService
from app.repositories.order_repository import OrderRepository
from app.repositories.trade_repository import TradeRepository
from app.kafka.producer import publish
from datetime import datetime
from decimal import Decimal
from datetime import datetime

from app.models.option import (
    Option,
    OptionType
)

from app.repositories.option_repository import (
    OptionRepository
)

router = APIRouter(prefix="/admin")

order_repo = OrderRepository()
trade_repo = TradeRepository()
option_repo = OptionRepository()

book_service = OrderBookService(
    OrderBook("GLOBAL"),
    order_repo,
    trade_repo
)


@router.post("/market/open")
def open_market():

    MarketState.open_market()

    publish("market_events", {
        "type": "MARKET_OPENED",
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {
        "market_open": True
    }


@router.post("/market/close")
def close_market():

    MarketState.close_market()

    result = book_service.handle_market_close()

    publish("market_events", {
        "type": "MARKET_CLOSED",
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {
        "market_open": False,
        "expired_orders": result["expired"],
        "rejected_orders": result["rejected"]
    }


@router.get("/market/status")
def market_status():

    return {
        "is_open": MarketState.is_open,
        "market_time": datetime.utcnow().isoformat(),
        "real_time": datetime.utcnow().isoformat(),
        "speed_multiplier": 60,
        "active_event": None
    }

@router.post("/events/trigger")
def trigger_event(payload: dict):

    publish("market_events", payload)

    return {
        "status": "EVENT_TRIGGERED",
        "event": payload
    }

@router.post("/options")
def create_option(payload: dict):

    option = Option(
        option_id=payload["option_id"],

        underlying_ticker=payload[
            "underlying_ticker"
        ],

        option_type=OptionType(
            payload["option_type"]
        ),

        strike_price=Decimal(
            str(payload["strike_price"])
        ),

        expiry_time=datetime.fromisoformat(
            payload["expiry_time"]
        ),

        premium=Decimal(
            str(payload["premium"])
        ),
    )

    option_repo.insert(option)

    return {
        "status": "CREATED",
        "option_id": option.option_id,
        "underlying_ticker": option.underlying_ticker,
        "option_type": option.option_type.value,
        "strike_price": str(option.strike_price),
        "expiry_time": option.expiry_time.isoformat(),
        "premium": str(option.premium),
        "is_active": option.is_active,
        "auto_exercise": option.auto_exercise,
        "option_id": option.option_id
    }

@router.post("/market/tick")
def trigger_tick(payload: dict):

    publish("stock.prices", payload)

    return {
        "status": "PUBLISHED",
        "payload": payload
    }