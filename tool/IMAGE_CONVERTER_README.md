# 图片转换工具使用指南

这个工具可以将多种格式的图片转换为适用于ESP32墨水屏显示的二进制点阵数据。

## 功能特点

- 支持多种图片格式：JPG、PNG、BMP、GIF、TIFF等
- 自动调整图片大小并居中显示
- 支持黑色背景白色文本或白色背景黑色文本
- 支持旋转90度显示
- 支持Floyd-Steinberg抖动算法提高图像质量
- 支持创建文本图像
- 支持批量转换

## 安装依赖

```bash
pip install Pillow
```

## 使用方法

### 1. 转换单个图片

```bash
python3 image_converter.py image <输入图片路径> <输出文件路径> [选项]
```

```bash
python image_converter.py image image.png test_image.py --
width 400 --height 300
```
选项参数：
- `--width`: 目标宽度（默认400）
- `--height`: 目标高度（默认300）
- `--invert`: 反转颜色（白色背景黑色文本）
- `--rotate`: 旋转90度
- `--no-dither`: 不使用抖动算法

示例：
```bash
# 转换为黑色背景白色文本（默认）
python3 image_converter.py image photo.jpg photo_dark.py

# 转换为白色背景黑色文本
python3 image_converter.py image photo.jpg photo_light.py --invert

# 转换并旋转90度
python3 image_converter.py image photo.jpg photo_rotated.py --rotate

# 转换为128x296尺寸并旋转
python3 image_converter.py image photo.jpg photo_small.py --width 128 --height 296 --rotate
```

### 2. 创建文本图像

```bash
python3 image_converter.py text "<文本内容>" <输出文件路径> [选项]
```


选项参数：
- `--width`: 目标宽度（默认400）
- `--height`: 目标高度（默认300）
- `--font-size`: 字体大小（默认24）
- `--invert`: 反转颜色（白色背景黑色文本）
- `--rotate`: 旋转90度

示例：
```bash
# 创建文本图像
python3 image_converter.py text "Hello ESP32!" hello.py

# 创建大字体文本图像
python3 image_converter.py text "Hello ESP32!" hello_big.py --font-size 32

# 创建旋转文本图像
python3 image_converter.py text "Rotated Text" rotated.py --rotate
```

### 3. 批量转换

```bash
python3 image_converter.py batch <输入目录> <输出目录> [选项]
```

示例：
```bash
# 批量转换目录中的所有图片
python3 image_converter.py batch images/ converted/

# 批量转换为白色背景黑色文本
python3 image_converter.py batch images/ converted/ --invert
```

## 输出格式

转换后的文件包含一个bytearray变量，变量名与文件名相同：

```python
# Converted from photo.jpg
# Size: 400x300
# Inverted: False, Rotated: False
photo = bytearray(b'\x00\x00\x00\x0...')
```

## 在ESP32项目中使用

1. 将转换后的.py文件复制到ESP32项目目录
2. 在boot.py中设置`RUN_MODE=3`
3. 修改image.py导入转换后的图片数据：

```python
# 在image.py中导入转换后的图片
from photo import photo

def run(img_data=None):
    if img_data is None:
        # 使用默认图片
        img_data = photo
    
    # ... 其余代码保持不变
```

4. 上传代码到ESP32并运行

## 示例

运行示例脚本：

```bash
python3 convert_examples.py
```

这将创建示例图片目录并展示各种转换用法。

## 注意事项

1. 图片会自动调整大小并居中显示，保持原始宽高比
2. 使用抖动算法可以提高图像质量，但会增加文件大小
3. 旋转90度后，宽度和高度会互换
4. 确保输出目录有写入权限
5. 转换大图片可能需要一些时间

## 故障排除

1. **ImportError: No module named 'PIL'**
   - 解决方案：运行 `pip install Pillow`

2. **无法识别的图片格式**
   - 解决方案：确保图片格式受支持（JPG、PNG、BMP、GIF、TIFF）

3. **转换后的图片显示不正确**
   - 解决方案：尝试使用`--invert`参数反转颜色
   - 尝试使用`--rotate`参数旋转图片

4. **内存不足**
   - 解决方案：减小目标尺寸或使用更小的源图片

## 技术细节

- 图片使用Floyd-Steinberg抖动算法转换为1位黑白图像
- 每个字节表示8个像素，最高位在前
- 像素值0表示黑色，1表示白色
- 字节数组按行组织，每行需要的字节数为(宽度+7)//8