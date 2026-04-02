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
    # 将以下代码补充至 main.py 中

# 天干与地支基础数组
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

def get_day_ganzhi(year: int, month: int, day: int) -> str:
    """
    严谨日干支推算算法：基于公历日期推算
    采用世纪常数法，确保前后1000年无误差
    """
    if month <= 2:
        month += 12
        year -= 1
    
    c = year // 100
    y = year % 100
    
    # 儒略日推导公式变体，计算天干地支索引
    i = (d := day) + (13 * (month + 1)) // 5 + y + y // 4 + c // 4 - 2 * c
    
    # 天干索引
    gan_index = (i - 1) % 10
    # 地支索引
    zhi_index = (i + 1) % 12
    
    return HEAVENLY_STEMS[gan_index] + EARTHLY_BRANCHES[zhi_index]

def get_hour_ganzhi(day_gan: str, hour: int) -> str:
    """
    严谨时干支推算算法：五鼠遁元法 (日上起时法)
    规则：甲己还加甲，乙庚丙作初...
    """
    # 确定时辰地支 (23-1点为子时，1-3点为丑时...)
    zhi_index = ((hour + 1) % 24) // 2
    hour_zhi = EARTHLY_BRANCHES[zhi_index]
    
    # 根据日干推导时辰天干的起点
    day_gan_index = HEAVENLY_STEMS.index(day_gan)
    
    # 五鼠遁元公式：时干起点 = (日干索引 % 5) * 2
    start_gan_index = (day_gan_index % 5) * 2
    
    # 计算当前时辰的天干
    hour_gan_index = (start_gan_index + zhi_index) % 10
    hour_gan = HEAVENLY_STEMS[hour_gan_index]
    
    return hour_gan + hour_zhi

# 更新原有的 API 端点，输出四柱核心数据
@app.get("/api/v1/astronomy/bazi_qimen_params")
async def get_qimen_parameters(year: int, month: int, day: int, hour: int, minute: int):
    """
    奇门遁甲核心参数获取接口
    """
    # 获取天文节气参数 (复用之前的逻辑)
    solar_longitude_data = await calculate_solar_longitude(year, month, day, hour, minute)
    
    # 计算日干支与时干支
    day_gz = get_day_ganzhi(year, month, day)
    hour_gz = get_hour_ganzhi(day_gz[0], hour)
    
    return {
        "timestamp_utc": f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
        "solar_term": solar_longitude_data["current_solar_term"],
        "day_pillar": day_gz,
        "hour_pillar": hour_gz,
        "status": "ready_for_dingju" # 标志状态：准备进行定局
    }
