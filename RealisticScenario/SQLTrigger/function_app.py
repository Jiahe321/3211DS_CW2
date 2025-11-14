import json
import logging
import azure.functions as func
import requests
import os

app = func.FunctionApp()

STATISTICS_DATA_URL = os.getenv("STATISTICS_FUNCTION_URL")

logging.info("function_app.py loaded successfully.")

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
            logging.info(f"DB changed! {count} line(s) affected.")

            if not STATISTICS_DATA_URL:
                logging.warning("STATISTICS_FUNCTION_URL not set. Skipping API call.")
            else:
                try:
                    # 设置 timeout，防止阻塞
                    response = requests.get(STATISTICS_DATA_URL, timeout=5)
                    logging.info(f"Fetched simulated data: {response.status_code} - {response.text}")
                except Exception as e:
                    logging.error(f"HTTP request failed: {e}")
        else:
            logging.info("DB changed! No lines affected.")

    except Exception as e:
        logging.error(f"Error processing SQL trigger: {e}")
