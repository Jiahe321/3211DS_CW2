import azure.functions as func
import logging
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from utils.SensorData import SensorData
from utils.db import create_table, insert_rows, get_rows, clear_table

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# 确保表存在
create_table()

# ----------------------------------------------------------
# 生成并插入数据
# ----------------------------------------------------------
@app.route(route="generate_sensor_data")
def generate_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Generating simulated IoT sensor data...')

    simulator = SensorData()
    data_dicts = simulator.generate_all()

    try:
        rows_inserted = insert_rows(data_dicts)
        logging.info(f"Inserted {rows_inserted} rows into the database.")
        return func.HttpResponse(
            json.dumps({"status": "success", "rows_inserted": rows_inserted}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error inserting data into database: {e}")
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
    try:
        sensor_id = int(req.params.get("sensor_id", 0))
        page = int(req.params.get("page", 1))
        page_size = int(req.params.get("page_size", 50))

        rows = get_rows(sensor_id=sensor_id, page=page, page_size=page_size)

        return func.HttpResponse(
            json.dumps({
                "page": page,
                "page_size": page_size,
                "rows_returned": len(rows),
                "data": rows
            }, default=str, indent=2),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
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
    try:
        cleared = clear_table()
        return func.HttpResponse(
            json.dumps({"status": "success", "rows_deleted": cleared}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error clearing table: {e}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )
