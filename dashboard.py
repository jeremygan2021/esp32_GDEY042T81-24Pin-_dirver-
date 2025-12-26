"""
墨水屏信息看板 - 适配GDEY042T81 (400x300)
显示今日日期、天气、温度等信息的美观UI看板
"""

import epaper4in2
import config
from time import sleep_ms, localtime
import framebuf
import gc
import wifi
import button_control
import urequests
import ujson

# 初始化墨水屏
e = epaper4in2.EPD(config.spi, config.cs, config.dc, config.rst, config.busy)
e.pwr_on()
e.init()

# 创建帧缓冲区
buf = bytearray(config.WIDTH * config.HEIGHT // 8)
fb = framebuf.FrameBuffer(buf, config.WIDTH, config.HEIGHT, framebuf.MONO_HMSB)

# 颜色定义
BLACK = 0
WHITE = 1

# 星期和月份名称
WEEKDAYS_CN = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
WEEKDAYS_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# 天气图标 (16x16像素)
# 晴天
SUNNY_ICON = bytearray([
    0x01, 0x80, 0x01, 0x80, 0x00, 0x00, 0x10, 0x08,
    0x08, 0x10, 0x07, 0xE0, 0x1F, 0xF8, 0x3F, 0xFC,
    0x3F, 0xFC, 0x1F, 0xF8, 0x07, 0xE0, 0x08, 0x10,
    0x10, 0x08, 0x00, 0x00, 0x01, 0x80, 0x01, 0x80
])

# 多云
CLOUDY_ICON = bytearray([
    0x00, 0x00, 0x00, 0x00, 0x07, 0x80, 0x18, 0x60,
    0x20, 0x10, 0x40, 0x08, 0x47, 0xC8, 0x58, 0x68,
    0x60, 0x18, 0x40, 0x08, 0x40, 0x08, 0x60, 0x18,
    0x3F, 0xF0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
])

# 雨天
RAINY_ICON = bytearray([
    0x00, 0x00, 0x07, 0x80, 0x18, 0x60, 0x20, 0x10,
    0x40, 0x08, 0x40, 0x08, 0x60, 0x18, 0x3F, 0xF0,
    0x00, 0x00, 0x09, 0x20, 0x09, 0x20, 0x09, 0x20,
    0x12, 0x40, 0x12, 0x40, 0x12, 0x40, 0x00, 0x00
])

# WiFi图标 (16x16像素)
WIFI_ICON_LARGE = bytearray([
    0x00, 0x00, 0x07, 0xE0, 0x18, 0x18, 0x20, 0x04,
    0x43, 0xC2, 0x8C, 0x31, 0x90, 0x09, 0xA1, 0x85,
    0xA1, 0x85, 0x90, 0x09, 0x8C, 0x31, 0x43, 0xC2,
    0x20, 0x04, 0x18, 0x18, 0x07, 0xE0, 0x00, 0x00
])

class DashboardApp:
    def __init__(self):
        # 天气配置 (使用 Open-Meteo API)
        self.lat = getattr(config, 'WEATHER_LAT', 31.2304)
        self.lon = getattr(config, 'WEATHER_LON', 121.4737)
        self.city = getattr(config, 'WEATHER_CITY_NAME', "Shanghai")
        
        # 时间相关变量
        self.current_year = 0
        self.current_month = 0
        self.current_day = 0
        self.current_hour = 0
        self.current_minute = 0
        self.current_weekday = 0
        
        # 天气相关变量
        self.temperature = None
        self.weather_desc = "Loading..."
        self.humidity = None
        self.weather_icon = SUNNY_ICON
        
        # WiFi相关变量
        self.wifi_connected = False
        self.wifi_signal_strength = None
        
        # 刷新控制
        self.last_refresh_hour = -1
        
    def update_time(self):
        """更新时间信息"""
        t = localtime()
        self.current_year = t[0]
        self.current_month = t[1]
        self.current_day = t[2]
        self.current_weekday = t[6]
        self.current_hour = t[3]
        self.current_minute = t[4]
        
    def update_wifi_status(self):
        """更新WiFi连接状态"""
        try:
            self.wifi_connected = wifi.wifi_manager.is_connected()
            if self.wifi_connected:
                self.wifi_signal_strength = wifi.wifi_manager.get_signal_strength()
            else:
                self.wifi_signal_strength = None
        except Exception as e:
            print(f"获取WiFi状态失败: {e}")
            self.wifi_connected = False
            self.wifi_signal_strength = None
    
    def fetch_weather(self):
        """获取天气信息"""
        if not self.wifi_connected:
            print("WiFi未连接，无法获取天气")
            return
            
        try:
            # 内存回收，防止 ENOMEM
            gc.collect()
            print(f"内存剩余: {gc.mem_free()} bytes")
            
            # Open-Meteo API
            # 使用 HTTP 而非 HTTPS 以节省内存 (SSL 需要大量 RAM)
            # 文档: https://open-meteo.com/en/docs
            url = f"http://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&current=temperature_2m,relative_humidity_2m,weather_code,is_day&timezone=auto"
            
            print(f"获取天气信息: {self.city} ({self.lat}, {self.lon})")
            # 增加超时时间，避免网络慢导致的问题
            response = urequests.get(url, timeout=20)
            
            if response.status_code == 200:
                data = ujson.loads(response.text)
                
                # 解析天气数据
                current = data.get('current', {})
                self.temperature = int(current.get('temperature_2m', 0))
                self.humidity = current.get('relative_humidity_2m', 0)
                weather_code = current.get('weather_code', 0)
                is_day = current.get('is_day', 1)
                
                # 天气代码映射 (WMO Weather interpretation codes)
                # 0: Clear sky
                # 1, 2, 3: Mainly clear, partly cloudy, and overcast
                # 45, 48: Fog and depositing rime fog
                # 51-55: Drizzle
                # 61-65: Rain
                # 71-77: Snow
                # 80-82: Rain showers
                # 85-86: Snow showers
                # 95-99: Thunderstorm
                
                # 简单的天气描述
                if weather_code == 0:
                    self.weather_desc = "Sunny" if is_day else "Clear"
                elif weather_code in [1, 2, 3]:
                    self.weather_desc = "Cloudy"
                elif weather_code in [45, 48]:
                    self.weather_desc = "Foggy"
                elif weather_code in [51, 53, 55]:
                    self.weather_desc = "Drizzle"
                elif weather_code in [61, 63, 65, 80, 81, 82]:
                    self.weather_desc = "Rainy"
                elif weather_code in [71, 73, 75, 77, 85, 86]:
                    self.weather_desc = "Snowy"
                elif weather_code in [95, 96, 99]:
                    self.weather_desc = "Storm"
                else:
                    self.weather_desc = "Unknown"
                
                # 选择图标
                if weather_code in [0, 1]:  # 晴天或少云
                    self.weather_icon = SUNNY_ICON
                elif weather_code in [2, 3, 45, 48]:  # 多云或雾
                    self.weather_icon = CLOUDY_ICON
                elif weather_code >= 51:  # 雨、雪、雷暴等
                    self.weather_icon = RAINY_ICON
                else:
                    self.weather_icon = CLOUDY_ICON
                
                print(f"天气: {self.weather_desc} (Code: {weather_code}), 温度: {self.temperature}°C, 湿度: {self.humidity}%")
            else:
                print(f"获取天气失败: HTTP {response.status_code}")
                
            response.close()
            
        except Exception as e:
            print(f"获取天气异常: {e}")
            self.weather_desc = "Error"
    
    def draw_scaled_icon(self, icon_data, x, y, source_size=16, scale=1):
        """绘制缩放的图标"""
        # 直接读取数据，避开 framebuf 可能存在的字节序问题
        bytes_per_row = source_size // 8
        
        for sy in range(source_size):
            for sx in range(source_size):
                # 计算字节索引: 行号 * 每行字节数 + 列号 // 8
                byte_index = sy * bytes_per_row + (sx // 8)
                
                # 确保索引不越界
                if byte_index < len(icon_data):
                    # 计算位索引: 7 - (列号 % 8) (MSB first)
                    bit_index = 7 - (sx % 8)
                    
                    # 获取像素值
                    if (icon_data[byte_index] >> bit_index) & 1:
                        fb.fill_rect(x + sx * scale, y + sy * scale, scale, scale, BLACK)

    def draw_icon(self, icon_data, x, y, size=16):
        """绘制图标"""
        # 直接读取数据，避开 framebuf 可能存在的字节序问题
        bytes_per_row = size // 8
        
        for sy in range(size):
            for sx in range(size):
                # 计算字节索引: 行号 * 每行字节数 + 列号 // 8
                byte_index = sy * bytes_per_row + (sx // 8)
                
                # 确保索引不越界
                if byte_index < len(icon_data):
                    # 计算位索引: 7 - (列号 % 8) (MSB first)
                    bit_index = 7 - (sx % 8)
                    
                    # 获取像素值
                    if (icon_data[byte_index] >> bit_index) & 1:
                        fb.pixel(x + sx, y + sy, BLACK)

    def draw_scaled_text(self, text, x, y, scale=1):
        """使用像素放大绘制文本"""
        text = str(text)
        # 创建单个字符的缓冲区 (8x8)
        char_width = 8
        char_height = 8
        char_buf = bytearray(char_width * char_height // 8)
        char_fb = framebuf.FrameBuffer(char_buf, char_width, char_height, framebuf.MONO_HMSB)
        
        current_x = x
        
        for char in text:
            # 清空字符缓冲区 (背景为0)
            char_fb.fill(0)
            # 绘制字符 (前景为1)
            char_fb.text(char, 0, 0, 1)
            
            # 逐像素放大绘制
            for cy in range(char_height):
                for cx in range(char_width):
                    if char_fb.pixel(cx, cy):
                        # 在主缓冲区绘制矩形 (颜色为BLACK)
                        fb.fill_rect(current_x + cx * scale, y + cy * scale, scale, scale, BLACK)
            
            # 移动到下一个字符位置
            current_x += char_width * scale

    def draw_dashboard(self):
        """绘制看板界面 - 优化版分栏布局"""
        fb.fill(WHITE)
        
        # === 全局边框 ===
        # 外框
        fb.rect(0, 0, config.WIDTH, config.HEIGHT, BLACK)
        # 内框 (留白效果)
        fb.rect(4, 4, config.WIDTH - 8, config.HEIGHT - 8, BLACK)
        
        # === 布局分割 ===
        # 垂直分割线 (x=240)
        fb.vline(240, 20, 260, BLACK)
        fb.vline(241, 20, 260, BLACK) # 加粗
        
        # === 左侧区域 (日期信息) ===
        # 区域中心 x=120
        
        # 1. 年月 (左上对齐)
        # 格式: "Dec 2025"
        month_year = f"{MONTHS_EN[self.current_month-1]} {self.current_year}"
        self.draw_scaled_text(month_year, 20, 30, scale=2)
        
        # 2. 巨大的日期 (居中)
        day_str = str(self.current_day)
        # 估算宽度: len * 8 * scale. Scale=10 -> 80px per char
        day_scale = 12
        day_width = len(day_str) * 8 * day_scale
        day_x = 120 - (day_width // 2)
        self.draw_scaled_text(day_str, day_x, 90, scale=day_scale)
        
        # 3. 星期 (左下对齐)
        weekday_en = WEEKDAYS_EN[self.current_weekday]
        self.draw_scaled_text(weekday_en, 20, 220, scale=2)
        
        # 4. 底部更新时间 (小字)
        time_str = f"Updated: {self.current_hour:02d}:{self.current_minute:02d}"
        fb.text(time_str, 20, 260, BLACK)

        # === 右侧区域 (天气与状态) ===
        # 区域中心 x=320
        
        # 1. WiFi状态 (右上角)
        if self.wifi_connected:
            self.draw_icon(WIFI_ICON_LARGE, 360, 10, 16)
        else:
            fb.text("No WiFi", 340, 10, BLACK)
            
        # 2. 天气图标 (放大显示)
        # 图标原始16x16, 放大3倍 -> 48x48
        icon_scale = 3
        icon_x = 320 - (16 * icon_scale // 2)
        self.draw_scaled_icon(self.weather_icon, icon_x, 60, 16, icon_scale)
        
        # 3. 温度 (大号)
        if self.temperature is not None:
            temp_str = f"{self.temperature}"
            temp_scale = 5
            temp_width = len(temp_str) * 8 * temp_scale
            # 加上摄氏度符号的空间
            total_width = temp_width + (10 * temp_scale // 2) 
            temp_x = 320 - (total_width // 2)
            
            self.draw_scaled_text(temp_str, temp_x, 130, scale=temp_scale)
            
            # 摄氏度符号
            degree_x = temp_x + temp_width
            degree_y = 130
            # 简单的矩形框作为度数符号
            fb.rect(degree_x, degree_y, 6, 6, BLACK)
            fb.rect(degree_x + 1, degree_y + 1, 4, 4, WHITE) # 中空
            
            # "C"
            # fb.text("C", degree_x + 10, degree_y, BLACK) 
            # 既然是极简风格，只画度数符号或者留白也可以，这里加个C
            self.draw_scaled_text("C", degree_x + 10, 130 + 5, scale=2)
            
        else:
            self.draw_scaled_text("--", 300, 130, scale=4)
            
        # 4. 天气描述
        if self.weather_desc:
            # 居中显示，如果太长需要处理，这里简单居中
            desc_str = self.weather_desc
            desc_width = len(desc_str) * 8 * 1
            desc_x = 320 - (desc_width // 2)
            # 限制边界
            if desc_x < 250: desc_x = 250
            fb.text(desc_str, desc_x, 190, BLACK)
            
        # 5. 湿度
        if self.humidity is not None:
            hum_str = f"Hum: {self.humidity}%"
            hum_width = len(hum_str) * 8
            hum_x = 320 - (hum_width // 2)
            fb.text(hum_str, hum_x, 210, BLACK)
            
        # 6. 城市名
        city_str = self.city
        city_width = len(city_str) * 8
        city_x = 320 - (city_width // 2)
        fb.text(city_str, city_x, 240, BLACK)
        
    def need_refresh(self):
        """检查是否需要刷新（每小时刷新一次）"""
        if self.current_hour != self.last_refresh_hour:
            self.last_refresh_hour = self.current_hour
            return True
        return False
    
    def connect_wifi(self):
        """连接WiFi"""
        if not wifi.wifi_manager.is_connected():
            print("尝试连接WiFi...")
            wifi.wifi_manager.connect()
        self.update_wifi_status()

    def display(self, force=False):
        """显示看板"""
        self.update_time()
        self.update_wifi_status()
        
        # 检查是否需要刷新
        if force or self.need_refresh():
            print(f"刷新看板 - {self.current_hour:02d}:{self.current_minute:02d}")
            
            # 确保WiFi已连接
            self.connect_wifi()
            
            # 获取天气信息
            self.fetch_weather()
            
            # 绘制界面
            self.draw_dashboard()
            
            # 显示到屏幕
            e.display_frame(buf, global_refresh=True)
        else:
            print(f"无需刷新 - {self.current_hour:02d}:{self.current_minute:02d}")
    
    def run(self):
        """运行看板应用"""
        print("启动墨水屏信息看板")
        
        # 初始化按钮中断
        button_control.init_button_irq()
        
        # 初始显示
        self.display(force=True)
        
        # 主循环
        while True:
            try:
                # 每分钟检查一次
                self.display()
                
                # 等待一分钟，期间检查按钮
                for _ in range(600):  # 600 * 100ms = 60s
                    if button_control.check_button() == 1:
                        print("检测到按钮点击，退出看板应用")
                        return
                    sleep_ms(100)
                
                gc.collect()
                
            except Exception as e:
                print(f"发生错误: {e}")
                sleep_ms(5000)

# 创建并运行看板应用
if __name__ == "__main__":
    dashboard = DashboardApp()
    dashboard.run()
