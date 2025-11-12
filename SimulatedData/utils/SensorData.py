import random

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
            "temperature": random.randint(*self.temp_range),
            "wind": random.randint(*self.wind_range),
            "humidity": random.randint(*self.humidity_range),
            "co2_level": random.randint(*self.co2_level_range)
        }

    # 生成所有传感器的数据
    def generate_all(self) -> list[dict]:
        return [self.generate_single(i+1) for i in range(self.num_sensors)]
