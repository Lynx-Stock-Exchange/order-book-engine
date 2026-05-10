import os
import glob
from app.db import Database


def run_migrations():
    migration_dir = os.path.dirname(__file__)

    # Run all V*.sql files in version order
    pattern = os.path.join(migration_dir, "V*.sql")
    migration_files = sorted(glob.glob(pattern))

    Database.init_pool()
    conn = Database.get_connection()

    try:
        for migration_path in migration_files:
            filename = os.path.basename(migration_path)
            with open(migration_path, "r") as f:
                sql = f.read()
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print(f"Migration applied: {filename}")

    finally:
        Database.release_connection(conn)


if __name__ == "__main__":
    run_migrations()
