import markdown
from xhtml2pdf import pisa

def md_to_pdf(md_file, pdf_file):
    """将Markdown文件转换为PDF"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 转换为HTML
    html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
    
    # 添加样式
    html_with_style = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'SimSun', 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; font-size: 12px; }}
            h1 {{ color: #1a1a2e; border-bottom: 2px solid #4a69bd; padding-bottom: 10px; font-size: 20px; }}
            h2 {{ color: #1a1a2e; margin-top: 30px; font-size: 16px; }}
            h3 {{ color: #1a1a2e; font-size: 14px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 6px; text-align: left; font-size: 11px; }}
            th {{ background-color: #f2f2f2; }}
            code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-size: 11px; }}
            pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 11px; }}
            ul, ol {{ margin-left: 20px; }}
            li {{ margin: 4px 0; }}
        </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """
    
    # 生成PDF
    with open(pdf_file, 'wb') as f:
        pisa.CreatePDF(html_with_style, dest=f)
    print(f"✅ PDF已生成: {pdf_file}")

# 转换两个文档
md_to_pdf("法律知识问答系统完整作品集.md", "法律知识问答系统.pdf")
md_to_pdf("文档测试结果.md", "文档测试结果.pdf")

print("\n🎉 所有PDF已生成完成！")
