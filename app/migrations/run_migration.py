import os
from app.db import Database


def run_migrations():
    migration_path = os.path.join(os.path.dirname(__file__), "V1__create_orders_and_trades.sql")
    with open(migration_path, "r") as f:
        sql = f.read()

    Database.init_pool()
    conn = Database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("Migration ran successfully.")
    finally:
        Database.release_connection(conn)


if __name__ == "__main__":
    run_migrations()