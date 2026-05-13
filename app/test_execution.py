from datetime import datetime
from decimal import Decimal

from app.db import Database
from app.execution_service import ExecutionService

from app.models.order import Order
from app.repositories.order_repository import OrderRepository


Database.init_pool()

order_repo = OrderRepository()

# --- TEST BUY ORDER ---
buy_order = Order(
    order_id="buy-1",
    platform_id="platform-1",
    platform_user_id="user-1",
    instrument_type="STOCK",
    instrument_id="AAPL",
    order_type="LIMIT",
    side="BUY",
    quantity=Decimal("100"),
    limit_price=Decimal("130"),
    status="PENDING",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
)

# --- TEST SELL ORDER ---
sell_order = Order(
    order_id="sell-1",
    platform_id="platform-1",
    platform_user_id="user-2",
    instrument_type="STOCK",
    instrument_id="AAPL",
    order_type="LIMIT",
    side="SELL",
    quantity=Decimal("50"),
    limit_price=Decimal("129"),
    status="PENDING",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
)

# --- SAVE TO DB ---
order_repo.insert(buy_order)
order_repo.insert(sell_order)

# --- EXECUTE ---
service = ExecutionService()

trades = service.execute_tick(
    instrument_id="AAPL",
    current_price=129
)

print("\nTRADES:")
for t in trades:
    print(t)