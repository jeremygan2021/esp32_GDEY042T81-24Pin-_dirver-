"""
图片显示模块
用于显示传入的二进制图片数据
"""
import epaper4in2
import config
import framebuf
from time import sleep_ms

def run(image_data=None, width=128, height=296):
    """显示传入的图片二进制数据
    
    参数:
        image_data: 图片的二进制数据，如果为None则使用默认的image_dark图片
    """
    print("启动图片显示应用")
    
    # 如果没有传入图片数据，则使用默认的image_dark图片
    if image_data is None:
        from image_dark import hello_world_dark
        image_data = hello_world_dark
        print("使用默认的image_dark图片")
    else:
        print("使用传入的图片数据")
    
    # 初始化墨水屏
    e = epaper4in2.EPD(config.spi, config.cs, config.dc, config.rst, config.busy)
    e.pwr_on()
    e.init()
    
    # 获取屏幕尺寸
    w = config.WIDTH
    h = config.HEIGHT
    
    # 创建帧缓冲区
    buf = bytearray(w * h // 8)
    fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_HMSB)
    
    # 设置背景为白色
    black = 0
    white = 1
    fb.fill(white)
    
    # 加载并显示图片
    print("显示图片")
    
    # 确保image_data是bytearray类型
    if isinstance(image_data, bytes):
        bufImage = bytearray(image_data)
    else:
        bufImage = image_data
    
    # 检查图片数据大小是否正确
    expected_size = width * height // 8
    if len(bufImage) != expected_size:
        print(f"警告: 图片数据大小不匹配，预期 {expected_size} 字节，实际 {len(bufImage)} 字节")
    
    fbImage = framebuf.FrameBuffer(bufImage, width, height, framebuf.MONO_HLSB)
    
    # 将图片放置在屏幕中央
    x_offset = (w - width) // 2
    y_offset = (h - height) // 2
    fb.blit(fbImage, x_offset, y_offset)
    
    # 显示图片，使用全屏刷新模式确保没有残影
    e.display_frame(buf, partial=False, global_refresh=True)
    
    print("图片显示完成")
