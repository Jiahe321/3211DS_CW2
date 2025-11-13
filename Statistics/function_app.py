import azure.functions as func
import logging
import json
import os
import pyodbc

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
# Task 2: Statistics Function (核心功能)
# ======================================
@app.route(route="calculate_statistics", methods=["GET"])
def calculate_statistics(req: func.HttpRequest) -> func.HttpResponse:
    """
    Task 2: 计算每个传感器的统计数据
    
    功能：
    - 读取数据库中所有传感器的数据
    - 计算每个传感器（1-20）的 min, max, avg
    - 涵盖 4 个数据字段：Temperature, Wind, Humidity, CO2 Level
    
    返回：
    JSON 格式的统计结果，包含所有 20 个传感器的统计信息
    """
    try:
        conn = get_db_connection()
        logger.info("Calculating statistics for all sensors...")
        
        # SQL 查询：按 sensor_id 分组计算统计值
        # 注意：列名是 wind（不是 wind_speed）
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
        
        # 检查是否有数据\
        if not rows:
            logger.warning("No data found in database")
            return func.HttpResponse(
                json.dumps({
                    "status": "warning",
                    "message": "No data in database. Please generate data first.",
                    "statistics": []
                }),
                mimetype="application/json",
                status_code=200
            )
        
        # 格式化统计结果
        statistics = []
        for row in rows:
            stat = {
                "sensor_id": row.sensor_id,
                "record_count": row.record_count,
                "temperature": {
                    "min": round(float(row.min_temp), 2),
                    "max": round(float(row.max_temp), 2),
                    "avg": round(float(row.avg_temp), 2)
                },
                "wind": {
                    "min": round(float(row.min_wind), 2),
                    "max": round(float(row.max_wind), 2),
                    "avg": round(float(row.avg_wind), 2)
                },
                "humidity": {
                    "min": round(float(row.min_humidity), 2),
                    "max": round(float(row.max_humidity), 2),
                    "avg": round(float(row.avg_humidity), 2)
                },
                "co2_level": {
                    "min": round(float(row.min_co2), 2),
                    "max": round(float(row.max_co2), 2),
                    "avg": round(float(row.avg_co2), 2)
                }
            }
            statistics.append(stat)
        
        logger.info(f" Statistics calculated successfully for {len(statistics)} sensors")
        
        # 返回结果
        response = {
            "status": "success",
            "total_sensors": len(statistics),
            "statistics": statistics
        }
        
        return func.HttpResponse(
            json.dumps(response, indent=2),
            mimetype="application/json",
            headers={"Cache-Control": "no-store"},
            status_code=200
        )
        
    except Exception as e:
        logger.error(f" Error calculating statistics: {e}")
        return func.HttpResponse(
            json.dumps({
                "status": "error", 
                "message": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )