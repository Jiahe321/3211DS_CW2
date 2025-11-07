import requests
import time
import matplotlib.pyplot as plt
import json

BASE_URL = "http://localhost:7071/api/generate_sensor_data"

SENSORS_NUM = 20

results = []

for call_num in range(1, 20, 2):
    print(f"Running test with {call_num} calls...")
    start_time = time.time()

    for _ in range(call_num):
        try:
            response = requests.get(BASE_URL)
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")

    total_time = time.time() - start_time
    avg_time = total_time / call_num

    total_data = call_num * SENSORS_NUM
    results.append({
        "calls": call_num,
        "total_data": total_data,
        "total_time": total_time,
        "avg_time": avg_time
    })

    print(f"{call_num} calls done in {total_time:.2f}s (avg {avg_time:.2f}s/call)\n")


print(json.dumps(results, indent=2))

x = [r["total_data"] for r in results]
y = [r["total_time"] for r in results]

plt.figure(figsize=(8,5))
plt.plot(x, y, marker='o', linestyle='-', color='royalblue')
plt.xlabel("Total data inserted")
plt.ylabel("Total time (s)")
plt.title("Azure Function Performance Scalability Test")
plt.grid(True)
plt.savefig("scalability_graph.png")
plt.show()
