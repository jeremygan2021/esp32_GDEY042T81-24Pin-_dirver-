"""
	Example for 4.2 inch black & white Good Display GDEQ042T81 E-ink screen
	Run on ESP32 / ESPink
	
	优化版本：在第一个图片显示后立即执行全屏刷新，完全解决残影问题
"""

import epaper4in2
import config
from time import sleep_ms

# 选择运行模式：0=原始演示，1=WiFi显示，2=日历应用，3=中文字体测试，4=HTTP图像显示，5=网络测试，6=显示BIN文件
RUN_MODE = 3  # 修改此值以选择不同的应用

if RUN_MODE == 1:
    # 运行WiFi显示应用
    print("启动WiFi显示应用")
    import wifi_display
    wifi_display.wifi_display_app.run()
elif RUN_MODE == 2:
    # 运行日历应用
    print("启动日历应用")
    import calendar
    calendar_app = calendar.CalendarApp()
    calendar_app.run()
elif RUN_MODE == 3:
    # 运行中文字体测试
    print("启动中文字体测试")
    import image
    from image_data import data
    image.run(data, width=400, height=300)
elif RUN_MODE == 4:
    # 运行HTTP图像显示
    print("启动HTTP图像显示")
    import http_image_display
    http_image_display.run()
elif RUN_MODE == 5:
    # 运行网络测试
    print("启动网络诊断测试")
    import test_network
    test_network.run()
elif RUN_MODE == 6:
    # 显示BIN文件
    print("启动BIN文件显示")
    # 读取.bin文件
    f = open('1_latest.bin', 'rb')
    bin_data = bytearray(f.read())
    f.close()
    print("读取BIN文件，大小: " + str(len(bin_data)) + " 字节")
    # 使用image模块显示，400x300是屏幕尺寸
    import image
    image.run(bin_data, width=400, height=300)
else:
    # 运行原始演示
    print("运行原始演示")
    
    e = epaper4in2.EPD(config.spi, config.cs, config.dc, config.rst, config.busy)
    
    e.pwr_on()
    e.init()
    
    w = config.WIDTH
    h = config.HEIGHT
    x = 0
    y = 0
    
    # --------------------
    
    # use a frame buffer
    # 400 * 300 / 8 = 15000
    import framebuf
    buf = bytearray(w * h // 8)
    fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_HMSB)
    black = 0
    white = 1
    fb.fill(white)
    
    # --------------------
    
    # write hello world with black bg and white text
    from image_dark import hello_world_dark
    from image_light import hello_world_light
    print('Image dark')
    bufImage = hello_world_dark
    fbImage = framebuf.FrameBuffer(bufImage, 128, 296, framebuf.MONO_HLSB)
    fb.blit(fbImage, 140, 2)
    bufImage = hello_world_light
    fbImage = framebuf.FrameBuffer(bufImage, 128, 296, framebuf.MONO_HLSB)
    fb.blit(fbImage, 288, 2)
    fb.text("Hola heja",10,10,black)
    ln = 50*100
    buf[ln+0]=255
    buf[ln+1]=0
    buf[ln+2]=255
    buf[ln+3]=0
    buf[ln+4]=0
    buf[ln+5]=0
    buf[ln+1+50]=15
    
    # 显示第一个图片后立即执行全屏刷新，完全解决残影问题
    print("显示第一个图片")
    e.display_frame(buf, partial=False, global_refresh=True)  # 使用全屏刷新模式显示第一个图片
    
    
    sleep_ms(3000)
    
    # 清空屏幕，显示全白
    print("清空屏幕为白色")
    e.clear_screen(double_refresh=False)
    
    print("演示完成")


