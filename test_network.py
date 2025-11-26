"""网络连接测试程序
用于诊断ESP32的网络连接问题
"""
import socket
import config
from time import sleep_ms
import wifi

def test_dns():
    """测试DNS解析"""
    print("\n=== 测试DNS解析 ===")
    test_hosts = [
        ("www.baidu.com", 80),
        (config.SERVER_IP, int(config.SERVER_PORT))
    ]
    
    for host, port in test_hosts:
        try:
            print(f"解析 {host}...")
            addr_info = socket.getaddrinfo(host, port)
            print(f"  成功: {addr_info[0][-1]}")
        except Exception as e:
            print(f"  失败: {e}")

def test_ping():
    """测试网络连通性"""
    print("\n=== 测试网络连通性 ===")
    
    # 测试网关
    gateway = wifi.wifi_manager.get_network_info()[2]
    print(f"网关地址: {gateway}")
    
    # 测试服务器连接
    test_hosts = [
        ("www.baidu.com", 80, 5),
        (config.SERVER_IP, int(config.SERVER_PORT), 10)
    ]
    
    for host, port, timeout in test_hosts:
        print(f"\n测试连接到 {host}:{port} (超时: {timeout}秒)")
        try:
            addr = socket.getaddrinfo(host, port)[0][-1]
            s = socket.socket()
            s.settimeout(timeout)
            print(f"  尝试连接到 {addr}...")
            s.connect(addr)
            print(f"  ✓ 连接成功！")
            s.close()
        except Exception as e:
            print(f"  ✗ 连接失败: {e}")
            import sys
            sys.print_exception(e)

def test_http_simple():
    """测试简单的HTTP请求"""
    print("\n=== 测试HTTP请求 ===")
    
    # 先测试一个已知可用的服务
    print("测试 http://www.baidu.com")
    try:
        addr = socket.getaddrinfo("www.baidu.com", 80)[0][-1]
        s = socket.socket()
        s.settimeout(5)
        s.connect(addr)
        s.send(b"GET / HTTP/1.0\r\nHost: www.baidu.com\r\n\r\n")
        data = s.recv(100)
        s.close()
        print(f"  ✓ 成功接收数据: {len(data)} 字节")
        print(f"  响应开头: {data[:50]}")
    except Exception as e:
        print(f"  ✗ 失败: {e}")

def run():
    """运行所有测试"""
    print("=== ESP32 网络诊断工具 ===\n")
    
    if not wifi.wifi_manager.connect():
        print("WiFi连接失败，无法继续测试")
        return
    
    test_dns()
    test_ping()
    test_http_simple()
    
    print("\n=== 测试完成 ===")
    print("\n如果能连接到百度但无法连接到服务器，请检查：")
    print("1. 服务器防火墙设置")
    print("2. 服务器是否监听 0.0.0.0 而不是 127.0.0.1")
    print("3. 路由器是否有AP隔离功能（阻止设备间通信）")

if __name__ == "__main__":
    run()
