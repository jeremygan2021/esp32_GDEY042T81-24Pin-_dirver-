import epaper4in2
import config
import wifi
import framebuf
from time import sleep_ms

class WiFiDisplayApp:
    def __init__(self):
        # 初始化墨水屏
        self.e = epaper4in2.EPD(config.spi, config.cs, config.dc, config.rst, config.busy)
        self.e.pwr_on()
        self.e.init()
        
        # 创建帧缓冲区
        self.buf = bytearray(config.WIDTH * config.HEIGHT // 8)
        self.fb = framebuf.FrameBuffer(self.buf, config.WIDTH, config.HEIGHT, framebuf.MONO_HMSB)
        
        # 颜色定义
        self.BLACK = 0
        self.WHITE = 1
        
        # 字体大小（使用内置字体）
        self.font_width = 8
        self.font_height = 10
        
        # 行高
        self.line_height = 16
        
        # 页边距
        self.margin = 20
        
        # 可用文本区域
        self.text_width = config.WIDTH - 2 * self.margin
        self.text_height = config.HEIGHT - 2 * self.margin
        
        # 最大显示行数
        self.max_lines = self.text_height // self.line_height
        
    def clear_screen(self):
        """Clear screen to white"""
        self.fb.fill(self.WHITE)
        
    def draw_title(self, title):
        """Draw title with decorative elements"""
        # 计算标题居中位置
        title_width = len(title) * self.font_width
        x = (config.WIDTH - title_width) // 2
        
        # 绘制装饰线
        self.fb.hline(self.margin, self.margin, 
                    config.WIDTH - 2 * self.margin, self.BLACK)
        
        # 绘制标题
        self.fb.text(title, x, self.margin + 3, self.BLACK)
        
        # 绘制下划线
        self.fb.hline(self.margin, self.margin + self.font_height + 4, 
                    config.WIDTH - 2 * self.margin, self.BLACK)
        
        return self.margin + self.font_height + 12  # 返回下一行的Y坐标
    
    def draw_text(self, text, x, y, max_width=None):
        """Draw text with automatic line wrapping"""
        if max_width is None:
            max_width = self.text_width
            
        # 计算每行最大字符数
        max_chars = max_width // self.font_width
        
        # 如果文本长度超过最大字符数，进行换行
        if len(text) <= max_chars:
            self.fb.text(text, x, y, self.BLACK)
            return y + self.line_height
        else:
            # 分行显示
            lines = []
            for i in range(0, len(text), max_chars):
                lines.append(text[i:i+max_chars])
            
            for line in lines:
                self.fb.text(line, x, y, self.BLACK)
                y += self.line_height
                
            return y
    
    def draw_wifi_list(self, networks):
        """Draw WiFi list with signal icons and better formatting"""
        y = self.draw_title("Available WiFi Networks")
        
        # 显示找到的网络数量
        self.draw_text(f"Found {len(networks)} networks:", self.margin, y)
        y += int(self.line_height * 1.5)  # 修复TypeError，确保为整数
        
        # 绘制分隔线
        self.fb.hline(self.margin, y - 5, config.WIDTH - 2 * self.margin, self.BLACK)
        
        # 显示每个网络
        for i, network in enumerate(networks):
            if y + self.line_height > config.HEIGHT - self.margin:
                break  # 超出屏幕范围
                
            ssid = network[0].decode('utf-8') if isinstance(network[0], bytes) else network[0]
            rssi = network[3]
            
            # 将RSSI转换为信号图标（使用二进制符号）
            if rssi > -40:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x3F\xFF')  # 极强
            elif rssi > -50:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x3F\x7F')  # 非常强
            elif rssi > -55:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x3F\x5F')  # 强
            elif rssi > -60:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x3F\x3F')  # 良好
            elif rssi > -65:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x3F\x1F')  # 中等偏强
            elif rssi > -70:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x1F\x1F')  # 中等
            elif rssi > -75:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x0F\x0F')  # 中等偏弱
            elif rssi > -80:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x0F\x0F\x0F')  # 弱
            else:
                icon = bytearray(b'\x00\x00\x00\x00\x03\x03\x03\x03')  # 极弱
                
            # 显示网络名称和信号图标
            wifi_text = f"{ssid}"
            self.draw_text(wifi_text, self.margin, y)
            
            # 绘制二进制信号图标
            icon_x = config.WIDTH - self.margin - 40  # 图标位置
            icon_height = 8
            for row in range(icon_height):
                byte_val = icon[row] if row < len(icon) else 0
                for col in range(8):
                    if byte_val & (0x80 >> col):
                        x = icon_x + col
                        y_pos = y - (icon_height - row) + 4  # 居中对齐
                        if x < config.WIDTH - self.margin and y_pos >= 0:
                            self.fb.pixel(x, y_pos, self.BLACK)
            
            y += self.line_height
            
            # 添加分隔线（除了最后一项）
            if i < len(networks) - 1 and y + self.line_height <= config.HEIGHT - self.margin:
                self.fb.hline(self.margin, y - 3, config.WIDTH - 2 * self.margin, self.BLACK)
    
    def draw_wifi_success(self):
        """Draw WiFi connection success screen with large signal icon"""
        # 清空屏幕
        self.fb.fill(self.WHITE)
        
        # 获取当前连接的SSID
        try:
            current_ssid = wifi.wifi_manager.wlan.config('ssid')
            if isinstance(current_ssid, bytes):
                current_ssid = current_ssid.decode('utf-8')
        except:
            current_ssid = "Unknown Network"
            
        # 获取信号强度
        try:
            rssi = wifi.wifi_manager.get_signal_strength()
            if rssi is None:
                rssi = -60  # 默认中等信号强度
        except:
            rssi = -60  # 默认中等信号强度
        
        # 显示WiFi名称（放大字体，居中显示）
        large_font_width = 16  # 放大字体宽度
        large_font_height = 24  # 放大字体高度
        ssid_width = len(current_ssid) * large_font_width
        ssid_x = (config.WIDTH - ssid_width) // 2
        ssid_y = 50  # 位置
        
        # 绘制放大的WiFi名称
        for i, char in enumerate(current_ssid):
            x = ssid_x + i * large_font_width
            # 使用简单的像素块绘制字符
            self.fb.text(char, x, ssid_y, self.BLACK)
        
        # 绘制四条竖杠信号图标（居中显示）
        bar_width = 12  # 每条竖杠的宽度
        bar_max_height = 60  # 最高竖杠的高度
        bar_spacing = 8  # 竖杠之间的间距
        bar_y_base = 180  # 竖杠基线位置
        
        # 计算总宽度和起始位置（居中）
        total_width = 4 * bar_width + 3 * bar_spacing
        start_x = (config.WIDTH - total_width) // 2
        
        # 根据信号强度确定显示的竖杠数量
        if rssi > -40:
            bars_to_show = 4  # 极强：显示4条竖杠
        elif rssi > -50:
            bars_to_show = 4  # 非常强：显示4条竖杠
        elif rssi > -55:
            bars_to_show = 4  # 强：显示4条竖杠
        elif rssi > -60:
            bars_to_show = 3  # 良好：显示3条竖杠
        elif rssi > -65:
            bars_to_show = 3  # 中等偏强：显示3条竖杠
        elif rssi > -70:
            bars_to_show = 2  # 中等：显示2条竖杠
        elif rssi > -75:
            bars_to_show = 2  # 中等偏弱：显示2条竖杠
        elif rssi > -80:
            bars_to_show = 1  # 弱：显示1条竖杠
        else:
            bars_to_show = 1  # 极弱：显示1条竖杠
        
        # 绘制竖杠
        for i in range(4):
            x = start_x + i * (bar_width + bar_spacing)
            
            # 计算每条竖杠的高度（递增）
            height = (i + 1) * (bar_max_height // 4)
            
            # 判断是否应该显示这条竖杠
            if i < bars_to_show:
                # 绘制竖杠
                for y in range(height):
                    for px in range(bar_width):
                        self.fb.pixel(x + px, bar_y_base - y, self.BLACK)
            else:
                # 绘制空心竖杠（仅边框）
                for y in range(height):
                    # 左边框
                    self.fb.pixel(x, bar_y_base - y, self.BLACK)
                    # 右边框
                    self.fb.pixel(x + bar_width - 1, bar_y_base - y, self.BLACK)
                
                # 顶部边框
                for px in range(bar_width):
                    self.fb.pixel(x + px, bar_y_base - height, self.BLACK)
        
        # 显示连接成功状态（居中）
        status_text = "Connected Successfully"
        status_width = len(status_text) * self.font_width
        status_x = (config.WIDTH - status_width) // 2
        status_y = bar_y_base + 30  # 位置
        self.fb.text(status_text, status_x, status_y, self.BLACK)
    
    def draw_connected_wifi(self):
        """Draw connected WiFi info with signal icon and better formatting"""
        y = self.draw_title("Connected WiFi")
        
        # 获取WiFi信息
        ssid = wifi.wifi_manager.get_network_info()
        if not ssid:
            self.draw_text("Cannot get WiFi info", self.margin, y)
            return
            
        # 获取当前连接的SSID
        current_ssid = wifi.wifi_manager.wlan.config('ssid')
        if isinstance(current_ssid, bytes):
            current_ssid = current_ssid.decode('utf-8')
            
        # 获取信号强度
        rssi = wifi.wifi_manager.get_signal_strength()
        
        # 绘制分隔线
        self.fb.hline(self.margin, y - 5, config.WIDTH - 2 * self.margin, self.BLACK)
        
        # 显示WiFi名称（居中显示）
        ssid_width = len(current_ssid) * self.font_width
        ssid_x = (config.WIDTH - ssid_width) // 2
        self.fb.text(current_ssid, ssid_x, y + 10, self.BLACK)
        
        # 绘制放大的信号图标（居中显示）
        if rssi is not None:
            # 将RSSI转换为信号图标（使用二进制符号）
            if rssi > -40:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x3F\xFF')  # 极强
            elif rssi > -50:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x3F\x7F')  # 非常强
            elif rssi > -55:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x3F\x5F')  # 强
            elif rssi > -60:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x3F\x3F')  # 良好
            elif rssi > -65:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x3F\x1F')  # 中等偏强
            elif rssi > -70:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x1F\x1F')  # 中等
            elif rssi > -75:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x1F\x0F\x0F')  # 中等偏弱
            elif rssi > -80:
                icon = bytearray(b'\x00\x00\x00\x00\x0F\x0F\x0F\x0F')  # 弱
            else:
                icon = bytearray(b'\x00\x00\x00\x00\x03\x03\x03\x03')  # 极弱
            
            # 绘制放大的信号图标（4倍大小）
            icon_size = 4  # 放大倍数
            icon_height = 8
            icon_width = 8
            icon_x = (config.WIDTH - icon_width * icon_size) // 2  # 居中
            icon_y = y + 40  # 位置
            
            for row in range(icon_height):
                byte_val = icon[row] if row < len(icon) else 0
                for col in range(icon_width):
                    if byte_val & (0x80 >> col):
                        # 绘制放大的像素块
                        for py in range(icon_size):
                            for px in range(icon_size):
                                x = icon_x + col * icon_size + px
                                y_pos = icon_y + row * icon_size + py
                                if x < config.WIDTH and y_pos < config.HEIGHT:
                                    self.fb.pixel(x, y_pos, self.BLACK)
            
            # 显示信号强度文字（居中）
            if rssi > -40:
                signal_text = "Excellent"
            elif rssi > -50:
                signal_text = "Very Strong"
            elif rssi > -55:
                signal_text = "Strong"
            elif rssi > -60:
                signal_text = "Good"
            elif rssi > -65:
                signal_text = "Fairly Strong"
            elif rssi > -70:
                signal_text = "Fair"
            elif rssi > -75:
                signal_text = "Fairly Weak"
            elif rssi > -80:
                signal_text = "Weak"
            else:
                signal_text = "Very Weak"
                
            # 居中显示信号强度文字
            text_width = len(signal_text) * self.font_width
            text_x = (config.WIDTH - text_width) // 2
            self.fb.text(signal_text, text_x, icon_y + icon_height * icon_size + 10, self.BLACK)
            
            # 显示连接成功状态（居中）
            status_text = "Connected Successfully"
            status_width = len(status_text) * self.font_width
            status_x = (config.WIDTH - status_width) // 2
            self.fb.text(status_text, status_x, icon_y + icon_height * icon_size + 30, self.BLACK)
    
    def draw_no_wifi_config(self):
        """Draw WiFi not configured prompt"""
        y = self.draw_title("WiFi Not Configured")
        
        self.draw_text("Please set WiFi name and password in config.py", self.margin, y)
        y += int(self.line_height * 1.5)  # 修复TypeError，确保为整数
        
        self.draw_text("WIFI_SSID = \"your_wifi_name\"", self.margin, y)
        y += self.line_height
        
        self.draw_text("WIFI_PASSWORD = \"your_wifi_password\"", self.margin, y)
        y += int(self.line_height * 1.5)  # 修复TypeError，确保为整数
        
        self.draw_text("Restart device after configuration", self.margin, y)
    
    def run(self):
        """Run WiFi display app"""
        print("WiFi display app started")
        
        try:
            # 检查WiFi是否已配置
            if config.WIFI_SSID == "your_wifi_ssid":
                # WiFi未配置，扫描并显示所有可用网络
                print("WiFi not configured, scanning available networks")
                try:
                    networks = wifi.wifi_manager.scan_networks()
                    # 按信号强度排序
                    networks.sort(key=lambda x: x[3], reverse=True)
                    self.clear_screen()
                    self.draw_wifi_list(networks)
                    # 使用全屏刷新
                    self.e.display_frame(self.buf, global_refresh=True)
                except Exception as e:
                    print(f"扫描网络时出错: {e}")
                    self.clear_screen()
                    self.draw_text("WiFi扫描失败", self.margin, 50)
                    self.draw_text(f"错误: {str(e)}", self.margin, 80)
                    self.e.display_frame(self.buf, global_refresh=True)
                return
                
            # 尝试连接WiFi
            print("Trying to connect to WiFi")
            try:
                if wifi.wifi_manager.connect():
                    print("WiFi connected successfully")
                    # 显示WiFi连接成功界面
                    self.draw_wifi_success()
                else:
                    print("WiFi connection failed, showing available networks")
                    # 连接失败，显示所有可用网络
                    try:
                        networks = wifi.wifi_manager.scan_networks()
                        # 按信号强度排序
                        networks.sort(key=lambda x: x[3], reverse=True)
                        self.clear_screen()
                        self.draw_wifi_list(networks)
                    except Exception as e:
                        print(f"连接失败后扫描网络时出错: {e}")
                        self.clear_screen()
                        self.draw_text("WiFi连接失败", self.margin, 50)
                        self.draw_text("网络扫描也失败", self.margin, 80)
                        self.e.display_frame(self.buf, global_refresh=True)
                        return
            except Exception as e:
                print(f"WiFi连接过程中出错: {e}")
                self.clear_screen()
                self.draw_text("WiFi连接出错", self.margin, 50)
                self.draw_text(f"错误: {str(e)}", self.margin, 80)
                # 尝试显示可用网络
                try:
                    networks = wifi.wifi_manager.scan_networks()
                    networks.sort(key=lambda x: x[3], reverse=True)
                    self.draw_wifi_list(networks)
                except:
                    self.draw_text("无法获取网络列表", self.margin, 110)
                
            # 使用全屏刷新显示内容
            self.e.display_frame(self.buf, global_refresh=True)
            
            print("WiFi display app completed")
        except Exception as e:
            print(f"WiFi显示应用运行时出错: {e}")
            self.clear_screen()
            self.draw_text("应用运行出错", self.margin, 50)
            self.draw_text(f"错误: {str(e)}", self.margin, 80)
            self.e.display_frame(self.buf, global_refresh=True)

# 创建全局应用实例

wifi_display_app = WiFiDisplayApp()