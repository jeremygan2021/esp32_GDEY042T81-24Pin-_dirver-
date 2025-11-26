from machine import reset, Pin
from time import sleep_ms
import config

# 从config模块导入按钮引脚配置
btn_pin = config.btn1  # 按钮1连接到引脚46
btn_pin2 = config.btn2  # 按钮2连接到引脚20

# 按钮状态变量
btn_irq_flag = False  # 按钮中断标志
btn_press_time = 0  # 按钮按下时长
long_press_threshold = 3000  # 长按阈值（毫秒）

# 模式数量
MODE_COUNT = 7

# 中断处理函数
def btn_irq_handler(pin):
    global btn_irq_flag
    btn_irq_flag = True

# 初始化按钮中断
def init_button_irq():
    # 设置按钮中断，下降沿触发（按钮按下）
    btn_pin.irq(trigger=Pin.IRQ_FALLING, handler=btn_irq_handler)

# 检测按钮状态变化（引脚46）
# 返回值：0=无操作，1=短按，2=长按
def check_button():
    global btn_irq_flag, btn_press_time
    
    # 检查中断标志
    if btn_irq_flag:
        btn_irq_flag = False
        # 短按检测
        print("按钮被点击")
        return 1  # 短按
    
    # 检查长按
    if btn_pin.value() == 0:  # 按钮持续按下
        btn_press_time += 10
        if btn_press_time >= long_press_threshold:
            btn_press_time = 0
            print("按钮被点击长按")
            return 2  # 长按
    else:
        btn_press_time = 0
    
    return 0

# 主按钮检测函数 - 处理按钮事件
def handle_buttons(current_mode):
    """处理按钮事件，返回新的模式或执行重启"""
    print("等待按钮操作...")
    
    # 初始化按钮中断
    init_button_irq()
    
    while True:
        # 检查按钮状态
        btn_action = check_button()
        if btn_action == 1:  # 短按 - 切换模式
            new_mode = (current_mode + 1) % MODE_COUNT
            return new_mode
        elif btn_action == 2:  # 长按 - 重启
            print("长按检测到，重启设备...")
            sleep_ms(500)
            reset()
        
        # 短暂延迟，降低CPU使用率
        sleep_ms(100)

# 独立测试函数 - 用于测试按钮功能
def test_buttons():
    """独立测试函数，点击按钮后打印收到按键消息"""
    print("按钮测试开始...")
    print("点击按钮46，长按3秒以上重启")
    print("注意：使用中断方式检测按钮")
    
    # 初始化按钮中断
    init_button_irq()
    
    while True:
        # 只检查第一个按钮（引脚46）
        btn_action = check_button()
        if btn_action == 1:  # 短按
            print("收到按钮46短按")
        elif btn_action == 2:  # 长按
            print("收到按钮46长按，重启设备...")
            sleep_ms(500)
            reset()
        
        # 短暂延迟，降低CPU使用率
        sleep_ms(100)

# 如果直接运行该文件，则执行测试
if __name__ == "__main__":
    test_buttons()

