"""
墨水屏 Todo List 应用 - 适配GDEY042T81 (400x300)
极简高级风格设计 (Premium Minimalist Design)
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

# 星期名称
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# 图标定义 (8x8)
# WiFi图标
WIFI_ICON = bytearray([0x00, 0x3C, 0x42, 0x81, 0x24, 0x42, 0x18, 0x00])
NO_WIFI_ICON = bytearray([0x00, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x00])

# 时钟图标 (用于截止日期)
CLOCK_ICON = bytearray([0x00, 0x1C, 0x22, 0x2A, 0x26, 0x22, 0x1C, 0x00])

class TodoApp:
    def __init__(self):
        self.todos = []
        self.wifi_connected = False
        self.last_refresh_time = 0
        self.refresh_interval = 300000  # 5分钟刷新一次
        
    def connect_wifi(self):
        """连接WiFi"""
        if not wifi.wifi_manager.is_connected():
            print("尝试连接WiFi...")
            wifi.wifi_manager.connect()
        self.wifi_connected = wifi.wifi_manager.is_connected()
        return self.wifi_connected

    def fetch_todos(self):
        """获取Todo列表"""
        if not self.wifi_connected:
            return

        try:
            url = "http://6.6.6.86:8199/api/todos/?skip=0&limit=100&device_id=1"
            headers = {
                'accept': 'application/json',
                'X-API-Key': '123tangledup-ai'
            }
            
            print("正在获取Todo列表...")
            response = urequests.get(url, headers=headers)
            
            if response.status_code == 200:
                self.todos = ujson.loads(response.text)
                # 排序：未完成的在前，已完成的在后；同类中按截止日期排序
                # 简单的排序逻辑：is_completed False < True
                try:
                    self.todos.sort(key=lambda x: (x.get('is_completed', False), x.get('due_date') or '9999'))
                except:
                    pass
                
                # 只保留前8条 (为了美观，减少数量)
                self.todos = self.todos[:8]
                print(f"成功获取 {len(self.todos)} 条Todo")
            else:
                print(f"获取Todo失败: HTTP {response.status_code}")
                
            response.close()
            
        except Exception as err:
            print(f"获取Todo异常: {err}")

    def parse_date_str(self, date_str):
        try:
            if not date_str: return None
            return (int(date_str[0:4]), int(date_str[5:7]), int(date_str[8:10]), 
                   int(date_str[11:13]), int(date_str[14:16]))
        except:
            return None

    def is_overdue(self, due_date_str):
        if not due_date_str: return False
        due = self.parse_date_str(due_date_str)
        if not due: return False
        t = localtime()
        curr = (t[0], t[1], t[2], t[3], t[4])
        return curr > due

    def draw_icon(self, icon_data, x, y, size=8, color=BLACK):
        icon_buf = bytearray(size * size // 8)
        icon_fb = framebuf.FrameBuffer(icon_buf, size, size, framebuf.MONO_HMSB)
        for i in range(len(icon_data)):
            icon_buf[i] = icon_data[i]
            
        # 如果需要反色（画白色图标），需要特殊处理，但blit不支持mask
        # 这里简单实现：如果color是WHITE，我们先画一个黑盒子，然后反色？
        # framebuf比较基础。
        # 简单起见，我们假设图标数据 1=前景。
        # 如果 color=BLACK，直接blit。
        # 如果 color=WHITE，我们手动画像素。
        
        if color == BLACK:
            fb.blit(icon_fb, x, y)
        else:
            for iy in range(size):
                for ix in range(size):
                    if icon_fb.pixel(ix, iy):
                        fb.pixel(x + ix, y + iy, WHITE)

    def draw_badge(self, text, x, y, padding=2):
        """绘制黑底白字的小标签"""
        w = len(text) * 8 + padding * 2
        h = 10 + padding * 2
        # 圆角矩形背景 (黑色)
        fb.fill_rect(x, y, w, h, BLACK)
        # 白色文字
        fb.text(text, x + padding, y + padding, WHITE)
        return w

    def draw_checkbox(self, x, y, checked=False):
        """绘制复选框"""
        size = 14
        # 外框
        fb.rect(x, y, size, size, BLACK)
        fb.rect(x+1, y+1, size-2, size-2, WHITE) # 确保中间是白的
        
        if checked:
            # 绘制对勾
            #   x   x
            #    x x
            #     x
            # 简单的实心方块代替对勾，更符合像素风
            fb.fill_rect(x+3, y+3, size-6, size-6, BLACK)

    def draw_header(self):
        """绘制高级感Header"""
        header_h = 45
        fb.fill_rect(0, 0, config.WIDTH, header_h, BLACK)
        
        # 左侧：APP名称
        self.draw_scaled_text("TASKS", 15, 12, scale=2, color=WHITE)
        
        # 右侧：日期和状态
        t = localtime()
        # 格式: DEC 17
        date_str = f"{MONTHS[t[1]-1].upper()} {t[2]}"
        # 格式: Tuesday
        day_str = WEEKDAYS[t[6]]
        
        # 右对齐
        right_margin = 15
        
        # 绘制日期 (大一点)
        date_w = len(date_str) * 8 * 2
        self.draw_scaled_text(date_str, config.WIDTH - right_margin - date_w, 8, scale=2, color=WHITE)
        
        # 绘制星期 (小一点，在日期下面)
        day_w = len(day_str) * 8
        fb.text(day_str, config.WIDTH - right_margin - day_w, 28, WHITE)
        
        # WiFi图标 (在Header左下角或者中间)
        if self.wifi_connected:
            self.draw_icon(WIFI_ICON, 140, 18, color=WHITE)
        else:
            self.draw_icon(NO_WIFI_ICON, 140, 18, color=WHITE)

    def draw_ui(self):
        """绘制主界面"""
        fb.fill(WHITE)
        self.draw_header()
        
        # === 列表内容 ===
        list_y = 55
        item_h = 30 # 更宽敞的行高
        
        if not self.todos:
            msg = "No tasks for today." if self.wifi_connected else "Connect WiFi to sync."
            fb.text(msg, (config.WIDTH - len(msg)*8)//2, 130, BLACK)
            return

        for i, todo in enumerate(self.todos):
            y = list_y + i * item_h
            
            # 1. 复选框
            is_completed = todo.get('is_completed', False)
            self.draw_checkbox(15, y + 2, is_completed)
            
            # 2. 标题
            title = todo.get('title', '')
            # 截断
            if len(title) > 32: title = title[:30] + "..."
            
            text_x = 40
            text_y = y + 2
            
            # 如果已完成，画删除线
            fb.text(title, text_x, text_y, BLACK)
            if is_completed:
                fb.hline(text_x, text_y + 4, len(title)*8, BLACK)
            
            # 3. 元数据 (截止日期 / 状态)
            due_date = todo.get('due_date')
            meta_y = y + 14
            
            if not is_completed:
                overdue = self.is_overdue(due_date)
                
                if overdue:
                    # 绘制 OVERDUE 标签
                    self.draw_badge("OVERDUE", text_x, meta_y, padding=1)
                elif due_date:
                    # 绘制截止时间
                    d = self.parse_date_str(due_date)
                    if d:
                        time_str = f"{d[1]}/{d[2]} {d[3]:02d}:{d[4]:02d}"
                        self.draw_icon(CLOCK_ICON, text_x, meta_y, size=8, color=BLACK)
                        fb.text(time_str, text_x + 10, meta_y, BLACK)
            
            # 4. 分割线 (极简风格：只在非最后一行画细线)
            if i < len(self.todos) - 1:
                fb.hline(15, y + item_h - 1, config.WIDTH - 30, BLACK)

        # 底部页脚
        footer_y = config.HEIGHT - 15
        count_str = f"{len(self.todos)} items"
        fb.text(count_str, 15, footer_y, BLACK)
        
        # 底部电量/状态栏 (模拟)
        fb.hline(0, footer_y - 2, config.WIDTH, BLACK)

    def draw_scaled_text(self, text, x, y, scale=1, color=BLACK):
        text = str(text)
        char_width = 8
        char_height = 8
        char_buf = bytearray(char_width * char_height // 8)
        char_fb = framebuf.FrameBuffer(char_buf, char_width, char_height, framebuf.MONO_HMSB)
        
        current_x = x
        for char in text:
            char_fb.fill(0)
            char_fb.text(char, 0, 0, 1)
            for cy in range(char_height):
                for cx in range(char_width):
                    if char_fb.pixel(cx, cy):
                        fb.fill_rect(current_x + cx * scale, y + cy * scale, scale, scale, color)
            current_x += char_width * scale

    def run(self):
        print("启动 Todo List 应用 (Premium UI)")
        button_control.init_button_irq()
        self.connect_wifi()
        self.fetch_todos()
        self.draw_ui()
        e.display_frame(buf, global_refresh=True)
        
        while True:
            try:
                if button_control.check_button() == 1:
                    print("退出")
                    return
                if not self.wifi_connected:
                     if self.connect_wifi():
                         self.fetch_todos()
                         self.draw_ui()
                         e.display_frame(buf, global_refresh=True)
                sleep_ms(100)
            except Exception as err:
                print(f"Error: {err}")
                sleep_ms(5000)

if __name__ == "__main__":
    app = TodoApp()
    app.run()
