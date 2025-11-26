#!/usr/bin/env python3
"""
图片转换工具 - 将多种格式的图片转换为适用于墨水屏显示的二进制点阵数据
支持转换为黑色背景白色文本或白色背景黑色文本的格式
"""

import os
import sys
from PIL import Image, ImageOps, ImageDraw, ImageFont
import argparse
import math

def convert_image_to_epaper(input_path, output_path, width=400, height=300, invert=False, rotate=False, dither=True):
    """
    将图片转换为墨水屏二进制格式
    
    参数:
        input_path: 输入图片路径
        output_path: 输出文件路径
        width: 目标宽度(默认400)
        height: 目标高度(默认300)
        invert: 是否反转颜色(默认False，黑色背景白色文本)
        rotate: 是否旋转90度(默认False)
        dither: 是否使用抖动算法(默认True)
    """
    try:
        # 打开图片
        img = Image.open(input_path)
        
        # 转换为RGB模式
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 调整大小，保持宽高比
        img_ratio = img.width / img.height
        target_ratio = width / height
        
        if img_ratio > target_ratio:
            # 图片较宽，以宽度为准
            new_width = width
            new_height = int(width / img_ratio)
        else:
            # 图片较高，以高度为准
            new_height = height
            new_width = int(height * img_ratio)
        
        img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 创建目标大小的黑色背景
        result = Image.new('RGB', (width, height), (0, 0, 0) if not invert else (255, 255, 255))
        
        # 计算居中位置
        x_offset = (width - new_width) // 2
        y_offset = (height - new_height) // 2
        
        # 将图片粘贴到中心
        result.paste(img, (x_offset, y_offset))
        
        # 转换为灰度
        result = result.convert('L')
        
        # 转换为1位黑白图像
        if dither:
            result = result.convert('1', dither=Image.FLOYDSTEINBERG)
        else:
            # 使用阈值128进行二值化
            result = result.point(lambda x: 0 if x < 128 else 255, '1')
        
        # 如果需要反转颜色
        if invert:
            result = ImageOps.invert(result)
        
        # 如果需要旋转90度
        if rotate:
            result = result.rotate(90, expand=True)
            # 如果旋转后尺寸不匹配，需要重新调整
            if result.size != (width, height):
                result = result.resize((width, height), Image.LANCZOS)
        
        # 转换为字节数组
        width_bytes = (width + 7) // 8  # 每行需要的字节数
        total_bytes = width_bytes * height
        
        # 创建字节数组
        byte_array = bytearray(total_bytes)
        
        # 将像素数据转换为字节数组
        for y in range(height):
            for x in range(width):
                # 获取像素值 (0或255)
                pixel = 0 if result.getpixel((x, y)) == 0 else 1
                
                # 计算字节位置和位位置
                byte_index = y * width_bytes + x // 8
                bit_position = 7 - (x % 8)  # 最高位在前
                
                # 设置位
                if pixel:
                    byte_array[byte_index] |= (1 << bit_position)
        
        # 生成Python代码
        var_name = os.path.splitext(os.path.basename(output_path))[0]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Converted from {input_path}\n")
            f.write(f"# Size: {width}x{height}\n")
            f.write(f"# Inverted: {invert}, Rotated: {rotate}\n")
            f.write(f"{var_name} = bytearray(b'")
            
            # 将字节数组格式化为十六进制字符串
            for i, byte in enumerate(byte_array):
                if i > 0 and i % 16 == 0:
                    f.write("'\n    b'")
                f.write(f"\\x{byte:02X}")
            
            f.write("')\n")
        
        print(f"转换完成: {input_path} -> {output_path}")
        print(f"输出尺寸: {width}x{height}")
        print(f"总字节数: {total_bytes}")
        
        return True
    
    except Exception as e:
        print(f"转换失败: {e}")
        return False

def create_text_image(text, output_path, width=400, height=300, font_size=24, invert=False, rotate=False):
    """
    创建文本图像并转换为墨水屏二进制格式
    
    参数:
        text: 要显示的文本
        output_path: 输出文件路径
        width: 目标宽度(默认400)
        height: 目标高度(默认300)
        font_size: 字体大小(默认24)
        invert: 是否反转颜色(默认False，黑色背景白色文本)
        rotate: 是否旋转90度(默认False)
    """
    try:
        # 创建图像
        result = Image.new('RGB', (width, height), (0, 0, 0) if not invert else (255, 255, 255))
        draw = ImageDraw.Draw(result)
        
        # 尝试加载字体
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                # 尝试使用项目中的字体
                font = ImageFont.truetype("GB2312-12.fon", font_size)
            except:
                # 使用默认字体
                font = ImageFont.load_default()
        
        # 计算文本位置
        text_width, text_height = draw.textsize(text, font=font)
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # 绘制文本
        text_color = (255, 255, 255) if not invert else (0, 0, 0)
        draw.text((x, y), text, font=font, fill=text_color)
        
        # 转换为灰度
        result = result.convert('L')
        
        # 转换为1位黑白图像
        result = result.convert('1')
        
        # 如果需要旋转90度
        if rotate:
            result = result.rotate(90, expand=True)
            # 如果旋转后尺寸不匹配，需要重新调整
            if result.size != (width, height):
                result = result.resize((width, height), Image.LANCZOS)
        
        # 转换为字节数组
        width_bytes = (width + 7) // 8  # 每行需要的字节数
        total_bytes = width_bytes * height
        
        # 创建字节数组
        byte_array = bytearray(total_bytes)
        
        # 将像素数据转换为字节数组
        for y in range(height):
            for x in range(width):
                # 获取像素值 (0或255)
                pixel = 0 if result.getpixel((x, y)) == 0 else 1
                
                # 计算字节位置和位位置
                byte_index = y * width_bytes + x // 8
                bit_position = 7 - (x % 8)  # 最高位在前
                
                # 设置位
                if pixel:
                    byte_array[byte_index] |= (1 << bit_position)
        
        # 生成Python代码
        var_name = os.path.splitext(os.path.basename(output_path))[0]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Text image: {text}\n")
            f.write(f"# Size: {width}x{height}\n")
            f.write(f"# Font size: {font_size}\n")
            f.write(f"# Inverted: {invert}, Rotated: {rotate}\n")
            f.write(f"{var_name} = bytearray(b'")
            
            # 将字节数组格式化为十六进制字符串
            for i, byte in enumerate(byte_array):
                if i > 0 and i % 16 == 0:
                    f.write("'\n    b'")
                f.write(f"\\x{byte:02X}")
            
            f.write("')\n")
        
        print(f"文本图像创建完成: {output_path}")
        print(f"文本: {text}")
        print(f"输出尺寸: {width}x{height}")
        print(f"总字节数: {total_bytes}")
        
        return True
    
    except Exception as e:
        print(f"创建失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='将图片转换为墨水屏二进制格式')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 图片转换命令
    img_parser = subparsers.add_parser('image', help='转换图片文件')
    img_parser.add_argument('input', help='输入图片路径')
    img_parser.add_argument('output', help='输出文件路径')
    img_parser.add_argument('--width', type=int, default=400, help='目标宽度(默认400)')
    img_parser.add_argument('--height', type=int, default=300, help='目标高度(默认300)')
    img_parser.add_argument('--invert', action='store_true', help='反转颜色(白色背景黑色文本)')
    img_parser.add_argument('--rotate', action='store_true', help='旋转90度')
    img_parser.add_argument('--no-dither', action='store_true', help='不使用抖动算法')
    
    # 文本创建命令
    text_parser = subparsers.add_parser('text', help='创建文本图像')
    text_parser.add_argument('text', help='要显示的文本')
    text_parser.add_argument('output', help='输出文件路径')
    text_parser.add_argument('--width', type=int, default=400, help='目标宽度(默认400)')
    text_parser.add_argument('--height', type=int, default=300, help='目标高度(默认300)')
    text_parser.add_argument('--font-size', type=int, default=24, help='字体大小(默认24)')
    text_parser.add_argument('--invert', action='store_true', help='反转颜色(白色背景黑色文本)')
    text_parser.add_argument('--rotate', action='store_true', help='旋转90度')
    
    # 批量转换命令
    batch_parser = subparsers.add_parser('batch', help='批量转换图片')
    batch_parser.add_argument('input_dir', help='输入目录')
    batch_parser.add_argument('output_dir', help='输出目录')
    batch_parser.add_argument('--width', type=int, default=400, help='目标宽度(默认400)')
    batch_parser.add_argument('--height', type=int, default=300, help='目标高度(默认300)')
    batch_parser.add_argument('--invert', action='store_true', help='反转颜色(白色背景黑色文本)')
    batch_parser.add_argument('--rotate', action='store_true', help='旋转90度')
    batch_parser.add_argument('--no-dither', action='store_true', help='不使用抖动算法')
    
    args = parser.parse_args()
    
    if args.command == 'image':
        convert_image_to_epaper(
            args.input, 
            args.output, 
            args.width, 
            args.height, 
            args.invert, 
            args.rotate, 
            not args.no_dither
        )
    elif args.command == 'text':
        create_text_image(
            args.text, 
            args.output, 
            args.width, 
            args.height, 
            args.font_size, 
            args.invert, 
            args.rotate
        )
    elif args.command == 'batch':
        # 确保输出目录存在
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 支持的图片格式
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
        
        # 遍历输入目录
        for filename in os.listdir(args.input_dir):
            if filename.lower().endswith(supported_formats):
                input_path = os.path.join(args.input_dir, filename)
                output_filename = os.path.splitext(filename)[0] + '.py'
                output_path = os.path.join(args.output_dir, output_filename)
                
                convert_image_to_epaper(
                    input_path, 
                    output_path, 
                    args.width, 
                    args.height, 
                    args.invert, 
                    args.rotate, 
                    not args.no_dither
                )
    else:
        parser.print_help()

if __name__ == '__main__':
    main()