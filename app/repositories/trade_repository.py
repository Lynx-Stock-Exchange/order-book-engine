from app.db import Database
from app.models.trade import Trade


class TradeRepository:

    def insert(self, trade: Trade) -> None:
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO trades (
                        trade_id, order_id, platform_id, platform_user_id,
                        instrument_type, instrument_id, side,
                        quantity, price, exchange_fee, executed_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    trade.trade_id, trade.order_id, trade.platform_id,
                    trade.platform_user_id, trade.instrument_type,
                    trade.instrument_id, trade.side, trade.quantity,
                    trade.price, trade.exchange_fee, trade.executed_at
                ))
            conn.commit()
        finally:
            Database.release_connection(conn)

    def find_by_order_id(self, order_id: str) -> list[Trade]:
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT trade_id, order_id, platform_id, platform_user_id,
                           instrument_type, instrument_id, side,
                           quantity, price, exchange_fee, executed_at
                    FROM trades
                    WHERE order_id = %s
                    ORDER BY executed_at ASC
                """, (order_id,))
                return [self._map_row(row) for row in cur.fetchall()]
        finally:
            Database.release_connection(conn)

    def _map_row(self, row) -> Trade:
        return Trade(
            trade_id=row[0],
            order_id=row[1],
            platform_id=row[2],
            platform_user_id=row[3],
            instrument_type=row[4],
            instrument_id=row[5],
            side=row[6],
            quantity=row[7],
            price=row[8],
            exchange_fee=row[9],
            executed_at=row[10]
        )