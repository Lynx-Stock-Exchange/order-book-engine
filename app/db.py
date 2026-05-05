from psycopg2 import pool
from app.config import Config

class Database:
    _pool = None

    @classmethod
    def init_pool(cls):
        if cls._pool is None:
            cls._pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                dbname=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
            )

    @classmethod
    def get_connection(cls):
        if cls._pool is None:
            raise Exception("Connection pool not initialized")
        return cls._pool.getconn()

    @classmethod
    def release_connection(cls, conn):
        if cls._pool:
            cls._pool.putconn(conn)

    @classmethod
    def close_all(cls):
        if cls._pool:
            cls._pool.closeall()