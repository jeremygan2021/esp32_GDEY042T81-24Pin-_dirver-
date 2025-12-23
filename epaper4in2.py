"""
MicroPython Good Display GDEQ042T81 (GDEY042T81)

Based on MicroPython Waveshare 4.2" Black/White GDEW042T2 e-paper display driver
https://github.com/mcauser/micropython-waveshare-epaper

licensed under the MIT License
Copyright (c) 2017 Waveshare
Copyright (c) 2018 Mike Causer
"""

"""
MicroPython Good Display GDEQ042T81 (GDEY042T81) e-paper display driver

MIT License
Copyright (c) 2024 Martin Maly

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from micropython import const
from time import sleep_ms
try:
    from buzzer import system_buzzer
except ImportError:
    system_buzzer = None

# Display resolution
EPD_WIDTH  = const(400)
EPD_HEIGHT = const(300)
BUSY = const(0)  # 0=busy, 1=idle

class EPD:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.busy.init(self.busy.IN)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.powered = False
        self.init_done = False
        self.hibernate = True
        self.use_fast_update = True
        # 添加刷新计数器，用于控制全屏刷新频率
        self.refresh_count = 0
        # 每N次局部刷新后执行一次全屏刷新，防止残影积累
        self.partial_refresh_limit = 5
        # 强制全屏刷新标志
        self.force_full_refresh = False

    def _command(self, command, data=None):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)
        
    def _ndata(self, data):
        self._data(bytearray([data]))
        
    def pwr_on(self):
        if self.powered == False:
            self._command(0x22, b'\xe0')
            self._command(0x20)
            self.wait_until_idle()
            self.powered = True

    def pwr_off(self):
        if self.powered == True:
            self._command(0x22, b'\x83')
            self._command(0x20)
            self.wait_until_idle()
            self.powered = False

    #set partial
    def set_partial(self, x, y, w, h):
        self._command(0x11,b'\x03')
        self._command(0x44)
        self._ndata(x // 8)
        self._ndata((x + w - 1) // 8)
        self._command(0x45)
        self._ndata(y % 256)        
        self._ndata(y // 256)
        self._ndata((y+h-1) % 256)
        self._ndata((y+h-1) // 256)
        self._command(0x4E)
        self._ndata(x // 8)
        self._command(0x4F)
        self._ndata(y % 256)        
        self._ndata(y // 256)

    def init(self):
        if self.hibernate==True:
            self.reset()
        sleep_ms(100)
        #self.wait_until_idle()
        self._command(const(0x12)) #SWRESET
        self.wait_until_idle()
        
        # 优化驱动初始化参数，确保与GDEY042T81规格匹配
        self._command(0x01,b'\x2B\x01\x00') #MUX 设置
        self._command(0x21,b'\x40\x00')      # 显示更新控制
        self._command(0x3C,b'\x05')         # 边界波形控制，减少残影
        self._command(0x18,b'\x80')         # 读取内部温度传感器
        self._command(0x0C,b'\x8B\x00\x00') # 设置开始和结束阶段，优化刷新
        
        self.set_partial(0, 0, self.width, self.height)
        self.init_done = True

    def wait_until_idle(self):
        while self.busy.value() == BUSY:
            sleep_ms(100)
            print("等待墨水屏空闲")

    def reset(self):
        self.rst(0)
        sleep_ms(200)
        self.rst(1)
        sleep_ms(200)

    def update_full(self):
        #update Full
        print("执行全屏更新")
        self._command(0x21,b'\x40\x00')
        if self.use_fast_update == False:
            self._command(0x22,b'\xf7')
        else:
            self._command(0x1A, b'\x64')  # 快速刷新设置
            self._command(0x22,b'\xd7')
        self._command(0x20)
        self.wait_until_idle()
        print("更新完成", self.busy.value())

    # 添加专门的全屏刷新方法，用于清除残影
    def clear_screen(self, double_refresh=True):
        """执行全屏刷新以清除残影
        
        参数:
            double_refresh: 是否执行两次刷新以彻底清除残影，默认为True
        """
        if double_refresh:
            print("执行双次全屏刷新以彻底清除残影")
        else:
            print("执行单次全屏刷新以清除残影")
            
        # 创建全白缓冲区
        white_buffer = bytearray(self.width * self.height // 8)
        for i in range(len(white_buffer)):
            white_buffer[i] = 0xFF  # 全白
            
        # 先写入全白数据
        self.set_partial(0, 0, self.width, self.height)
        self.write_image(0x24, white_buffer, True, True)
        
        # 执行第一次全屏刷新
        self._command(0x21,b'\x40\x00')
        self._command(0x22,b'\xf7')  # 使用完整刷新模式
        self._command(0x20)
        self.wait_until_idle()
        
        # 如果启用双次刷新，再执行一次
        if double_refresh:
            print("执行第二次全屏刷新")
            self._command(0x21,b'\x40\x00')
            self._command(0x22,b'\xf7')  # 使用完整刷新模式
            self._command(0x20)
            self.wait_until_idle()
        
        # 重置刷新计数器
        self.refresh_count = 0
        self.force_full_refresh = False
        print("全屏刷新完成")

    def write_image(self, command, bitmap, mirror_x, mirror_y):
        sleep_ms(1)
        h = self.height
        w = self.width
        bpl = w // 8 # bytes per line
        
        self._command(command)
        for i in range(0, h):
            for j in range(0, bpl):
                idx = ((bpl-j-1) if mirror_x else j) + ((h-i-1) if mirror_y else i) * bpl
                self._ndata(bitmap[idx])
                
    def write_value(self, command, value):
        sleep_ms(1)
        h = self.height
        w = self.width
        bpl = w // 8 # bytes per line
        
        self._command(command)
        for i in range(0, h):
            for j in range(0, bpl):
                self._ndata(value)

    # 修改显示方法，添加刷新控制逻辑
    def display_frame(self, frame_buffer, partial=False, x=0, y=0, w=None, h=None, global_refresh=False):
        """显示帧缓冲区内容
        
        参数:
            frame_buffer: 要显示的帧缓冲区数据
            partial: 是否使用局部刷新模式，默认为False
            x: 局部刷新的起始X坐标，默认为0
            y: 局部刷新的起始Y坐标，默认为0
            w: 局部刷新的宽度，默认为全屏宽度
            h: 局部刷新的高度，默认为全屏高度
            global_refresh: 是否使用全局刷新模式，默认为False
        """
        print("显示帧缓冲区")
        if self.init_done==False:
            self.init()

        # 如果未指定宽高，则使用全屏
        if w is None:
            w = self.width
        if h is None:
            h = self.height
            
        # 检查是否需要强制全屏刷新
        need_clear_screen = self.force_full_refresh or self.refresh_count >= self.partial_refresh_limit
        
        # 如果使用全局刷新模式，则设置全屏刷新区域
        if global_refresh:
            self.set_partial(0, 0, self.width, self.height)
        elif need_clear_screen:
            self.clear_screen()
            # 设置局部刷新区域
            self.set_partial(x, y, w, h)
        else:
            # 设置局部刷新区域
            self.set_partial(x, y, w, h)
        
        # 写入图像数据
        self.write_image(0x24, frame_buffer, True, True)

        # 播放等待音效 (异步)
        if system_buzzer:
            system_buzzer.play_process_async()

        # 执行刷新
        if global_refresh:
            # 全局刷新模式
            print("执行全局刷新模式")
            self._command(0x21,b'\x40\x00')
            self._command(0x22,b'\xf7')  # 使用完整刷新模式
            self._command(0x20)
            self.wait_until_idle()
            self.refresh_count = 0
            print("全局刷新完成，重置计数器")
        elif need_clear_screen:
            # 已经通过clear_screen()执行了刷新，这里不需要再次刷新
            print("已通过clear_screen完成全屏刷新，跳过重复刷新")
            self.refresh_count = 0
        elif partial and not self.force_full_refresh and self.refresh_count < self.partial_refresh_limit:
            # 局部刷新模式
            print("执行局部刷新模式")
            self._command(0x21,b'\x40\x00')
            self._command(0x1A, b'\x64')  # 快速刷新设置
            self._command(0x22,b'\xd7')  # 局部刷新命令
            self._command(0x20)
            self.wait_until_idle()
            self.refresh_count += 1
            print(f"局部刷新完成，刷新计数: {self.refresh_count}/{self.partial_refresh_limit}")
        else:
            # 全屏刷新模式
            print("执行全屏刷新模式")
            self.update_full()
            self.refresh_count = 0
            print("全屏刷新完成，重置计数器")

    # 添加强制全屏刷新的方法
    def force_refresh(self):
        """强制执行下一次全屏刷新，清除所有残影"""
        self.force_full_refresh = True
        print("已设置强制全屏刷新标志")

    # to wake call reset() or init()
    def sleep(self):
        self.pwr_off()
        self._command(0x10, b'\x01')
        self.init_done = False
        self.hibernate = True