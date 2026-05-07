from app.db import Database
from app.models.option import Option, OptionType
from decimal import Decimal


class OptionRepository:

    def insert(self, option):

        conn = Database.get_connection()

        try:
            with conn.cursor() as cur:

                cur.execute("""
                    INSERT INTO options (
                        option_id,
                        underlying_ticker,
                        option_type,
                        strike_price,
                        expiry_time,
                        premium,
                        is_active
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (
                    option.option_id,
                    option.underlying_ticker,
                    option.option_type.value,
                    option.strike_price,
                    option.expiry_time,
                    option.premium,
                    option.is_active
                ))

            conn.commit()

        finally:
            Database.release_connection(conn)



    def find_active_by_underlying(self, ticker):

        conn = Database.get_connection()

        try:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT
                        option_id,
                        underlying_ticker,
                        option_type,
                        strike_price,
                        expiry_time,
                        premium,
                        is_active
                    FROM options
                    WHERE underlying_ticker = %s
                    AND is_active = TRUE
                """, (ticker,))

                rows = cur.fetchall()

                result = []

                for r in rows:

                    result.append(
                        Option(
                            option_id=r[0],
                            underlying_ticker=r[1],
                            option_type=OptionType(r[2]),
                            strike_price=Decimal(str(r[3])),
                            expiry_time=r[4],
                            premium=Decimal(str(r[5])),
                            is_active=r[6]
                        )
                    )

                return result

        finally:
            Database.release_connection(conn)


    def update_premium(
        self,
        option_id,
        premium
    ):

        conn = Database.get_connection()

        try:
            with conn.cursor() as cur:

                cur.execute("""
                    UPDATE options
                    SET premium = %s
                    WHERE option_id = %s
                """, (
                    premium,
                    option_id
                ))

            conn.commit()

        finally:
            Database.release_connection(conn)

    def find_all_active(self):

        conn = Database.get_connection()

        try:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT
                        option_id,
                        underlying_ticker,
                        option_type,
                        strike_price,
                        expiry_time,
                        premium,
                        is_active
                    FROM options
                    WHERE is_active = TRUE
                """)

                rows = cur.fetchall()

                result = []

                for r in rows:

                    result.append(
                        Option(
                            option_id=r[0],
                            underlying_ticker=r[1],
                            option_type=OptionType(r[2]),
                            strike_price=Decimal(str(r[3])),
                            expiry_time=r[4],
                            premium=Decimal(str(r[5])),
                            is_active=r[6]
                        )
                    )

                return result

        finally:
            Database.release_connection(conn)


    def find_by_id(self, option_id):

        conn = Database.get_connection()

        try:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT
                        option_id,
                        underlying_ticker,
                        option_type,
                        strike_price,
                        expiry_time,
                        premium,
                        is_active
                    FROM options
                    WHERE option_id = %s
                """, (
                    option_id,
                ))

                row = cur.fetchone()

                if not row:
                    return None

                return Option(
                    option_id=row[0],
                    underlying_ticker=row[1],
                    option_type=OptionType(row[2]),
                    strike_price=Decimal(str(row[3])),
                    expiry_time=row[4],
                    premium=Decimal(str(row[5])),
                    is_active=row[6]
                )

        finally:
            Database.release_connection(conn)