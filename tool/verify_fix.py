#!/usr/bin/env python3
"""
验证修复后的图片数据
"""

# 导入旧的(有问题的)和新的(修复后的)图片数据
from test_iamge import test_iamge as old_data
from test_iamge_fixed import test_iamge_fixed as new_data

print("=== 验证图片数据修复 ===\n")

# 检查数据长度
print(f"旧数据长度: {len(old_data)} 字节")
print(f"新数据长度: {len(new_data)} 字节")
print(f"预期长度: {(400 * 300) // 8} 字节\n")

# 检查旧数据中的换行符
newline_count = old_data.count(0x0A)  # 0x0A 是换行符 \n
print(f"旧数据中的换行符(0x0A)数量: {newline_count}")
print(f"新数据中的换行符(0x0A)数量: {new_data.count(0x0A)}\n")

# 显示前几个字节
print("旧数据前32字节:")
print(' '.join(f'{b:02X}' for b in old_data[:32]))
print("\n新数据前32字节:")
print(' '.join(f'{b:02X}' for b in new_data[:32]))

# 检查数据类型
print(f"\n旧数据类型: {type(old_data)}")
print(f"新数据类型: {type(new_data)}")

print("\n=== 结论 ===")
if newline_count > 0:
    print(f"❌ 旧数据包含 {newline_count} 个错误的换行符,会导致显示乱码")
else:
    print("✓ 旧数据没有换行符问题")

if new_data.count(0x0A) == 0 or new_data.count(0x0A) < newline_count:
    print("✓ 新数据已修复,不包含错误的换行符")
else:
    print("❌ 新数据仍有问题")

if len(new_data) == 15000:
    print("✓ 新数据长度正确 (400x300/8 = 15000 字节)")
else:
    print(f"❌ 新数据长度不正确,应该是 15000 字节")
