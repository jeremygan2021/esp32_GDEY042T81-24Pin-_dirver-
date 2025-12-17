#!/usr/bin/env python3
"""
示例：如何在ESP32项目中使用转换后的图片数据
"""

# 假设你已经使用图片转换工具将图片转换为example_image.py
# 其中包含以下内容：
# example_image = bytearray(b'\x00\x00\x00\x0...')

# 1. 导入转换后的图片数据
# from example_image import example_image

# 2. 在image.py中使用图片数据
"""
# image.py 中的示例代码

import framebuf
from machine import Pin, SPI
import epaper4in2
import time
import config

def run(img_data=None):
    # 如果没有提供图片数据，使用默认图片
    if img_data is None:
        # 可以在这里设置默认图片
        img_data = None
    
    try:
        # 初始化墨水屏
        epd = epaper4in2.EPD()
        epd.init()
        
        # 创建帧缓冲区
        buf = bytearray(config.WIDTH * config.HEIGHT // 8)
        fb = framebuf.FrameBuffer(buf, config.WIDTH, config.HEIGHT, framebuf.MONO_HLSB)
        
        if img_data is not None:
            # 使用提供的图片数据
            # 根据图片数据长度判断图片尺寸
            data_length = len(img_data)
            
            # 常见尺寸检查
            if data_length == 128 * 296 // 8:  # 128x296
                img_width, img_height = 128, 296
            elif data_length == 400 * 300 // 8:  # 400x300
                img_width, img_height = 400, 300
            else:
                # 默认尺寸
                img_width, img_height = 400, 300
            
            # 计算居中位置
            x_offset = (config.WIDTH - img_width) // 2
            y_offset = (config.HEIGHT - img_height) // 2
            
            # 将图片数据复制到帧缓冲区
            for y in range(img_height):
                for x in range(img_width):
                    # 计算源位置
                    src_byte_index = y * ((img_width + 7) // 8) + x // 8
                    src_bit_position = 7 - (x % 8)
                    
                    # 获取像素值
                    pixel = (img_data[src_byte_index] >> src_bit_position) & 1
                    
                    # 计算目标位置
                    dst_x = x_offset + x
                    dst_y = y_offset + y
                    
                    if 0 <= dst_x < config.WIDTH and 0 <= dst_y < config.HEIGHT:
                        fb.pixel(dst_x, dst_y, pixel)
        else:
            # 如果没有图片数据，显示测试图案
            fb.fill(0)
            fb.rect(10, 10, config.WIDTH-20, config.HEIGHT-20, 1)
            fb.text("No Image Data", 50, config.HEIGHT//2, 1)
        
        # 显示图片
        epd.display_frame(buf)
        
        # 等待一段时间
        time.sleep(5)
        
        # 清屏并进入深度睡眠
        epd.clear()
        epd.sleep()
        
    except Exception as e:
        print(f"显示图片时出错: {e}")
        # 清屏并进入深度睡眠
        epd.clear()
        epd.sleep()
"""

# 3. 在boot.py中设置RUN_MODE=3
"""
# boot.py 中的示例代码

import machine
import time
import config

# 设置运行模式
# 0: 正常运行模式
# 1: WiFi连接模式
# 2: 配置模式
# 3: 图片显示模式
RUN_MODE = 3

if RUN_MODE == 3:
    # 导入图片数据
    from example_image import example_image
    
    # 导入图片显示模块
    import image
    
    # 显示图片
    image.run(example_image)
"""

# 4. 使用不同的图片
"""
# 你可以根据需要导入不同的图片数据

# 显示黑色背景白色文本的图片
from example_dark import example_dark
image.run(example_dark)

# 显示白色背景黑色文本的图片
from example_light import example_light
image.run(example_light)

# 显示旋转的图片
from example_rotated import example_rotated
image.run(example_rotated)

# 显示文本图片
from hello_text import hello_text
image.run(hello_text)
"""

# 5. 动态选择图片
"""
# 你可以根据条件动态选择要显示的图片

def display_image_by_condition(condition):
    if condition == "dark":
        from example_dark import example_dark
        return example_dark
    elif condition == "light":
        from example_light import example_light
        return example_light
    elif condition == "rotated":
        from example_rotated import example_rotated
        return example_rotated
    else:
        from hello_text import hello_text
        return hello_text

# 使用示例
img_data = display_image_by_condition("dark")
image.run(img_data)
"""

print("这是一个示例文件，展示了如何在ESP32项目中使用转换后的图片数据。")
print("请参考注释中的代码示例，根据你的实际需求进行修改。")