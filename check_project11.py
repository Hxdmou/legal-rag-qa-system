import re

# 读取文件
with open('f:\\个人作品\\legal-rag-qa-system\\generate_pptx.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到项目11的数据部分
start = content.find('{"title": "项目11：总结与未来规划')
end = content.find(']\n        }\n    ]\n', start)
if start == -1 or end == -1:
    print("未找到项目11")
    exit()

project11_data = content[start:end]

# 检查数据结构
print('=== 项目11数据检查 ===')
print()

# 统计行数和列数
rows = re.findall(r'\[.*?\]', project11_data)
print(f'总行数: {len(rows)}')
print()

# 检查每一行的列数
for i, row in enumerate(rows):
    cols = row.split(',')
    print(f'第{i+1}行: {len(cols)}列')
    if i == 0:
        print(f'  表头: {[c.strip().strip("\'\"") for c in cols[:5]]}...')
    else:
        print(f'  第一个单元格: {cols[0].strip().strip("\'\"")}')
        # 检查最后一列（关键技术指标）是否有内容
        last_col = cols[-1].strip().strip('"\']') if cols else ''
        if not last_col or last_col == '-':
            print(f'  ⚠️ 关键技术指标为空！')
        else:
            print(f'  关键技术指标: {last_col[:50]}...')
    print()
