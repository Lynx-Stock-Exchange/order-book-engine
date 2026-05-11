from app.db import Database


class MarketStatsService:

    @staticmethod
    def get_market_stats():

        conn = Database.get_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT
                        COALESCE(SUM(exchange_fee), 0),
                        COUNT(trade_id),
                        COALESCE(SUM(quantity), 0)
                    FROM trades
                """)

                row = cur.fetchone()

                total_revenue = row[0]
                total_trades = row[1]
                total_volume = row[2]

                return {
                    "total_revenue": str(total_revenue),
                    "total_trades": total_trades,
                    "total_volume": str(total_volume),
                }

        finally:
            Database.release_connection(conn)