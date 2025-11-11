def create_table(conn):
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
    cursor = conn.cursor()
    cursor.execute(create_sql)
    conn.commit()

def insert_rows(conn, rows):
    insert_sql = """
    INSERT INTO SensorData (sensor_id, temperature, wind, humidity, co2_level)
    VALUES (?, ?, ?, ?, ?)
    """
    params = [(r["sensor_id"], r["temperature"], r["wind"], r["humidity"], r["co2_level"]) for r in rows]
    cursor = conn.cursor()
    cursor.fast_executemany = True
    cursor.executemany(insert_sql, params)
    conn.commit()
    return len(params)

def get_rows(conn, sensor_id=0, page=1, page_size=50):
    offset = (page - 1) * page_size
    if sensor_id == 0:
        query_sql = f"""
            SELECT id, sensor_id, temperature, wind, humidity, co2_level, server_ts
            FROM SensorData
            ORDER BY server_ts DESC
            OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY;
        """
        params = ()
    else:
        query_sql = f"""
            SELECT id, sensor_id, temperature, wind, humidity, co2_level, server_ts
            FROM SensorData
            WHERE sensor_id = ?
            ORDER BY server_ts DESC
            OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY;
        """
        params = (sensor_id,)

    cursor = conn.cursor()
    cursor.execute(query_sql, params)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def clear_table(conn):
    delete_sql = "DELETE FROM SensorData"
    cursor = conn.cursor()
    cursor.execute(delete_sql)
    conn.commit()
    return cursor.rowcount
