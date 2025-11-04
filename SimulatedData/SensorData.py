import random
import json
import pandas as pd

class SensorData:

    def __init__(self):
        self.num_sensors = 20
        self.temp_range = (5, 18)
        self.wind_range = (12, 24)
        self.humidity_range = (30, 60)
        self.co2_level_range = (400, 1600)

    # 生成指定传感器的数据
    def generate_single(self, sensor_id: int) -> dict:
        return {
            "sensor_id": sensor_id,
            "temperature": round(random.uniform(*self.temp_range), 2),
            "wind": round(random.uniform(*self.wind_range), 2),
            "humidity": round(random.uniform(*self.humidity_range), 2),
            "co2_level": round(random.uniform(*self.co2_level_range), 2)
        }

    # 生成所有传感器的数据
    def generate_all(self) -> list[dict]:
        return [self.generate_single(i+1) for i in range(self.num_sensors)]

    # 以 JSON 形式返回数据
    def to_json(self) -> str:
        data = self.generate_all()
        return json.dumps(data, indent=2)

if __name__ == "__main__":
    simulator = SensorData()
    data_json = simulator.to_json()
    print(data_json)

