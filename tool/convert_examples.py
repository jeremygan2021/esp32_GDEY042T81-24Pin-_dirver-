#!/usr/bin/env python3
"""
图片转换工具使用示例
"""

import os
import subprocess
import sys

def run_command(cmd):
    """运行命令并打印输出"""
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"错误: {result.stderr}")
    return result.returncode == 0

def main():
    print("=== 图片转换工具使用示例 ===\n")
    
    # 检查是否存在示例图片目录
    example_dir = "example_images"
    output_dir = "converted_images"
    
    if not os.path.exists(example_dir):
        print(f"创建示例图片目录: {example_dir}")
        os.makedirs(example_dir, exist_ok=True)
        print("请将图片文件放入此目录后再次运行此脚本")
        return
    
    if not os.path.exists(output_dir):
        print(f"创建输出目录: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
    
    # 示例1: 转换单个图片为黑色背景白色文本
    print("\n示例1: 转换单个图片为黑色背景白色文本")
    print("=" * 50)
    cmd = [
        "python3", "image_converter.py", "image",
        os.path.join(example_dir, "example.jpg"),
        os.path.join(output_dir, "example_dark.py"),
        "--width", "400",
        "--height", "300"
    ]
    run_command(cmd)
    
    # 示例2: 转换单个图片为白色背景黑色文本
    print("\n示例2: 转换单个图片为白色背景黑色文本")
    print("=" * 50)
    cmd = [
        "python3", "image_converter.py", "image",
        os.path.join(example_dir, "example.jpg"),
        os.path.join(output_dir, "example_light.py"),
        "--width", "400",
        "--height", "300",
        "--invert"
    ]
    run_command(cmd)
    
    # 示例3: 创建文本图像
    print("\n示例3: 创建文本图像")
    print("=" * 50)
    cmd = [
        "python3", "image_converter.py", "text",
        "Hello ESP32!",
        os.path.join(output_dir, "hello_text.py"),
        "--width", "400",
        "--height", "300",
        "--font-size", "32"
    ]
    run_command(cmd)
    
    # 示例4: 创建旋转90度的文本图像
    print("\n示例4: 创建旋转90度的文本图像")
    print("=" * 50)
    cmd = [
        "python3", "image_converter.py", "text",
        "Rotated Text",
        os.path.join(output_dir, "rotated_text.py"),
        "--width", "400",
        "--height", "300",
        "--font-size", "32",
        "--rotate"
    ]
    run_command(cmd)
    
    # 示例5: 批量转换图片
    print("\n示例5: 批量转换图片")
    print("=" * 50)
    cmd = [
        "python3", "image_converter.py", "batch",
        example_dir,
        output_dir,
        "--width", "400",
        "--height", "300"
    ]
    run_command(cmd)
    
    # 示例6: 转换为128x296尺寸（与现有示例相同）
    print("\n示例6: 转换为128x296尺寸")
    print("=" * 50)
    cmd = [
        "python3", "image_converter.py", "image",
        os.path.join(example_dir, "example.jpg"),
        os.path.join(output_dir, "example_128x296.py"),
        "--width", "128",
        "--height", "296",
        "--rotate"
    ]
    run_command(cmd)
    
    print("\n=== 转换完成 ===")
    print(f"输出文件位于: {output_dir}")
    print("\n使用方法:")
    print("1. 将转换后的.py文件复制到ESP32项目目录")
    print("2. 在boot.py中设置RUN_MODE=3")
    print("3. 修改image.py导入转换后的图片数据")
    print("4. 上传代码到ESP32并运行")

if __name__ == '__main__':
    main()