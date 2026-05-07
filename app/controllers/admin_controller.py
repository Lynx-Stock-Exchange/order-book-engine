from fastapi import APIRouter
from app.market_state import MarketState
from app.order_book import OrderBook
from app.order_book_service import OrderBookService
from app.repositories.order_repository import OrderRepository
from app.repositories.trade_repository import TradeRepository
from app.kafka.producer import publish
from datetime import datetime

router = APIRouter(prefix="/admin")

order_repo = OrderRepository()
trade_repo = TradeRepository()

book_service = OrderBookService(
    OrderBook("GLOBAL"),
    order_repo,
    trade_repo
)


@router.post("/market/open")
def open_market():

    MarketState.open_market()

    return {
        "market_open": True
    }


@router.post("/market/close")
def close_market():

    MarketState.close_market()

    result = book_service.handle_market_close()

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