from app.db import Database


class MarketState:
    is_open: bool = False  # in-memory cache; DB is the source of truth

    @classmethod
    def load_from_db(cls) -> None:
        """Read persisted market state from the DB on startup."""
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT is_open FROM market_state ORDER BY id LIMIT 1"
                )
                row = cur.fetchone()
                if row:
                    cls.is_open = row[0]
                else:
                    # No row yet — insert closed state as a safe default
                    cur.execute(
                        "INSERT INTO market_state (is_open) VALUES (FALSE)"
                    )
                    conn.commit()
                    cls.is_open = False
        finally:
            Database.release_connection(conn)

    @classmethod
    def open_market(cls) -> None:
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE market_state SET is_open = TRUE, updated_at = NOW()"
                )
            conn.commit()
        finally:
            Database.release_connection(conn)
        cls.is_open = True

    @classmethod
    def close_market(cls) -> None:
        conn = Database.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE market_state SET is_open = FALSE, updated_at = NOW()"
                )
            conn.commit()
        finally:
            Database.release_connection(conn)
        cls.is_open = False
