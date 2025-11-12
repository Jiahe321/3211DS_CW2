import json
import logging
import azure.functions as func

app = func.FunctionApp()

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
            # TODO：在这里实现你的逻辑
        else:
            logging.info("数据库变动，但没有新行。")
    except Exception as e:
        logging.error(f"处理 SQL 触发数据时出错: {e}")
