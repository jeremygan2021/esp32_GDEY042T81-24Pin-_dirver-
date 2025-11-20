# GDEY042T81 (24Pin) 墨水屏 MicroPython 驱动开发指南

## 概述

本项目提供了Good Display GDEY042T81 4.2英寸电子墨水屏的MicroPython驱动程序。该显示屏具有400x300像素的分辨率，支持黑白显示，适用于ESP32等微控制器。

## 硬件规格

- **型号**: GDEY042T81 (24Pin版本)
- **尺寸**: 4.2英寸
- **分辨率**: 400×300像素
- **显示颜色**: 黑白
- **接口**: SPI
- **工作电压**: 3.3V
- **刷新模式**: 支持全屏刷新和局部刷新

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

## 安装与配置

### 1. 文件结构

将以下文件上传到ESP32：

```
/espdisplay/
├── epaper4in2.py    # 墨水屏驱动程序
├── boot.py          # 主程序示例
├── image_dark.py    # 黑底白字图像数据
└── image_light.py   # 白底黑字图像数据
```

### 2. 驱动初始化

```python
import epaper4in2
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

# 初始化SPI
spi = SPI(2, baudrate=2000000, polarity=0, phase=0, sck=sck, miso=miso, mosi=mosi)

# 电源控制
epd_power = Pin(2, Pin.OUT)
epd_power.on()
sleep_ms(10)

# 初始化墨水屏
e = epaper4in2.EPD(spi, cs, dc, rst, busy)
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

##### `display_frame(buffer, partial=True, x=0, y=0, w=400, h=300)`
显示帧缓冲区内容。

参数：
- `buffer`: 帧缓冲区数据
- `partial`: 是否使用局部刷新模式（默认True）
- `x`: 局部刷新的起始X坐标
- `y`: 局部刷新的起始Y坐标
- `w`: 局部刷新的宽度
- `h`: 局部刷新的高度

##### `clear_screen()`
执行全屏刷新，清除残影。

##### `force_refresh()`
设置强制全屏刷新标志，下次调用`display_frame()`时会执行全屏刷新。

## 使用示例

### 基本显示

```python
import epaper4in2
from machine import Pin, SPI
import framebuf

# 初始化代码（如上所示）

# 创建帧缓冲区
w, h = 400, 300
buf = bytearray(w * h // 8)
fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_HMSB)

# 填充白色背景
fb.fill(1)  # 1表示白色

# 绘制文本
fb.text("Hello World", 50, 50, 0)  # 0表示黑色

# 显示内容
e.display_frame(buf, partial=False)  # 使用全屏刷新
```

### 局部刷新示例

```python
# 初始化代码...

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

### 刷新策略

1. **全屏刷新**：
   - 清除残影效果最好
   - 耗时较长（约2-3秒）
   - 建议在初始显示和定期维护时使用

2. **局部刷新**：
   - 速度快（约0.5秒）
   - 长期使用可能导致残影
   - 适合频繁更新的小区域

3. **混合策略**：
   - 每5-10次局部刷新后执行一次全屏刷新
   - 使用驱动内置的刷新计数器自动管理

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
   - 解决方案：执行全屏刷新 `e.clear_screen()`
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
# 简单动画示例
for i in range(10):
    fb.fill(1)  # 清屏
    x = 50 + i * 10
    fb.text("Moving", x, 50, 0)
    e.display_frame(buf, partial=True, x=40, y=40, w=200, h=30)
    sleep_ms(500)

# 动画结束后执行全屏刷新
e.clear_screen()
```

### 触摸交互（如果支持）

```python
# 假设有触摸输入
def on_touch(x, y):
    # 在触摸位置绘制内容
    fb.fill_rect(x-10, y-10, 20, 20, 0)
    e.display_frame(buf, partial=True, x=x-15, y=y-15, w=30, h=30)
```

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交问题报告和改进建议。

## 参考资料

- [Good Display GDEY042T81 规格书](https://www.good-display.com/product/376.html)
- [MicroPython 官方文档](https://micropython.org/)
- [ESP32 MicroPython 文档](https://docs.micropython.org/en/latest/esp32/quickref.html)