"""
HTTP图像显示程序
从后端服务器获取二进制图像数据并显示在墨水屏上
"""
import socket
import config
from time import sleep_ms
import network
import image

def connect_wifi():
    """连接WiFi"""
    print("正在连接WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print("连接到 " + config.WIFI_SSID)
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        
        # 等待连接
        timeout = config.WIFI_TIMEOUT // 100
        while not wlan.isconnected() and timeout > 0:
            sleep_ms(100)
            timeout -= 1
            
        if not wlan.isconnected():
            print("WiFi连接失败")
            return False
    
    print("WiFi已连接")
    print("IP地址: " + wlan.ifconfig()[0])
    return True

def http_get(host, port, path, headers=None):
    """使用socket实现HTTP GET请求"""
    try:
        # 创建socket连接
        print("连接到 " + host + ":" + str(port))
        addr = socket.getaddrinfo(host, port)[0][-1]
        s = socket.socket()
        s.settimeout(10)
        s.connect(addr)
        
        # 构建HTTP请求
        request = "GET " + path + " HTTP/1.1\r\n"
        request += "Host: " + host + "\r\n"
        request += "Connection: close\r\n"
        
        # 添加自定义头
        if headers:
            for key, value in headers.items():
                request += key + ": " + value + "\r\n"
        
        request += "\r\n"
        
        # 发送请求
        print("发送HTTP请求")
        s.send(request.encode())
        
        # 接收响应
        print("接收响应...")
        response = b""
        while True:
            chunk = s.recv(1024)
            if not chunk:
                break
            response += chunk
        
        s.close()
        print("接收完成，总大小: " + str(len(response)) + " 字节")
        
        # 解析HTTP响应
        header_end = response.find(b"\r\n\r\n")
        if header_end == -1:
            return None, None
        
        body = response[header_end + 4:]
        
        # 提取状态码
        headers_part = response[:header_end].decode('utf-8', 'ignore')
        status_line = headers_part.split('\r\n')[0]
        status_code = int(status_line.split()[1])
        
        print("HTTP状态码: " + str(status_code))
        return status_code, body
        
    except Exception as e:
        print("HTTP请求失败: " + str(e))
        import sys
        sys.print_exception(e)
        return None, None

def fetch_image_from_server():
    """从服务器获取图像二进制数据"""
    # API路径
    path = "/api/contents/devices/1/content/latest/binary?invert=false&rotate=false&dither=true"
    
    print("正在从服务器获取图像")
    print("路径: " + path)
    
    # 设置请求头
    headers = {
        'accept': 'application/json',
        'X-API-Key': config.API_KEY
    }
    
    status_code, body = http_get(
        config.SERVER_IP,
        int(config.SERVER_PORT),
        path,
        headers
    )
    
    if status_code == 200:
        print("成功获取图像数据，大小: " + str(len(body)) + " 字节")
        return body
    else:
        print("获取图像失败，状态码: " + str(status_code))
        return None

def run():
    """主运行函数"""
    print("启动HTTP图像显示程序")
    
    # 连接WiFi
    if not connect_wifi():
        print("无法连接WiFi，程序退出")
        return
    
    # 从服务器获取图像
    print("\n=== 获取图像数据 ===")
    bin_data = fetch_image_from_server()
    
    if bin_data is None:
        print("无法获取图像数据，程序退出")
        return
    
    # 使用image模块显示
    print("\n=== 显示图像 ===")
    image.run(bin_data, width=400, height=300)
    
    print("\n程序完成")

if __name__ == "__main__":
    run()
