import azure.functions as func
import logging
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.SensorData import SensorData

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="generate_sensor_data")
def generate_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Generating simulated IoT sensor data...')

    simulator = SensorData()
    data_json = simulator.to_json()

    # 显示生成的数据
    return func.HttpResponse(
        data_json,
        mimetype="application/json",
        status_code=200
    )
