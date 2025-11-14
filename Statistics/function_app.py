import azure.functions as func
import logging
import json
import os
import pyodbc
import tabulate

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
logger = logging.getLogger("azure")
logger.setLevel(logging.INFO)

# 数据库连接配置
_db_conn = None
_CONN_STR = os.getenv("SQL_CONNECTION_STRING")


def get_db_connection():
    """获取数据库连接（带连接池）"""
    global _db_conn
    
    if not _CONN_STR:
        raise RuntimeError("SQL_CONNECTION_STRING not set")
    
    try:
        # 验证现有连接
        if _db_conn is not None:
            cursor = _db_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()
            return _db_conn
    except:
        _db_conn = None
    
    # 创建新连接
    _db_conn = pyodbc.connect(_CONN_STR, timeout=30)
    logger.info("Database connection established")
    return _db_conn


# ======================================
# Task 2: Statistics Function (表格输出)
# ======================================
@app.route(route="calculate_statistics", methods=["GET"])
def calculate_statistics(req: func.HttpRequest) -> func.HttpResponse:
    """
    Task 2: 计算每个传感器的统计数据
    
    功能：
    - 读取数据库中所有传感器的数据
    - 计算每个传感器（1-20）的 min, max, avg
    - 涵盖 4 个数据字段：Temperature, Wind, Humidity, CO2 Level
    - 以纯文本表格形式输出
    """
    try:
        conn = get_db_connection()
        logger.info("Calculating statistics for all sensors...")
        
        # SQL 查询：按 sensor_id 分组计算统计值
        query = """
        SELECT 
            sensor_id,
            MIN(temperature) as min_temp,
            MAX(temperature) as max_temp,
            AVG(temperature) as avg_temp,
            MIN(wind) as min_wind,
            MAX(wind) as max_wind,
            AVG(wind) as avg_wind,
            MIN(humidity) as min_humidity,
            MAX(humidity) as max_humidity,
            AVG(humidity) as avg_humidity,
            MIN(co2_level) as min_co2,
            MAX(co2_level) as max_co2,
            AVG(co2_level) as avg_co2,
            COUNT(*) as record_count
        FROM SensorData
        GROUP BY sensor_id
        ORDER BY sensor_id
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 检查是否有数据
        if not rows:
            logger.warning("No data found in database")
            return func.HttpResponse(
                "No data in database. Please generate data first.",
                mimetype="text/plain",
                status_code=200
            )
        
        # 构建表格数据
        table_data = []
        for row in rows:
            table_row = [
                row.sensor_id,
                row.record_count,
                round(float(row.min_temp), 1),
                round(float(row.max_temp), 1),
                round(float(row.avg_temp), 1),
                round(float(row.min_wind), 1),
                round(float(row.max_wind), 1),
                round(float(row.avg_wind), 1),
                round(float(row.min_humidity), 1),
                round(float(row.max_humidity), 1),
                round(float(row.avg_humidity), 1),
                round(float(row.min_co2), 1),
                round(float(row.max_co2), 1),
                round(float(row.avg_co2), 1)
            ]
            table_data.append(table_row)
        
        # 定义表头
        headers = [
            'Sensor_ID', 'Records',
            'Temp_Min', 'Temp_Max', 'Temp_Avg',
            'Wind_Min', 'Wind_Max', 'Wind_Avg',
            'Humidity_Min', 'Humidity_Max', 'Humidity_Avg',
            'CO2_Min', 'CO2_Max', 'CO2_Avg'
        ]
        
        # 生成ASCII表格
        table_text = tabulate.tabulate(table_data, headers=headers, tablefmt='grid', floatfmt='.1f')
        
        logger.info(f"Statistics calculated successfully for {len(table_data)} sensors")
        
        # 返回纯文本表格
        return func.HttpResponse(
            table_text,
            mimetype="text/plain",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        return func.HttpResponse(
            f"Error: {str(e)}",
            mimetype="text/plain",
            status_code=500
        )