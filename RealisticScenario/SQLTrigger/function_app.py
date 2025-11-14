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
    """
    Task 3: SQL Trigger - 当数据库更新时自动触发统计计算
    
    当SensorData表有数据变化时：
    1. 检测变化的行数
    2. 自动调用Statistics Function重新计算
    3. 记录统计结果到日志
    """
    try:
        data = json.loads(changes)
        count = len(data)

        if count > 0:
            logging.info(f"Database changed! {count} line(s) affected.")
            
            # 调用统计函数重新计算
            logging.info(f"Triggering statistics calculation...")
            response = requests.get(STATISTICS_DATA_URL, timeout=30)
            
            if response.status_code == 200:
                # 获取表格文本
                table_text = response.text
                
                # 记录统计信息
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