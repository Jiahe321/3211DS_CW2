# function_app.py
import azure.functions as func
import logging
import json
import os
import time
import pyodbc
import matplotlib.pyplot as plt
import io
import base64

from utils.SensorData import SensorData
from utils.db import create_table, insert_rows, get_rows, clear_table

# ----------------------------------------
# 基础配置
# ----------------------------------------
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
logger = logging.getLogger("azure")
logger.setLevel(logging.INFO)

# ----------------------------------------
# 全局数据库连接缓存
# ----------------------------------------
_db_conn = None
_CONN_STR = os.getenv("SQL_CONNECTION_STRING")


# 获取全局数据库连接
def get_global_conn():
    global _db_conn

    if not _CONN_STR:
        raise RuntimeError("Environment variable SQL_CONNECTION_STRING not set")

    try:
        # 如果已有连接，尝试验证
        if _db_conn is not None:
            cursor = _db_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()
            return _db_conn
    except Exception as e:
        logger.warning(f"DB connection invalid, reconnecting... ({e})")
        _db_conn = None

    try:
        logger.info("Creating new persistent DB connection...")
        _db_conn = pyodbc.connect(_CONN_STR, autocommit=False, timeout=30)
        logger.info("DB connection established successfully.")
    except Exception as e:
        logger.error(f"Failed to create DB connection: {e}")
        raise

    return _db_conn


# ----------------------------------------
# 初始化数据表（仅执行一次）
# ----------------------------------------
_table_created = False


def ensure_table_exists():
    global _table_created
    if not _table_created:
        try:
            conn = get_global_conn()
            create_table(conn)
            _table_created = True
            logger.info("SensorData table ensured.")
        except Exception as e:
            logger.warning(f"Skipping table creation (may already exist): {e}")


# ----------------------------------------
# 路由：生成并插入数据
# ----------------------------------------
@app.route(route="generate_sensor_data")
def generate_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    ensure_table_exists()
    conn = get_global_conn()

    logger.info("Generating simulated IoT sensor data...")
    simulator = SensorData()
    data_dicts = simulator.generate_all()

    try:
        rows_inserted = insert_rows(conn, data_dicts)
        logger.info(f"Inserted {rows_inserted} rows into the database.")
        return func.HttpResponse(
            json.dumps({"status": "success", "rows_inserted": rows_inserted}),
            mimetype="application/json",
            headers={"Cache-Control": "no-store"},
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error inserting data: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


# ----------------------------------------
# 路由：查询数据
# ----------------------------------------
@app.route(route="get_sensor_data")
def get_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    ensure_table_exists()
    conn = get_global_conn()

    try:
        sensor_id = int(req.params.get("sensor_id", 0))
        page = int(req.params.get("page", 1))
        page_size = int(req.params.get("page_size", 20))
        rows = get_rows(conn, sensor_id=sensor_id, page=page, page_size=page_size)

        response = {
            "page": page,
            "page_size": page_size,
            "rows_returned": len(rows),
            "data": rows,
        }

        return func.HttpResponse(
            json.dumps(response, default=str),
            mimetype="application/json",
            headers={"Cache-Control": "no-store"},
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


# ----------------------------------------
# 路由：清空数据库
# ----------------------------------------
@app.route(route="clear_sensor_data")
def clear_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    ensure_table_exists()
    conn = get_global_conn()

    try:
        cleared = clear_table(conn)
        return func.HttpResponse(
            json.dumps({"status": "success", "rows_deleted": cleared}),
            mimetype="application/json",
            headers={"Cache-Control": "no-store"},
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error clearing table: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


# ----------------------------------------
# 路由：性能测试
# ----------------------------------------
@app.route(route="performance_test")
def performance_test(req: func.HttpRequest) -> func.HttpResponse:
    ensure_table_exists()
    conn = get_global_conn()

    simulator = SensorData()
    call_counts = [1, 5, 10, 20, 40]
    results = []

    for n_calls in call_counts:
        start = time.time()
        for _ in range(n_calls):
            data = simulator.generate_all()
            insert_rows(conn, data)
        total_time = time.time() - start
        avg_time = total_time / n_calls
        total_data = n_calls * 20  # 每批20条

        results.append(
            {
                "calls": n_calls,
                "total_data": total_data,
                "total_time": total_time,
                "avg_time": avg_time,
            }
        )
        logger.info(f"{n_calls} calls: {total_time:.2f}s total, {avg_time:.2f}s/call")

    # 绘制结果图
    x = [r["total_data"] for r in results]
    y = [r["total_time"] for r in results]
    plt.figure(figsize=(7, 5))
    plt.plot(x, y, marker="o", color="royalblue")
    plt.xlabel("Total data inserted")
    plt.ylabel("Total time (s)")
    plt.title("Internal Scalability Test (Azure Function)")
    plt.grid(True)

    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format="png")
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode()

    return func.HttpResponse(
        json.dumps({"status": "success", "results": results, "image_base64": img_base64}, indent=2),
        mimetype="application/json",
        status_code=200,
    )
