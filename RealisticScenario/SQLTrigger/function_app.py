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
            logging.info(f"Database changed! {count} line(s) affected.")

            logging.info(f"Triggering statistics calculation...")
            response = requests.get(STATISTICS_DATA_URL, timeout=30)
            
            if response.status_code == 200:
                table_text = response.text
                
                logging.info("Statistics calculated successfully!")
                logging.info("Statistics Table:")
                logging.info("\n" + table_text)
                
            else:
                logging.error(f"Statistics calculation failed with status code: {response.status_code}")

        else:
            logging.info("Database changed but no lines affected.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling statistics function: {e}")
    except Exception as e:
        logging.error(f"Error processing SQL trigger: {e}")