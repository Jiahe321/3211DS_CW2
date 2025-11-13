import json
import logging
import azure.functions as func
import requests
import os

app = func.FunctionApp()

STATISTICS_DATA_URL = os.getenv("STATISTICS_FUNCTION_URL")
@app.function_name(name="SensorSQLTrigger")
@app.sql_trigger(
    arg_name="changes",
    table_name="SensorData",
    connection_string_setting="SQL_CONNECTION_STRING"
)
def sensor_trigger(changes: str) -> None:
    try:
        data = json.loads(changes)
        count = len(data)

        if count > 0:
            logging.info(f"数据库变动！共检测到 {count} 条变动。")

            response = requests.get(STATISTICS_DATA_URL)
            logging.info(f"Fetched simulated data: {response.status_code} - {response.text}")    
        else:
            logging.info("数据库变动，但没有新行。")
    except Exception as e:
        logging.error(f"处理 SQL 触发数据时出错: {e}")