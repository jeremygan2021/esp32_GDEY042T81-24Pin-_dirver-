"""
	Example for 4.2 inch black & white Good Display GDEQ042T81 E-ink screen
	Run on ESP32 / ESPink
	
	优化版本：在第一个图片显示后立即执行全屏刷新，完全解决残影问题
"""


import epaper4in2
import config
import button_control
from time import sleep_ms


# 选择运行模式：0=原始演示，1=WiFi显示，2=日历应用，3=中文字体测试，4=HTTP图像显示，5=网络测试，6=显示BIN文件
RUN_MODE = 0  # 修改此值以选择不同的应用

# 执行当前模式的应用
def run_current_mode(mode):
    if mode == 1:
        # 先运行WiFi显示应用，然后运行日历应用
        print("启动WiFi显示应用")
        import wifi_display
        wifi_display.wifi_display_app.run()
        sleep_ms(8000)
        
        print("启动日历应用")
        import calendar
        calendar_app = calendar.CalendarApp()
        calendar_app.run()
    elif mode == 2:
        # 运行中文字体测试
        print("启动中文字体测试")
        import image
        from image_data import data
        image.run(data, width=400, height=300)
    elif mode == 3:
        # 运行HTTP图像显示
        print("启动HTTP图像显示")
        import http_image_display
        http_image_display.run()
    elif mode == 4:
        # 运行信息看板
        print("启动信息看板")
        import dashboard
        app = dashboard.DashboardApp()
        app.run()
    elif mode == 5:
        # 显示BIN文件
        print("启动BIN文件显示")
        # 读取.bin文件
        f = open('mac.bin', 'rb')
        bin_data = bytearray(f.read())
        f.close()
        print("读取BIN文件，大小: " + str(len(bin_data)) + " 字节")
        # 使用image模块显示，400x300是屏幕尺寸
        import image
        image.run(bin_data, width=400, height=300)
    else:
        # 清空屏幕，显示全白
        print("清空屏幕为白色")
        
        e = epaper4in2.EPD(config.spi, config.cs, config.dc, config.rst, config.busy)
        
        e.pwr_on()
        e.init()
        e.clear_screen(double_refresh=False)
        
        print("演示完成")

# 主程序入口
if __name__ == "__main__":
    current_mode = RUN_MODE
    
    # 模式名称列表
    mode_names = [
        "原始演示",
        "WiFi显示应用",
        "日历应用",
        "中文字体测试",
        "HTTP图像显示",
        "信息看板",
        "显示BIN文件"
    ]
    
    # 持续监听按钮事件
    while True:
        # 打印当前模式
        print(f"\n当前模式: {current_mode} - {mode_names[current_mode]}")
        print("点击按钮切换到下一个程序，长按3秒重启")
        
        # 调用按钮控制模块处理按钮事件
        new_mode = button_control.handle_buttons(current_mode)
        
        # 如果模式发生变化，切换程序
        if new_mode != current_mode:
            current_mode = new_mode
            print(f"切换到模式: {current_mode} - {mode_names[current_mode]}")
        
        # 执行当前模式
        run_current_mode(current_mode)





