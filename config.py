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

# 屏幕尺寸
WIDTH = 400
HEIGHT = 300

# 初始化SPI
spi = SPI(2, baudrate=2000000, polarity=0, phase=0, sck=sck, miso=miso, mosi=mosi)

# ESPink电源控制
epd_power = Pin(2, Pin.OUT)
epd_power.on()
sleep_ms(10)

# WiFi配置
# WIFI_SSID = "your_wifi_ssid"  # 替换为你的WiFi名称
# WIFI_PASSWORD = "your_wifi_password"  # 替换为你的WiFi密码
# WIFI_TIMEOUT = 10000  # WiFi连接超时时间(毫秒)

# WIFI_SSID = "Tangleup-AI"  # 替换为你的WiFi名称
# WIFI_PASSWORD = "djt12345678"  # 替换为你的WiFi密码
# WIFI_TIMEOUT = 10000  # WiFi连接超时时间(毫秒)

WIFI_SSID = "Atable1"  # 替换为你的WiFi名称
WIFI_PASSWORD = "atable666"  # 替换为你的WiFi密码
WIFI_TIMEOUT = 10000  # WiFi连接超时时间(毫秒)



SERVER_IP = "192.168.0.216"
SERVER_PORT = "8888"
DEVICE_ID = "1"
CONTENT_ID = "latest"
SERVER_END_POINT = "http://" + SERVER_IP + ":" + SERVER_PORT + "/api/contents/devices/" + DEVICE_ID + "/content" + CONTENT_ID + "binary?invert=false&rotate=false&dither=true"
API_KEY = "123tangledup-ai"