# 图片转换工具使用说明

## 问题修复说明

### 之前的问题
转换器在生成的图片数据中错误地插入了换行符 (`\n`, 0x0A),导致墨水屏显示乱码。

### 修复内容
修改了 `image_converter.py` 中的字节数组格式化逻辑:
- **之前**: 每16个字节后直接写入 `\n`,导致换行符成为数据的一部分
- **现在**: 每16个字节后正确地分割字符串为多个 `b'...'` 部分

## 使用方法

### 1. 转换单个图片

```bash
python image_converter.py image <输入图片路径> <输出文件路径> [选项]
```

**示例:**
```bash
# 基本用法
python image_converter.py image test_image.png output.py

# 指定尺寸
python image_converter.py image test_image.png output.py --width 400 --height 300

# 反转颜色(白底黑字)
python image_converter.py image test_image.png output.py --invert

# 旋转90度
python image_converter.py image test_image.png output.py --rotate

# 不使用抖动算法
python image_converter.py image test_image.png output.py --no-dither
```

**重要提示:**
- 输出路径必须包含文件名,不能只是目录
- ❌ 错误: `python image_converter.py image input.png /path/to/directory`
- ✅ 正确: `python image_converter.py image input.png /path/to/directory/output.py`

### 2. 创建文本图片

```bash
python image_converter.py text <文本内容> <输出文件路径> [选项]
```

**示例:**
```bash
# 基本用法
python image_converter.py text "Hello World" output.py

# 指定字体大小
python image_converter.py text "Hello" output.py --font-size 32

# 白底黑字
python image_converter.py text "Hello" output.py --invert
```

### 3. 批量转换

```bash
python image_converter.py batch <输入目录> <输出目录> [选项]
```

**示例:**
```bash
python image_converter.py batch ./input_images ./output_files --width 400 --height 300
```

## 参数说明

### 通用参数
- `--width`: 目标宽度(默认400像素)
- `--height`: 目标高度(默认300像素)
- `--invert`: 反转颜色(黑底白字 → 白底黑字)
- `--rotate`: 旋转90度

### 图片转换专用
- `--no-dither`: 不使用抖动算法(使用简单阈值二值化)

### 文本创建专用
- `--font-size`: 字体大小(默认24)

## 在MicroPython中使用生成的文件

```python
# 导入生成的图片数据
from output import image_data

# 在image.py中使用
import image
image.run(image_data, width=400, height=300)
```

## 验证修复

运行验证脚本检查生成的文件是否正确:

```bash
python verify_fix.py
```

这会比较修复前后的数据,确认没有错误的换行符。

## 常见问题

### Q: 为什么显示乱码?
A: 如果使用旧版本转换器生成的文件,数据中包含错误的换行符。请使用修复后的转换器重新生成。

### Q: 如何重新生成所有图片?
A: 使用批量转换功能:
```bash
python image_converter.py batch ./old_images ./new_images --width 400 --height 300
```

### Q: 支持哪些图片格式?
A: 支持 JPG, PNG, BMP, GIF, TIFF 等常见格式。

### Q: 生成的文件大小是多少?
A: 对于400x300的图片,二进制数据大小为 15000 字节 (400 * 300 / 8)。

## 技术细节

### 数据格式
- 每个像素用1位表示(黑或白)
- 每行需要 `(width + 7) // 8` 个字节
- 总字节数: `width_bytes * height`
- 位顺序: MSB first (最高位在前)

### 正确的输出格式
```python
image_data = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
    b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
    b'...')
```

### 错误的输出格式(已修复)
```python
# 不要使用这种格式!
image_data = bytearray(b'\n\xFF\xFF\xFF\xFF...\n\xFF\xFF...')
```
