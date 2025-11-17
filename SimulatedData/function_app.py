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

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
logger = logging.getLogger("azure")
logger.setLevel(logging.INFO)

_db_conn = None
_CONN_STR = os.getenv("SQL_CONNECTION_STRING")


# Obtain the global database connection
def get_global_conn():
    global _db_conn

    if not _CONN_STR:
        raise RuntimeError("Environment variable SQL_CONNECTION_STRING not set")

    try:
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


simulator = SensorData() 

@app.route(route="generate_sensor_data")
def generate_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    ensure_table_exists()
    conn = get_global_conn()

    logger.info("Generating simulated IoT sensor data...")
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

@app.route(route="performance_test")
def performance_test(req: func.HttpRequest) -> func.HttpResponse:
    ensure_table_exists()
    conn = get_global_conn()

    sample_batch = simulator.generate_all()
    batch_size = len(sample_batch)
    logger.info(f"Detected batch size = {batch_size}")

    call_counts = [1, 5, 10, 20, 40, 60, 80, 100]
    seq_results = []

    for n_calls in call_counts:
        start = time.time()
        inserted = 0
        try:
            for _ in range(n_calls):
                data = simulator.generate_all()
                inserted += insert_rows(conn, data)
            conn.commit()
        except Exception as e:
            logger.error(f"Error during sequential inserts: {e}")
            try:
                conn.rollback()
            except Exception:
                pass
        total_time = time.time() - start
        total_data = n_calls * batch_size
        throughput = total_data / total_time if total_time > 0 else 0

        seq_results.append(
            {
                "calls": n_calls,
                "total_data": total_data,
                "total_time": total_time,
                "avg_time_per_call": total_time / n_calls if n_calls else None,
                "throughput_rows_per_s": throughput,
                "rows_inserted": inserted,
            }
        )
        logger.info(f"Seq {n_calls} calls -> {total_data} rows: {total_time:.2f}s, {throughput:.2f} rows/s")


    x_seq = [r["total_data"] for r in seq_results]
    y_seq_time = [r["total_time"] for r in seq_results]
    y_seq_tp = [r["throughput_rows_per_s"] for r in seq_results]

    fig, ax_time = plt.subplots(figsize=(9, 5))

    ax_time.plot(x_seq, y_seq_time, marker='o', label='Total time (s)')
    ax_time.set_xlabel("Total data inserted (rows)")
    ax_time.set_ylabel("Total time (s)")
    ax_time.grid(True)

    ax_tp = ax_time.twinx()
    ax_tp.plot(x_seq, y_seq_tp, marker='x', linestyle='--', label='Throughput (rows/s)')
    ax_tp.set_ylabel("Throughput (rows/s)")

    lines_time, labels_time = ax_time.get_legend_handles_labels()
    lines_tp, labels_tp = ax_tp.get_legend_handles_labels()
    ax_time.legend(lines_time + lines_tp, labels_time + labels_tp, loc='best')

    ax_time.set_title("Data Scalability: time & throughput vs total rows")

    plt.tight_layout()

    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format="png")
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode()

    return func.HttpResponse(
        json.dumps(
            {
                "status": "success",
                "data_scalability_results": seq_results,
                "image_base64": img_base64,
            },
            indent=2,
            default=str,
        ),
        mimetype="application/json",
        status_code=200,
    )
