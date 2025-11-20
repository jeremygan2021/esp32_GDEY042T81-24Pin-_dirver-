"""
墨水屏日历应用 - 适配GDEY042T81 (400x300)
每6小时全局刷新一次，显示美观的日历界面
"""

import epaper4in2
from machine import Pin, SPI
from time import sleep_ms, localtime, mktime
import framebuf
import gc

# SPI引脚配置
sck = Pin(47)   # SCK pin47
miso = Pin(46)  # MISO pin46
mosi = Pin(21)  # SDI/MOSI pin21

# 控制引脚配置
dc = Pin(40)    # D/C pin40
cs = Pin(45)    # CS pin45
rst = Pin(41)   # RES pin41
busy = Pin(42)  # BUSY pin42

# 屏幕尺寸
WIDTH = 400
HEIGHT = 300

# 初始化SPI
spi = SPI(2, baudrate=2000000, polarity=0, phase=0, sck=sck, miso=miso, mosi=mosi)

# ESPink电源控制
epd_power = Pin(2, Pin.OUT)
epd_power.on()
sleep_ms(10)

# 初始化墨水屏
e = epaper4in2.EPD(spi, cs, dc, rst, busy)
e.pwr_on()
e.init()

# 创建帧缓冲区
buf = bytearray(WIDTH * HEIGHT // 8)
fb = framebuf.FrameBuffer(buf, WIDTH, HEIGHT, framebuf.MONO_HMSB)

# 颜色定义
BLACK = 0
WHITE = 1

# 星期名称
WEEKDAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", 
          "jul", "aug", "sep", "oct", "nov", "dec"]

class CalendarApp:
    def __init__(self):
        # 刷新计数器
        self.refresh_count = 0
        self.last_full_refresh = 0  # 使用0表示未进行过全屏刷新
        self.last_refresh_hour = -1  # 上次全屏刷新的小时数，-1表示未刷新过
        self.full_refresh_interval = 6 * 60 * 60 * 1000  # 6小时（毫秒）
        
        # 时间相关变量
        self.current_year = 0
        self.current_month = 0
        self.current_day = 0
        self.current_hour = 0
        self.current_minute = 0
        self.current_weekday = 0
        
    def update_time(self):
        """更新当前时间"""
        t = localtime()
        self.current_year = t[0]
        self.current_month = t[1]
        self.current_day = t[2]
        self.current_weekday = t[6]  # 0=星期日, 1=星期一, ...
        self.current_hour = t[3]
        self.current_minute = t[4]
        
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
        fb.hline(0, 50, WIDTH, BLACK)
        
        # 绘制年份和月份
        month_year = f"year {self.current_year} {MONTHS[self.current_month-1]}"
        fb.text(month_year, WIDTH // 2 - len(month_year) * 6 // 2, 20, BLACK)
        
        # 绘制装饰性元素
        fb.rect(10, 10, WIDTH - 20, 30, BLACK)
        
    def draw_calendar_grid(self):
        """绘制日历网格"""
        # 网格参数
        grid_start_y = 70
        grid_height = 180
        cell_width = WIDTH // 7
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
            fb.hline(0, y, WIDTH, BLACK)
            
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
                    # 绘制背景框
                    fb.rect(col * cell_width + 2, grid_start_y + row * cell_height + 2, 
                           cell_width - 4, cell_height - 4, BLACK)
                    # 反色显示
                    fb.text(str(day), x, y, WHITE)
                else:
                    fb.text(str(day), x, y, BLACK)
                    
                day += 1
                if day > days_in_month:
                    break
                    
            if day > days_in_month:
                break
                
    def draw_footer(self):
        """绘制底部时间信息"""
        # 绘制分割线
        fb.hline(0, HEIGHT - 50, WIDTH, BLACK)
        
        # 格式化时间
        time_str = f"{self.current_hour:02d}:{self.current_minute:02d}"
        date_str = f"Year: {self.current_year} Month: {self.current_month} Day: {self.current_day} &{WEEKDAYS[self.current_weekday]}"
        
        # 显示时间
        fb.text(time_str, WIDTH // 2 - len(time_str) * 6 // 2, HEIGHT - 40, BLACK)
        
        # 显示日期
        fb.text(date_str, WIDTH // 2 - len(date_str) * 6 // 2, HEIGHT - 25, BLACK)
        
        # 绘制装饰性元素
        fb.rect(10, HEIGHT - 45, WIDTH - 20, 35, BLACK)
        
    def need_full_refresh(self):
        """检查是否需要全屏刷新"""
        # 如果是第一次运行，需要全屏刷新
        if self.last_full_refresh == 0:
            return True
            
        # 获取当前时间
        current_time = localtime()
        current_hour = current_time[3]
        
        # 简单判断：如果当前小时是6的倍数（6:00, 12:00, 18:00, 0:00），则执行全屏刷新
        # 这样可以确保每6小时执行一次全屏刷新
        if current_hour % 6 == 0 and current_time[4] < 5:  # 在每6小时的开始5分钟内执行
            # 检查是否已经在这个时间段执行过刷新
            if not hasattr(self, 'last_refresh_hour') or self.last_refresh_hour != current_hour:
                self.last_refresh_hour = current_hour
                return True
        
        return False
        
    def display(self):
        """显示日历"""
        self.update_time()
        self.draw_calendar()
        
        # 检查是否需要全屏刷新
        if self.need_full_refresh():
            print("执行全屏刷新")
            e.display_frame(buf, global_refresh=True)
            # 标记已执行全屏刷新
            self.last_full_refresh = 1  # 非零值表示已执行过刷新
        else:
            print("执行局部刷新")
            e.display_frame(buf, partial=True)
            
    def run(self):
        """运行日历应用"""
        print("启动墨水屏日历应用")
        
        # 初始全屏刷新
        self.display()
        
        # 主循环
        while True:
            try:
                # 每分钟更新一次显示
                self.display()
                
                # 等待一分钟
                sleep_ms(60000)
                
                # 垃圾回收
                gc.collect()
                
            except Exception as e:
                print(f"发生错误: {e}")
                sleep_ms(5000)

# 创建并运行日历应用
if __name__ == "__main__":
    calendar = CalendarApp()
    calendar.run()