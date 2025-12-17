# GDEY042T81 (24Pin) 墨水屏 MicroPython 驱动开发指南

## 概述

本项目提供了Good Display GDEY042T81 4.2英寸电子墨水屏的MicroPython驱动程序。该显示屏具有400x300像素的分辨率，支持黑白显示，适用于ESP32等微控制器。驱动程序经过优化，有效解决了墨水屏常见的残影问题，并提供了灵活的刷新控制策略。

项目特点：
- 统一的引脚配置管理
- 智能刷新策略，自动防止残影积累
- 内置日历应用，支持时段变化刷新
- 模块化设计，易于扩展

## 硬件规格

- **型号**: GDEY042T81 (24Pin版本)
- **尺寸**: 4.2英寸
- **分辨率**: 400×300像素
- **显示颜色**: 黑白
- **接口**: SPI
- **工作电压**: 3.3V
- **刷新模式**: 支持全屏刷新和局部刷新
- **残影控制**: 内置智能刷新策略，自动防止残影积累

## 硬件连接

### 使用C02转接板的连接方式

| 引脚 | ESP32引脚 | 功能 |
|------|-----------|------|
| VCC  | 3.3V      | 电源正极 |
| GND  | GND       | 电源负极 |
| DIN  | GPIO21    | SPI MOSI |
| CLK  | GPIO47    | SPI SCK |
| CS   | GPIO45    | 片选信号 |
| DC   | GPIO40    | 数据/命令选择 |
| RST  | GPIO41    | 复位信号 |
| BUSY | GPIO42    | 忙碌状态指示 |
| MISO | GPIO46    | SPI MISO |

### 电源控制

- 使用GPIO2控制墨水屏电源：`epd_power = Pin(2, Pin.OUT)`

## 软件环境

- MicroPython固件
- ESP32开发板
- 支持的库：
  - `machine` - 硬件控制
  - `framebuf` - 帧缓冲区
  - `time` - 时间控制
  - `network` - WiFi网络连接
  - `urequests` - HTTP请求（可选）

## WiFi配置

如果需要网络功能，请在`config.py`中添加以下WiFi配置：

```python
# WiFi配置
WIFI_SSID = "your_wifi_ssid"  # 替换为你的WiFi名称
WIFI_PASSWORD = "your_wifi_password"  # 替换为你的WiFi密码
WIFI_TIMEOUT = 10000  # WiFi连接超时时间(毫秒)

def connect_wifi():
    import network
    import time
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('正在连接WiFi...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # 等待连接
        timeout = WIFI_TIMEOUT
        while not wlan.isconnected() and timeout > 0:
            time.sleep_ms(100)
            timeout -= 100
            
    if wlan.isconnected():
        print('WiFi连接成功')
        print('网络配置:', wlan.ifconfig())
        return True
    else:
        print('WiFi连接失败')
        return False
```

使用方法：
```python
import config

# 连接WiFi
if config.connect_wifi():
    print("网络已就绪，可以进行网络操作")
else:
    print("网络连接失败，使用离线模式")
```

## 安装与配置

### 1. 文件结构

将以下文件上传到ESP32：

```
/espdisplay/
├── config.py        # 统一配置文件（引脚、屏幕尺寸等）
├── epaper4in2.py    # 墨水屏驱动程序
├── boot.py          # 主程序示例
├── calendar.py      # 日历应用
├── image_dark.py    # 黑底白字图像数据
└── image_light.py   # 白底黑字图像数据
```

### 2. 统一配置

本项目使用`config.py`文件统一管理所有硬件配置，包括引脚定义和屏幕参数：

```python
# config.py 内容示例
from machine import Pin, SPI
from time import sleep_ms

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
```

### 3. 驱动初始化

```python
import epaper4in2
import config  # 导入统一配置

# 使用config中的配置初始化墨水屏
e = epaper4in2.EPD(config.spi, config.cs, config.dc, config.rst, config.busy)
e.pwr_on()
e.init()
```

## API参考

### EPD类

#### 初始化
```python
e = epaper4in2.EPD(spi, cs, dc, rst, busy)
```

#### 主要方法

##### `pwr_on()`
打开墨水屏电源。

##### `pwr_off()`
关闭墨水屏电源。

##### `init()`
初始化墨水屏，设置基本参数。

##### `display_frame(frame_buffer, partial=False, x=0, y=0, w=None, h=None, global_refresh=False)`
显示帧缓冲区内容。

参数：
- `frame_buffer`: 帧缓冲区数据
- `partial`: 是否使用局部刷新模式（默认False）
- `x`: 局部刷新的起始X坐标（默认0）
- `y`: 局部刷新的起始Y坐标（默认0）
- `w`: 局部刷新的宽度（默认全屏宽度）
- `h`: 局部刷新的高度（默认全屏高度）
- `global_refresh`: 是否使用全局刷新模式（默认False）

##### `clear_screen(double_refresh=True)`
执行全屏刷新，清除残影。

参数：
- `double_refresh`: 是否执行两次刷新以彻底清除残影（默认True）

##### `force_refresh()`
设置强制全屏刷新标志，下次调用`display_frame()`时会执行全屏刷新。

## 刷新策略

### 自动残影控制

驱动内置了智能刷新策略，自动管理刷新模式以防止残影：

1. **刷新计数器**：跟踪局部刷新次数
2. **自动全屏刷新**：每5次局部刷新后自动执行一次全屏刷新
3. **强制全屏刷新**：可通过`force_refresh()`方法强制执行全屏刷新

### 刷新模式对比

| 刷新模式 | 速度 | 残影控制 | 适用场景 |
|---------|------|---------|---------|
| 全屏刷新 | 慢(2-3秒) | 最好 | 初始显示、定期维护 |
| 局部刷新 | 快(0.5秒) | 一般 | 频繁更新小区域 |
| 双次全屏刷新 | 最慢(4-6秒) | 最佳 | 彻底清除残影 |

## 使用示例

### 基本显示

```python
import epaper4in2
import config
import framebuf

# 初始化墨水屏
e = epaper4in2.EPD(config.spi, config.cs, config.dc, config.rst, config.busy)
e.pwr_on()
e.init()

# 创建帧缓冲区
buf = bytearray(config.WIDTH * config.HEIGHT // 8)
fb = framebuf.FrameBuffer(buf, config.WIDTH, config.HEIGHT, framebuf.MONO_HMSB)

# 填充白色背景
fb.fill(1)  # 1表示白色

# 绘制文本
fb.text("Hello World", 50, 50, 0)  # 0表示黑色

# 显示内容
e.display_frame(buf, partial=False)  # 使用全屏刷新
```

### 日历应用

本项目包含一个完整的日历应用，支持时段变化自动刷新：

```python
import calendar

# 直接运行日历应用
calendar_app = calendar.CalendarApp()
calendar_app.run()
```

日历应用特点：
- 自动检测时段变化（Morning/Noon/Afternoon/Evening/Night）
- 只在时段变化时执行全屏刷新，节省功耗
- 美观的日历界面，显示当前日期和时段
- 内置时段图标，直观显示当前时段

### 局部刷新示例

```python
# 全屏显示初始内容
e.display_frame(buf, partial=False)

# 局部更新特定区域
fb.text("Updated", 50, 100, 0)
e.display_frame(buf, partial=True, x=40, y=90, w=200, h=30)
```

### 防止残影的最佳实践

```python
# 显示第一个图片后立即执行全屏刷新
e.display_frame(buf, partial=False)

# 再次执行全屏刷新，确保彻底清除所有可能的残影
e.clear_screen()

# 后续可以使用局部刷新
for i in range(5):
    # 更新内容
    fb.text(f"Update #{i}", 50, 50, 0)
    # 使用局部刷新
    e.display_frame(buf, partial=True, x=40, y=40, w=200, h=30)
    sleep_ms(1000)

# 定期执行全屏刷新防止残影积累
e.clear_screen()
```

### 使用全局刷新模式

```python
# 使用全局刷新模式显示内容
e.display_frame(buf, global_refresh=True)

# 清空屏幕为白色
e.clear_screen(double_refresh=True)
```

## 图像处理

### 创建黑白图像

1. 使用图像处理软件创建400x300像素的黑白图像
2. 转换为字节数组：

```python
# 示例：将图像转换为字节数组
def image_to_bytearray(image_path):
    # 这里需要实现图像到字节数组的转换
    # 可以使用PIL等库在PC上预处理，然后保存为.py文件
    pass
```

### 使用预处理的图像

```python
# 导入预处理的图像数据
from my_image import my_image_data

# 创建帧缓冲区
img_fb = framebuf.FrameBuffer(my_image_data, 400, 300, framebuf.MONO_HMSB)

# 复制到主缓冲区
fb.blit(img_fb, 0, 0)

# 显示
e.display_frame(buf)
```

## 性能优化

### 刷新策略建议

1. **初始化阶段**：
   - 使用全屏刷新显示初始内容
   - 执行一次`clear_screen()`确保无残影

2. **频繁更新阶段**：
   - 使用局部刷新更新小区域
   - 让驱动自动管理刷新计数器

3. **维护阶段**：
   - 定期执行`clear_screen()`清除残影
   - 或使用`force_refresh()`强制下次全屏刷新

### 电源管理

```python
# 不使用时关闭电源
e.pwr_off()

# 重新使用时打开电源
e.pwr_on()
e.init()  # 需要重新初始化
```

## 故障排除

### 常见问题

1. **显示不清晰或有残影**
   - 解决方案：执行双次全屏刷新 `e.clear_screen(double_refresh=True)`
   - 预防措施：定期执行全屏刷新，避免连续多次局部刷新

2. **屏幕无响应**
   - 检查硬件连接
   - 确认电源已开启
   - 尝试复位：`e.init()`

3. **显示内容错位**
   - 检查帧缓冲区尺寸是否正确（400x300）
   - 确认framebuf模式是否正确（MONO_HMSB）

4. **局部刷新效果不佳**
   - 确保刷新区域参数正确
   - 尝试扩大刷新区域
   - 考虑使用全屏刷新

### 调试技巧

```python
# 添加调试输出
print("初始化墨水屏...")
e.init()
print("初始化完成")

# 检查忙碌状态
if busy.value() == 0:
    print("墨水屏忙碌")
else:
    print("墨水屏就绪")
```

## 高级应用

### 动画效果

```python
## WiFi模块使用

本项目包含一个WiFi管理模块(`wifi.py`)，提供便捷的WiFi连接和管理功能。

### 基本使用

```python
import wifi

# 连接到WiFi
if wifi.wifi_manager.connect():
    print("WiFi连接成功")
    print("IP地址:", wifi.wifi_manager.get_ip())
else:
    print("WiFi连接失败")
```

### 高级功能

```python
import wifi

# 扫描可用网络
networks = wifi.wifi_manager.scan_networks()
for net in networks:
    print(f"SSID: {net[0]}, 信号强度: {net[3]}")

# 获取网络信息
if wifi.wifi_manager.is_connected():
    ip_info = wifi.wifi_manager.get_network_info()
    print(f"IP: {ip_info[0]}")
    print(f"子网掩码: {ip_info[1]}")
    print(f"网关: {ip_info[2]}")
    
    # 获取信号强度
    rssi = wifi.wifi_manager.get_signal_strength()
    print(f"信号强度: {rssi} dBm")

# 断开连接
wifi.wifi_manager.disconnect()
```

### WiFi模块API

#### WiFiManager类

- `connect(ssid=None, password=None, timeout=None)`: 连接到WiFi网络
- `disconnect()`: 断开WiFi连接
- `is_connected()`: 检查连接状态
- `get_ip()`: 获取当前IP地址
- `get_network_info()`: 获取完整网络配置信息
- `scan_networks()`: 扫描可用WiFi网络
- `get_signal_strength()`: 获取当前连接的信号强度

## 网络应用示例

### 获取网络时间

```python
import wifi
import urequests
import ujson

# 连接WiFi
if wifi.wifi_manager.connect():
    # 获取网络时间
    try:
        response = urequests.get("http://worldtimeapi.org/api/ip")
        if response.status_code == 200:
            data = ujson.loads(response.text)
            datetime = data["datetime"]
            print(f"当前时间: {datetime}")
        response.close()
    except Exception as e:
        print(f"获取时间失败: {e}")
```

### HTTP请求示例

```python
import wifi
import urequests

# 连接WiFi
if wifi.wifi_manager.connect():
    # 发送GET请求
    try:
        response = urequests.get("https://api.example.com/data")
        if response.status_code == 200:
            data = response.text
            print(f"响应数据: {data}")
        response.close()
    except Exception as e:
        print(f"请求失败: {e}")
```

## WiFi显示应用

本项目包含一个WiFi显示应用(`wifi_display.py`)，可以在墨水屏上显示WiFi网络信息。

### 功能特点

- 根据config.py中的WiFi配置状态显示不同内容
- 如果WiFi未配置，显示所有可用网络列表及其信号强度
- 如果WiFi已配置且连接成功，显示已连接WiFi的详细信息
- 支持密码部分隐藏显示（只显示前两位和后两位，中间用****代替）
- 自动按信号强度排序网络列表

### 使用方法

1. 在`boot.py`中设置`RUN_MODE = 1`以启动WiFi显示应用
2. 上传代码到ESP32并重启设备

### 显示内容

#### WiFi未配置时
- 显示"WiFi未配置"提示
- 显示配置说明和示例代码

#### WiFi已配置但连接失败时
- 显示所有可用的WiFi网络
- 按信号强度从强到弱排序
- 显示每个网络的名称和信号强度

#### WiFi连接成功时
- 显示已连接的WiFi名称
- 显示密码（部分隐藏）
- 显示信号强度和IP地址
- 显示连接状态

### 代码示例

```python
import wifi_display

# 创建并运行WiFi显示应用
app = wifi_display.WiFiDisplayApp()
app.run()
```

## 简单动画示例
for i in range(10):
    fb.fill(1)  # 清屏
    x = 50 + i * 10
    fb.text("Moving", x, 50, 0)
    e.display_frame(buf, partial=True, x=40, y=40, w=200, h=30)
    sleep_ms(500)

# 动画结束后执行全屏刷新
e.clear_screen()
```

### 自定义应用开发

基于本项目开发自定义应用时，建议遵循以下模式：

```python
import epaper4in2
import config
import framebuf
from time import sleep_ms

class CustomApp:
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
        
        # 应用状态
        self.last_refresh_time = 0
        
    def need_refresh(self):
        """判断是否需要刷新屏幕"""
        # 实现自定义刷新逻辑
        return True
        
    def draw_screen(self):
        """绘制屏幕内容"""
        # 实现自定义绘制逻辑
        self.fb.fill(self.WHITE)
        self.fb.text("Custom App", 50, 50, self.BLACK)
        
    def display(self):
        """显示内容"""
        if self.need_refresh():
            self.draw_screen()
            self.e.display_frame(self.buf, global_refresh=True)
            
    def run(self):
        """运行应用主循环"""
        while True:
            self.display()
            sleep_ms(60000)  # 每分钟检查一次
```

### 触摸交互（如果支持）

```python
# 假设有触摸输入
def on_touch(x, y):
    # 在触摸位置绘制内容
    fb.fill_rect(x-10, y-10, 20, 20, 0)
    e.display_frame(buf, partial=True, x=x-15, y=y-15, w=30, h=30)
```

## 项目扩展

### 添加新的显示内容

1. 创建新的图像文件：
   ```python
   # new_image.py
   new_image_data = bytearray([...])  # 图像数据
   ```

2. 在应用中使用：
   ```python
   from new_image import new_image_data
   
   # 创建帧缓冲区并显示
   img_fb = framebuf.FrameBuffer(new_image_data, width, height, framebuf.MONO_HMSB)
   fb.blit(img_fb, x, y)
   ```

### 修改引脚配置

要修改引脚配置，只需编辑`config.py`文件：

```python
# 修改SPI引脚
sck = Pin(18)   # 改为GPIO18
miso = Pin(19)  # 改为GPIO19
mosi = Pin(23)  # 改为GPIO23

# 修改控制引脚
dc = Pin(22)    # 改为GPIO22
cs = Pin(5)     # 改为GPIO5
rst = Pin(4)    # 改为GPIO4
busy = Pin(21)  # 改为GPIO21
```

修改后，所有使用这些引脚的文件都会自动使用新的配置，无需逐个修改。

## 贡献

欢迎提交问题报告和功能请求！如果您想贡献代码，请遵循以下步骤：

1. Fork 本仓库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 更新日志

### v1.1.0 (最新版本)
- 添加统一的引脚配置管理（config.py）
- 实现智能刷新策略，减少残影问题
- 新增内置日历应用，支持时段变化自动刷新
- 优化代码结构，提高可维护性
- 完善文档和使用示例

### v1.0.0
- 初始版本发布
- 基本的4.2寸墨水屏驱动功能
- 支持全屏和局部刷新模式

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 致谢

- 感谢 Good Display 提供的墨水屏技术支持和规格说明
- 感谢 MicroPython 社区提供的优秀框架和工具
- 感谢所有为本项目做出贡献的开发者

## 联系方式

如果您有任何问题或建议，可以通过以下方式联系：

- 提交 [Issue](https://github.com/yourusername/espdisplay/issues)
- 发送邮件至：your.email@example.com

---

**注意**：使用墨水屏时请注意避免频繁刷新，以延长屏幕寿命。建议在长时间使用后定期执行全屏刷新，以防止残影积累。

## 参考资料

- [Good Display GDEY042T81 产品规格书](https://www.good-display.cn/product/386.html)
- [MicroPython 官方文档](https://docs.micropython.org/)
- [ESP32 开发指南](https://docs.espressif.com/projects/esp-idf/zh_CN/latest/esp32/)