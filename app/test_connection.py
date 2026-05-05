from app.db import Database

print("STARTING TEST...")

def main():
    try:
        print("Initializing pool...")
        Database.init_pool()

        print("Getting connection...")
        conn = Database.get_connection()

        print("Creating cursor...")
        cursor = conn.cursor()

        print("Executing query...")
        cursor.execute("SELECT 1;")

        result = cursor.fetchone()
        print("Connection OK:", result)

        cursor.close()
        Database.release_connection(conn)

    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()