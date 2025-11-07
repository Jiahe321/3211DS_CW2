import azure.functions as func
import logging
import json
from utils.SensorData import SensorData
from utils.db import get_conn,create_table, insert_rows, get_rows, clear_table
import time
import matplotlib.pyplot as plt
import io
import base64

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
logger = logging.getLogger("azure")
logger.setLevel(logging.INFO)

_table_created = False

def ensure_table_exists():
    global _table_created
    if not _table_created:
        try:
            create_table()
            _table_created = True
            logger.info("SensorData table ensured.")
        except Exception as e:
            logger.warning(f"Skipping table creation (may already exist): {e}")

# ----------------------------------------------------------
# 生成并插入数据
# ----------------------------------------------------------
@app.route(route="generate_sensor_data")
def generate_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    ensure_table_exists()
    logger.info("Generating simulated IoT sensor data...")

    simulator = SensorData()
    data_dicts = simulator.generate_all()

    try:
        rows_inserted = insert_rows(data_dicts)
        logger.info(f"Inserted {rows_inserted} rows into the database.")
        return func.HttpResponse(
            json.dumps({"status": "success", "rows_inserted": rows_inserted}),
            mimetype="application/json",
            headers={"Cache-Control": "no-store"},
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error inserting data: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )


# ----------------------------------------------------------
# 查询数据库内容
# ----------------------------------------------------------
@app.route(route="get_sensor_data")
def get_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    ensure_table_exists()
    try:
        sensor_id = int(req.params.get("sensor_id", 0))
        page = int(req.params.get("page", 1))
        page_size = int(req.params.get("page_size", 20))
        rows = get_rows(sensor_id=sensor_id, page=page, page_size=page_size)

        response = {
            "page": page,
            "page_size": page_size,
            "rows_returned": len(rows),
            "data": rows
        }

        return func.HttpResponse(
            json.dumps(response, default=str),
            mimetype="application/json",
            headers={"Cache-Control": "no-store"},
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )


# ----------------------------------------------------------
# 清空数据库表
# ----------------------------------------------------------
@app.route(route="clear_sensor_data")
def clear_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    ensure_table_exists()
    try:
        cleared = clear_table()
        return func.HttpResponse(
            json.dumps({"status": "success", "rows_deleted": cleared}),
            mimetype="application/json",
            headers={"Cache-Control": "no-store"},
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error clearing table: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )

# 目前是顺序请求，之后考虑测并发？
@app.route(route="performance_test")
def performance_test(req: func.HttpRequest) -> func.HttpResponse:

    # 预热数据库连接
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.commit()

    simulator = SensorData()
    call_counts = [1, 5, 10, 20, 40]
    results = []

    for n_calls in call_counts:
        start = time.time()
        for _ in range(n_calls):
            data = simulator.generate_all()
            insert_rows(data)
        total_time = time.time() - start
        avg_time = total_time / n_calls
        total_data = n_calls * 20  # 每批20条

        results.append({
            "calls": n_calls,
            "total_data": total_data,
            "total_time": total_time,
            "avg_time": avg_time
        })
        print(f"{n_calls} calls: {total_time:.2f}s total, {avg_time:.2f}s/call")

    x = [r["total_data"] for r in results]
    y = [r["total_time"] for r in results]

    plt.figure(figsize=(7,5))
    plt.plot(x, y, marker='o', color='royalblue')
    plt.xlabel("Total data inserted")
    plt.ylabel("Total time (s)")
    plt.title("Internal Scalability Test (Azure Function)")
    plt.grid(True)

    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode()

    return func.HttpResponse(
        json.dumps({
            "status": "success",
            "results": results,
            "image_base64": img_base64
        }, indent=2),
        mimetype="application/json",
        status_code=200
    )
