# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from skyfield.api import load
from skyfield.framelib import ecliptic_J2000
import math

# 初始化最专业的异步 API 框架
app = FastAPI(title="高精度奇门遁甲运算引擎", version="1.0.0")

# 配置跨域，允许前端调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 预加载国家天文台级别的 JPL DE421 星历表 (适用于当前及未来数十年的高精度计算)
print("正在加载高精度星历数据...")
eph = load('de421.bsp')
sun = eph['sun']
earth = eph['earth']
ts = load.timescale()

@app.get("/api/v1/astronomy/solar_longitude")
async def calculate_solar_longitude(year: int, month: int, day: int, hour: int, minute: int):
    """
    核心算法：计算指定时间的精确太阳黄经，用于严密判定二十四节气与奇门定局
    """
    # 将输入时间转换为国际标准时间 (UTC)，此处暂不考虑经纬度均位差计算，后续迭代加入
    t = ts.utc(year, month, day, hour, minute)
    
    # 建立地球对太阳的观测模型
    astrometric = earth.at(t).observe(sun)
    lat, lon, distance = astrometric.frame_latlon(ecliptic_J2000)
    
    # 获取黄经度数 (0-360度)
    degrees = lon.degrees % 360
    
    # 初步的节气映射逻辑 (每15度为一个节气，0度为春分)
    term_index = math.floor(degrees / 15)
    solar_terms = ["春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑", 
                   "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", 
                   "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰"]
    
    current_term = solar_terms[term_index]

    return {
        "timestamp": f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} UTC",
        "solar_longitude": round(degrees, 6), # 精确到小数点后6位
        "current_solar_term": current_term,
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    # 启动后端服务：python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
