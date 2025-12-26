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
import gc

# 选择运行模式：0=原始演示，1=WiFi显示，2=中文字体测试，3=HTTP图像显示，4=信息看板，5=显示BIN文件，6=Todo List
RUN_MODE = 0  # 默认启动 	Todo List

import sys
import machine

# 清理缓存函数
def clear_cache():
    """清理所有非必要模块的缓存，释放内存"""
    print("执行深度内存清理...")
    # 需要清理的模块列表
    modules_to_clear = [
        'wifi_display', 'calendar', 'image', 'http_image_display', 
        'dashboard', 'todo_list', 'image_data', 'image_dark'
    ]
    
    for m in modules_to_clear:
        if m in sys.modules:
            try:
                del sys.modules[m]
                print(f"已卸载模块: {m}")
            except Exception as e:
                print(f"卸载模块 {m} 失败: {e}")
                
    gc.collect()
    print(f"内存清理完成，当前空闲: {gc.mem_free()} 字节")

# 执行当前模式的应用
def run_current_mode(mode):
    # 运行前进行垃圾回收
    gc.collect()
    
    # Play startup sound for the new mode
    if system_buzzer:
        system_buzzer.play_startup()
        # 增加延迟并清除可能因声音干扰产生的按钮中断
        sleep_ms(500)
        button_control.btn_irq_flag = False

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
        sleep_ms(1500)
        print("\n播放音乐6")
        system_buzzer.play_song(config.PLAY_SONG_INDEX)
        sleep_ms(3000)
    elif mode == 3:
        # 运行HTTP图像显示
        print("启动HTTP图像显示")
        import http_image_display
        http_image_display.run()
        sleep_ms(1500)
        print("\n播放音乐6")
        system_buzzer.play_song(6)
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
        import os
        try:
            gc.collect() # 读取大文件前回收内存
            stat = os.stat('mac.bin')
            size = stat[6]
            print(f"文件大小: {size} 字节")
            
            f = open('mac.bin', 'rb')
            # 尝试预分配
            try:
                bin_data = bytearray(size)
                f.readinto(bin_data)
                f.close()
                print("读取BIN文件成功")
                
                # 使用image模块显示，400x300是屏幕尺寸
                import image
                # 再次回收，为image模块内部buffer腾出空间
                gc.collect() 
                image.run(bin_data, width=400, height=300)
                
                # 运行完立即释放bin_data
                bin_data = None
                gc.collect()
                
                sleep_ms(2000)
            except MemoryError:
                print("内存不足，无法读取或显示BIN文件")
                if 'f' in locals(): f.close()
                
        except OSError as e:
            print(f"Error reading mac.bin: {e}")
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
        # 增加延迟并清除可能因声音干扰产生的按钮中断
        sleep_ms(500)
        button_control.btn_irq_flag = False

    # Clean up memory after mode execution
    gc.collect()
    print(f"Free memory: {gc.mem_free()} bytes")

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
            
            # 如果切换回模式0，执行深度清理
            if current_mode == 0:
                clear_cache()
                # 播放专属的 Macintosh 关机音频
                try:
                    if system_buzzer:
                        system_buzzer.play_song(28, unstoppable=True)
                        sleep_ms(2500)
                except:
                    pass
                print("即将重启以释放内存")
                # 关闭墨水屏电源（如有）
                try:
                    config.epd_power.off()
                except:
                    pass
                sleep_ms(500)
                machine.reset()
        
        # 执行当前模式
        run_current_mode(current_mode)







