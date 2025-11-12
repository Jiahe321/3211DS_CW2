import os
import logging
import azure.functions as func
import requests

app = func.FunctionApp()

SIMULATED_DATA_URL = os.getenv("SIMULATED_FUNCTION_URL")
@app.timer_trigger(schedule="*/10 * * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Timer trigger executed — calling simulated data function.')

    try:
        response = requests.get(SIMULATED_DATA_URL)
        logging.info(f"Fetched simulated data: {response.status_code}")
    except Exception as e:
        logging.error(f"Error fetching simulated data: {e}")
