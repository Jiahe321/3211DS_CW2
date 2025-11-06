# utils/db.py
import os
import pyodbc
import logging
from contextlib import contextmanager

CONN_STR = os.getenv("SQL_CONNECTION_STRING")

if not CONN_STR:
    logging.warning("SQL_CONNECTION_STRING not set in environment.")

@contextmanager
def get_conn():
    conn = None
    try:
        conn = pyodbc.connect(CONN_STR, autocommit=False, timeout=30)
        yield conn
    finally:
        if conn:
            conn.close()

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
        cursor.fast_executemany = True # 加速大量插入
        cursor.executemany(insert_sql, params)
        conn.commit()
    return len(params)

def get_rows(sensor_id=0) -> list[dict]:
    rows = []

    if sensor_id == 0:
        query_sql = """
            SELECT id, sensor_id, temperature, wind, humidity, co2_level, server_ts
            FROM SensorData
            ORDER BY server_ts DESC
        """
        params = ()
    else:
        query_sql = """
            SELECT id, sensor_id, temperature, wind, humidity, co2_level, server_ts
            FROM SensorData
            WHERE sensor_id = ?
            ORDER BY server_ts DESC
        """
        params = (sensor_id,)

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query_sql, params)
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()

    for row in data:
        rows.append(dict(zip(columns, row)))

    return rows


def clear_table():
    delete_sql = "DELETE FROM SensorData"
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(delete_sql)
        conn.commit()

    return cursor.rowcount
        
