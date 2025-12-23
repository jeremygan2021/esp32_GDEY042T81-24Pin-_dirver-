"""
	Example for 4.2 inch black & white Good Display GDEQ042T81 E-ink screen
	Run on ESP32 / ESPink
	
	优化版本：在第一个图片显示后立即执行全屏刷新，完全解决残影问题
"""


import epaper4in2
import config
import button_control
from time import sleep_ms
from buzzer import system_buzzer

# 选择运行模式：0=原始演示，1=WiFi显示，2=中文字体测试，3=HTTP图像显示，4=信息看板，5=显示BIN文件，6=Todo List
RUN_MODE = 0  # 默认启动 	Todo List

# 执行当前模式的应用
def run_current_mode(mode):
    # Play startup sound for the new mode
    if system_buzzer:
        system_buzzer.play_startup()

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
        sleep_ms(3000)
    elif mode == 2:
        # 运行中文字体测试
        print("启动中文字体测试")
        import image
        from image_data import data
        image.run(data, width=400, height=300)
        sleep_ms(3000)
    elif mode == 3:
        # 运行HTTP图像显示
        print("启动HTTP图像显示")
        import http_image_display
        http_image_display.run()
        sleep_ms(3000)
    elif mode == 4:
        # 运行信息看板
        print("启动信息看板")
        import dashboard
        app = dashboard.DashboardApp()
        app.run()
        sleep_ms(2000)
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
        sleep_ms(2000)
    elif mode == 6:
        # 运行Todo List
        print("启动Todo List")
        import todo_list
        app = todo_list.TodoApp()
        app.run()
    else:
        # 清空屏幕，显示全白
        print("清空屏幕为白色")
        
        e = epaper4in2.EPD(config.spi, config.cs, config.dc, config.rst, config.busy)
        
        e.pwr_on()
        e.init()
        e.clear_screen(double_refresh=False)
        
        print("演示完成")

    # Play shutdown/completion sound after mode finishes
    if system_buzzer:
        system_buzzer.play_shutdown()

# 主程序入口
if __name__ == "__main__":
    current_mode = RUN_MODE
    
    # 模式名称列表
    mode_names = [
        "原始演示",
        "WiFi显示+日历",
        "中文字体测试",
        "HTTP图像显示",
        "信息看板",
        "显示BIN文件",
        "Todo List"
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









