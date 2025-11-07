# utils/db.py
import os
import pyodbc
import logging
from contextlib import contextmanager

CONN_STR = os.getenv("SQL_CONNECTION_STRING")

if not CONN_STR:
    logging.warning("SQL_CONNECTION_STRING not set in environment.")

_conn = None

@contextmanager
def get_conn():
    global _conn
    try:
        if _conn is None:
            logging.info("Creating DB connection...")
            _conn = pyodbc.connect(CONN_STR, autocommit=False, timeout=30)
        yield _conn
    except Exception as e:
        logging.error(f"DB connection failed: {e}")
        raise

# 检查是否有表，没有则创建
def create_table():
    create_sql = """
    IF OBJECT_ID('SensorData', 'U') IS NULL
    CREATE TABLE SensorData (
      id BIGINT IDENTITY(1,1) PRIMARY KEY,
      sensor_id INT NOT NULL,
      temperature INT NOT NULL,
      wind INT NOT NULL,
      humidity INT NOT NULL,
      co2_level INT NOT NULL,
      server_ts DATETIME2 DEFAULT (SYSUTCDATETIME())
    )
    """
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(create_sql)
        conn.commit()

def insert_rows(rows):
    insert_sql = """
    INSERT INTO SensorData (sensor_id, temperature, wind, humidity, co2_level)
    VALUES (?, ?, ?, ?, ?)
    """
    params = [(r["sensor_id"], r["temperature"], r["wind"], r["humidity"], r["co2_level"]) for r in rows]
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.fast_executemany = True
        cursor.executemany(insert_sql, params)
        conn.commit()
    return len(params)

def get_rows(sensor_id=0, page=1, page_size=50) -> list[dict]:

    offset = (page - 1) * page_size

    if sensor_id == 0:
        query_sql = f"""
            SELECT id, sensor_id, temperature, wind, humidity, co2_level, server_ts
            FROM SensorData
            ORDER BY server_ts DESC
            OFFSET {offset} ROWS
            FETCH NEXT {page_size} ROWS ONLY;
        """
        params = ()
    else:
        query_sql = f"""
            SELECT id, sensor_id, temperature, wind, humidity, co2_level, server_ts
            FROM SensorData
            WHERE sensor_id = ?
            ORDER BY server_ts DESC
            OFFSET {offset} ROWS
            FETCH NEXT {page_size} ROWS ONLY;
        """
        params = (sensor_id,)

    rows = []
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query_sql, params)
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            rows.append(dict(zip(columns, row)))

    return rows

def clear_table():
    delete_sql = "DELETE FROM SensorData"
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(delete_sql)
        conn.commit()

    return cursor.rowcount
        