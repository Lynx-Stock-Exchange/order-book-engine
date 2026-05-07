from datetime import datetime
from app.kafka.producer import publish

from app.db import Database


class OptionExpiryService:

    def expire_options(self):

        conn = Database.get_connection()

        try:
            with conn.cursor() as cur:

                cur.execute("""
                    UPDATE options
                    SET is_active = FALSE
                    WHERE expiry_time <= %s
                """, (
                    datetime.utcnow(),
                ))

            expired_count = cur.rowcount

            conn.commit()

            if expired_count > 0:

                publish("option_expired", {
                    "type": "OPTION_EXPIRED",
                    "expired_count": expired_count
                })

        finally:
            Database.release_connection(conn)