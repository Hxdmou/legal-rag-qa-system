from md_to_pptx_v14 import read_markdown, parse_markdown

content = read_markdown(r'f:\个人作品\legal-rag-qa-system\A2A_PPT完整升级内容.md')
chapters = parse_markdown(content)

print(f'找到 {len(chapters)} 个章节')
for c in chapters:
    print(f'章节 {c["num"]}: {c["title"]}')
    print(f'  段落数: {len(c["sections"])}')