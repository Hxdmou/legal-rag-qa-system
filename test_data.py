# 测试项目11的数据结构
import re

with open('f:\\个人作品\\legal-rag-qa-system\\generate_pptx.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到项目11的数据部分
start_line = None
end_line = None

for i, line in enumerate(lines):
    if '项目11：总结与未来规划' in line:
        # 找到项目11开始
        for j in range(i, min(i+10, len(lines))):
            if '"data": [' in lines[j]:
                start_line = j + 1  # 数据开始的下一行
                break
    
    if start_line and line.strip() == ']' and end_line is None:
        # 找到数据结束
        end_line = i
        break

print(f"项目11数据范围: 第{start_line+1}行到第{end_line+1}行")
print()

errors = []

for i in range(start_line, end_line):
    line = lines[i]
    # 使用正则提取行内的数据
    match = re.search(r'\[([^\]]+)\]', line)
    if match:
        row_str = match.group(1)
        # 分割列（处理引号内的逗号）
        cols = []
        current_col = ''
        in_quotes = False
        
        for char in row_str:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                cols.append(current_col.strip().strip('"'))
                current_col = ''
            else:
                current_col += char
        cols.append(current_col.strip().strip('"'))
        
        print(f"第{i+1}行: {len(cols)}列")
        if len(cols) != 15:
            print(f"  ⚠️ 列数不匹配！期望15列，实际{len(cols)}列")
            errors.append((i+1, len(cols)))
        else:
            print(f"  项目: {cols[0]}")
            print(f"  关键技术指标: '{cols[-1]}'")
    print()

if errors:
    print("=== 发现错误 ===")
    for row_num, actual_cols in errors:
        print(f"第{row_num}行: 列数不足，期望15列，实际{actual_cols}列")
else:
    print("=== 所有行都有15列，数据结构完整 ===")
