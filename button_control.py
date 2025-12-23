from machine import reset, Pin
from time import sleep_ms
import config
try:
    from buzzer import system_buzzer
except ImportError:
    system_buzzer = None

# 从config模块导入按钮引脚配置
btn_pin = config.btn1  # 按钮1连接到引脚46
btn_pin2 = config.btn2  # 按钮2连接到引脚20

# 按钮状态变量
btn_irq_flag = False  # 按钮中断标志

# 模式数量
MODE_COUNT = 7

# 中断处理函数
def btn_irq_handler(pin):
    global btn_irq_flag
    btn_irq_flag = True
    
    # 点击按钮时停止正在播放的音乐
    if system_buzzer:
        system_buzzer.stop()

# 初始化按钮中断
def init_button_irq():
    # 设置按钮中断，下降沿触发（按钮按下）
    btn_pin.irq(trigger=Pin.IRQ_FALLING, handler=btn_irq_handler)

# 检测按钮状态变化（引脚46）
# 返回值：0=无操作，1=短按
def check_button():
    global btn_irq_flag
    
    # 检查中断标志
    if btn_irq_flag:
        btn_irq_flag = False
        # 短按检测
        print("按钮被点击")
        if system_buzzer:
            system_buzzer.play_click()
        return 1  # 短按
    

    
    return 0

# 主按钮检测函数 - 处理按钮事件
def handle_buttons(current_mode):
    """处理按钮事件，返回新的模式或执行重启"""
    print("等待按钮操作...")
    
    # 清除之前可能残留的中断标志
    global btn_irq_flag
    btn_irq_flag = False
    
    # 初始化按钮中断
    init_button_irq()
    
    # 短暂延迟，忽略初始化瞬间可能产生的噪声
    sleep_ms(200)
    btn_irq_flag = False
    
    while True:
        # 检查按钮状态
        btn_action = check_button()
        if btn_action == 1:  # 短按 - 切换模式
            new_mode = (current_mode + 1) % MODE_COUNT
            return new_mode

        
        # 短暂延迟，降低CPU使用率
        sleep_ms(100)

# 独立测试函数 - 用于测试按钮功能
def test_buttons():
    """独立测试函数，点击按钮后打印收到按键消息"""
    print("按钮测试开始...")
    print("点击按钮46进行短按测试")
    print("注意：使用中断方式检测按钮")
    
    # 初始化按钮中断
    init_button_irq()
    
    while True:
        # 只检查第一个按钮（引脚46）
        btn_action = check_button()
        if btn_action == 1:  # 短按
            print("收到按钮46短按")

        
        # 短暂延迟，降低CPU使用率
        sleep_ms(100)

# 如果直接运行该文件，则执行测试
if __name__ == "__main__":
    test_buttons()

