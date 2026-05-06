from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.db import Database
from app.models.order import Order


class OrderRepository:

    def insert(self, order: Order) -> None:
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO orders (
                        order_id, platform_id, platform_user_id,
                        instrument_type, instrument_id, order_type,
                        side, quantity, limit_price, status,
                        filled_quantity, average_fill_price,
                        exchange_fee, created_at, updated_at, expires_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                """, (
                    order.order_id, order.platform_id, order.platform_user_id,
                    order.instrument_type, order.instrument_id, order.order_type,
                    order.side, order.quantity, order.limit_price, order.status,
                    order.filled_quantity, order.average_fill_price,
                    order.exchange_fee, order.created_at, order.updated_at,
                    order.expires_at
                ))
            conn.commit()
        finally:
            Database.release_connection(conn)

    def find_by_order_id(self, order_id: str) -> Optional[Order]:
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT order_id, platform_id, platform_user_id,
                           instrument_type, instrument_id, order_type,
                           side, quantity, limit_price, status,
                           filled_quantity, average_fill_price,
                           exchange_fee, created_at, updated_at, expires_at
                    FROM orders
                    WHERE order_id = %s
                """, (order_id,))
                row = cur.fetchone()
                return self._map_row(row) if row else None
        finally:
            Database.release_connection(conn)

    def find_open_by_ticker(self, instrument_id: str) -> list[Order]:
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT order_id, platform_id, platform_user_id,
                           instrument_type, instrument_id, order_type,
                           side, quantity, limit_price, status,
                           filled_quantity, average_fill_price,
                           exchange_fee, created_at, updated_at, expires_at
                    FROM orders
                    WHERE instrument_id = %s
                      AND status IN ('PENDING', 'PARTIALLY_FILLED')
                    ORDER BY created_at ASC
                """, (instrument_id,))
                return [self._map_row(row) for row in cur.fetchall()]
        finally:
            Database.release_connection(conn)

    def update_status(self, order_id: str, status: str,
                      filled_quantity: Optional[Decimal] = None,
                      average_fill_price: Optional[Decimal] = None,
                      exchange_fee: Optional[Decimal] = None) -> None:
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE orders
                    SET status = %s,
                        filled_quantity = COALESCE(%s, filled_quantity),
                        average_fill_price = COALESCE(%s, average_fill_price),
                        exchange_fee = COALESCE(%s, exchange_fee),
                        updated_at = NOW()
                    WHERE order_id = %s
                """, (status, filled_quantity, average_fill_price,
                      exchange_fee, order_id))
            conn.commit()
        finally:
            Database.release_connection(conn)

    def _map_row(self, row) -> Order:
        return Order(
            order_id=row[0],
            platform_id=row[1],
            platform_user_id=row[2],
            instrument_type=row[3],
            instrument_id=row[4],
            order_type=row[5],
            side=row[6],
            quantity=row[7],
            limit_price=row[8],
            status=row[9],
            filled_quantity=row[10],
            average_fill_price=row[11],
            exchange_fee=row[12],
            created_at=row[13],
            updated_at=row[14],
            expires_at=row[15]
        )