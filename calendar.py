"""
墨水屏日历应用 - 适配GDEY042T81 (400x300)
只在时段变化时全局刷新，显示美观的日历界面
时段分为：Morning(5:00-12:00), Noon(12:00-14:00), Afternoon(14:00-17:00), Evening(17:00-20:00), Night(20:00-5:00)
"""

import epaper4in2
import config
from time import sleep_ms, localtime, mktime
import framebuf
import gc
import wifi
import button_control

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

# 星期名称
WEEKDAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", 
          "jul", "aug", "sep", "oct", "nov", "dec"]

# 时段图标 (8x8像素)
# Morning/Afternoon - 太阳图标
MORNING_ICON = bytearray(b'\x08\x1C\x22\x41\x41\x22\x1C\x08')
AFTERNOON_ICON = bytearray(b'\x08\x1C\x22\x41\x41\x22\x1C\x08')

# Noon - 正午太阳（更亮）
NOON_ICON = bytearray(b'\x3C\x42\x42\x42\x42\x42\x42\x3C')

# Evening/Night - 月亮图标
EVENING_ICON = bytearray(b'\x08\x1C\x2A\x55\x55\x2A\x1C\x08')
NIGHT_ICON = bytearray(b'\x08\x1C\x2A\x55\x55\x2A\x1C\x08')

# WiFi图标 (8x8像素)
# WiFi图标（8×8 像素，文字描述：底部一条横线，中间三竖，顶部一横，呈“Wi-Fi”扇形）
WIFI_ICON = bytearray([0x00, 0x0E, 0x11, 0x11, 0x11, 0x0A, 0x04, 0x00])
WIFI_NO_SIGNAL_ICON = bytearray(b'\x00\x0E\x11\x11\x11\x11\x0E\x00')

class CalendarApp:
    def __init__(self):
        # 刷新相关变量
        self.last_full_refresh = 0  # 使用0表示未进行过全屏刷新
        self.last_period = ""  # 上次显示的时段
        
        # 时间相关变量
        self.current_year = 0
        self.current_month = 0
        self.current_day = 0
        self.current_hour = 0
        self.current_minute = 0
        self.current_weekday = 0
        
        # WiFi相关变量
        self.wifi_connected = False
        self.wifi_signal_strength = None
        
    def get_time_period_icon(self, hour):
        """根据小时数返回时段对应的图标"""
        if 5 <= hour < 12:
            return MORNING_ICON
        elif 12 <= hour < 14:
            return NOON_ICON
        elif 14 <= hour < 17:
            return AFTERNOON_ICON
        elif 17 <= hour < 20:
            return EVENING_ICON
        else:
            return NIGHT_ICON
            
    def get_time_period(self, hour):
        """根据小时数返回时段"""
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 14:
            return "Noon"
        elif 14 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 20:
            return "Evening"
        else:
            return "Night"
            
    def update_time(self):
        t = localtime()
        self.current_year = t[0]
        self.current_month = t[1]
        self.current_day = t[2]
        self.current_weekday = t[6]  # 0=星期日, 1=星期一, ...
        self.current_hour = t[3]
        self.current_minute = t[4]
        
    def update_wifi_status(self):
        """更新WiFi连接状态和信号强度"""
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
        
    def get_month_days(self, year, month):
        """获取指定月份的天数"""
        # 简化的月份天数计算，不考虑闰年
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif month in [4, 6, 9, 11]:
            return 30
        else:  # 二月
            # 简单的闰年判断
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                return 29
            else:
                return 28
                
    def get_first_weekday(self, year, month):
        """获取指定月份的第一天是星期几（0=星期日, 1=星期一, ...）"""
        # 使用Zeller公式计算星期几
        if month < 3:
            month += 12
            year -= 1
        k = year % 100
        j = year // 100
        day = 1
        weekday = (day + (13 * (month + 1)) // 5 + k + k // 4 + j // 4 + 5 * j) % 7
        # 调整为0=星期日, 1=星期一, ...
        # Zeller公式返回的是: 0=星期六, 1=星期日, 2=星期一, ..., 6=星期五
        # 我们需要转换为: 0=星期日, 1=星期一, ..., 6=星期六
        return (weekday + 6) % 7
        
    def draw_calendar(self):
        """绘制日历界面"""
        # 清空屏幕
        fb.fill(WHITE)
        
        # 绘制顶部标题区域
        self.draw_header()
        
        # 绘制日历网格
        self.draw_calendar_grid()
        
        # 绘制底部时间信息
        self.draw_footer()
        
    def draw_header(self):
        """绘制顶部标题区域"""
        # 绘制分割线
        fb.hline(0, 50, config.WIDTH, BLACK)
        
        # 绘制WiFi状态（左上角）
        if self.wifi_connected:
            # 绘制WiFi图标
            self.draw_icon(WIFI_ICON, 10, 15)
            
            # 绘制信号强度条
            if self.wifi_signal_strength is not None:
                # 将信号强度转换为0-4的等级
                if self.wifi_signal_strength > -50:
                    signal_bars = 4  # 信号极好
                elif self.wifi_signal_strength > -60:
                    signal_bars = 3  # 信号良好
                elif self.wifi_signal_strength > -70:
                    signal_bars = 2  # 信号一般
                elif self.wifi_signal_strength > -80:
                    signal_bars = 1  # 信号较弱
                else:
                    signal_bars = 0  # 信号极弱或无信号
                
                # 绘制信号强度条
                bar_width = 2
                bar_height_step = 2
                max_height = 8
                
                for i in range(4):
                    height = (i + 1) * bar_height_step
                    if height > max_height:
                        height = max_height
                    
                    # 如果当前信号强度等级大于等于当前条，则填充黑色
                    if i < signal_bars:
                        fb.fill_rect(22 + i * (bar_width + 1), 24 - height, bar_width, height, BLACK)
                    else:
                        fb.rect(22 + i * (bar_width + 1), 24 - height, bar_width, height, BLACK)
        else:
            # 绘制无WiFi连接图标
            self.draw_icon(WIFI_NO_SIGNAL_ICON, 10, 15)
        
        # 绘制年份和月份（居中）
        month_year = f"year {self.current_year} {MONTHS[self.current_month-1]}"
        fb.text(month_year, config.WIDTH // 2 - len(month_year) * 6 // 2, 20, BLACK)
        
        # 绘制装饰性元素
        fb.rect(10, 10, config.WIDTH - 20, 30, BLACK)
        
    def draw_calendar_grid(self):
        """绘制日历网格"""
        # 网格参数
        grid_start_y = 70
        grid_height = 180
        cell_width = config.WIDTH // 7
        cell_height = grid_height // 7
        
        # 绘制星期标题
        for i, weekday in enumerate(WEEKDAYS):
            x = i * cell_width + cell_width // 2 - len(weekday) * 6 // 2
            y = grid_start_y - 20
            fb.text(weekday, x, y, BLACK)
            
        # 绘制网格线
        # 水平线
        for i in range(8):
            y = grid_start_y + i * cell_height
            fb.hline(0, y, config.WIDTH, BLACK)
            
        # 垂直线
        for i in range(8):
            x = i * cell_width
            fb.vline(x, grid_start_y - 30, grid_height + 30, BLACK)
            
        # 获取月份信息
        days_in_month = self.get_month_days(self.current_year, self.current_month)
        first_weekday = self.get_first_weekday(self.current_year, self.current_month)
        
        # 填充日期
        day = 1
        for row in range(6):  # 最多6行
            for col in range(7):  # 7列
                if (row == 0 and col < first_weekday) or day > days_in_month:
                    continue
                    
                x = col * cell_width + cell_width // 2 - 6
                y = grid_start_y + row * cell_height + cell_height // 2 - 8
                
                # 如果是今天，高亮显示
                if day == self.current_day:
                    # 先填充黑色背景
                    fb.fill_rect(col * cell_width + 2, grid_start_y + row * cell_height + 2, 
                                cell_width - 4, cell_height - 4, BLACK)
                    # 然后用白色文字显示日期
                    fb.text(str(day), x, y, WHITE)
                else:
                    fb.text(str(day), x, y, BLACK)
                    
                day += 1
                if day > days_in_month:
                    break
                    
            if day > days_in_month:
                break
                
    def draw_icon(self, icon_data, x, y, size=8):
        """绘制8x8像素的图标"""
        # 创建一个小的帧缓冲区用于图标
        icon_buf = bytearray(size * size // 8)
        icon_fb = framebuf.FrameBuffer(icon_buf, size, size, framebuf.MONO_HMSB)
        
        # 将图标数据复制到缓冲区
        for i in range(len(icon_data)):
            icon_buf[i] = icon_data[i]
            
        # 将图标绘制到主帧缓冲区
        fb.blit(icon_fb, x, y)
        
    def draw_footer(self):
        """绘制底部时间信息"""
        # 绘制分割线
        fb.hline(0, config.HEIGHT - 50, config.WIDTH, BLACK)
        
        # 获取当前时段和图标
        current_period = self.get_time_period(self.current_hour)
        period_icon = self.get_time_period_icon(self.current_hour)
        
        # 格式化日期
        date_str = f"Year: {self.current_year} Month: {self.current_month} Day: {self.current_day} {WEEKDAYS[self.current_weekday]}"
        
        # 计算时段文本位置（考虑图标）
        period_x = config.WIDTH // 2 - len(current_period) * 6 // 2 + 10  # 向右偏移10像素为图标留空间
        icon_x = period_x - 15  # 图标在文本左侧
        
        # 绘制图标
        self.draw_icon(period_icon, icon_x, config.HEIGHT - 42)
        
        # 显示时段
        fb.text(current_period, period_x, config.HEIGHT - 40, BLACK)
        
        # 显示日期
        fb.text(date_str, config.WIDTH // 2 - len(date_str) * 6 // 2, config.HEIGHT - 25, BLACK)
        
        # 绘制装饰性元素
        fb.rect(10, config.HEIGHT - 45, config.WIDTH - 20, 35, BLACK)
        
    def need_refresh(self):
        """检查是否需要刷新（只在时段变化时刷新）"""
        # 获取当前时段
        current_period = self.get_time_period(self.current_hour)
        
        # 如果时段发生变化，需要刷新
        if current_period != self.last_period:
            self.last_period = current_period
            return True
            
        return False
        
    def display(self):
        """显示日历"""
        self.update_time()
        self.update_wifi_status()
        
        # 检查是否需要刷新
        if self.need_refresh():
            print(f"时段变化，执行全局刷新 - {self.last_period}")
            self.draw_calendar()
            e.display_frame(buf, global_refresh=True)
        else:
            print(f"时段未变化，不刷新 - {self.last_period}")
            
    def run(self):
        """运行日历应用"""
        print("启动墨水屏日历应用")
        
        # 初始化按钮中断
        button_control.init_button_irq()
        
        # 增加延迟并清除可能因声音干扰产生的按钮中断
        sleep_ms(500)
        button_control.btn_irq_flag = False
        
        # 初始显示
        self.display()
        
        # 主循环
        while True:
            try:
                # 每分钟检查一次是否需要刷新
                self.display()
                
                # 等待一分钟，期间每100ms检查一次按钮状态
                for _ in range(600):  # 600 * 100ms = 60s
                    # 检查按钮状态
                    if button_control.check_button() == 1:
                        print("检测到按钮点击，退出日历应用")
                        return  # 退出循环
                    sleep_ms(100)
                
                # 垃圾回收
                gc.collect()
                
            except Exception as e:
                print(f"发生错误: {e}")
                sleep_ms(5000)

# 创建并运行日历应用
if __name__ == "__main__":
    calendar = CalendarApp()
    calendar.run()