from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import re

CHAPTER_COLORS = {
    1: {'bg': RGBColor(15, 20, 35), 'accent': RGBColor(0, 150, 255), 'text': RGBColor(230, 235, 240), 'highlight': RGBColor(255, 80, 80)},
    2: {'bg': RGBColor(20, 30, 25), 'accent': RGBColor(0, 200, 150), 'text': RGBColor(220, 230, 220), 'highlight': RGBColor(255, 100, 100)},
    3: {'bg': RGBColor(35, 20, 30), 'accent': RGBColor(200, 100, 200), 'text': RGBColor(230, 220, 235), 'highlight': RGBColor(255, 100, 100)},
    4: {'bg': RGBColor(25, 25, 15), 'accent': RGBColor(255, 200, 50), 'text': RGBColor(235, 235, 220), 'highlight': RGBColor(255, 100, 100)},
    5: {'bg': RGBColor(15, 30, 35), 'accent': RGBColor(150, 100, 255), 'text': RGBColor(220, 235, 240), 'highlight': RGBColor(255, 100, 100)},
    6: {'bg': RGBColor(30, 25, 20), 'accent': RGBColor(255, 100, 150), 'text': RGBColor(240, 230, 225), 'highlight': RGBColor(255, 100, 100)}
}

CHAPTER_TITLES = [
    "第一章：A2A协议架构与核心价值",
    "第二章：协议规范与技术细节",
    "第三章：安全与合规体系",
    "第四章：部署与运维实践",
    "第五章：性能优化策略",
    "第六章：实战案例与最佳实践"
]

DEFAULT_TABLES = {
    1: [
        ['价值维度', '业务收益', '技术实现'],
        ['互操作性', '降低集成成本60%+', '标准化消息格式'],
        ['弹性扩展', '支持百万级并发', '去中心化架构'],
        ['安全合规', '通过SOC2认证', '端到端加密'],
        ['可观测性', '全链路追踪', '标准化日志']
    ],
    2: [
        ['协议层级', '主要技术', '核心功能'],
        ['应用层', 'Agent Cards', '技能注册与发现'],
        ['消息层', 'JSON-RPC 2.0', '异步消息传递'],
        ['传输层', 'HTTP/2、gRPC', '高效数据传输'],
        ['安全层', 'OAuth2、mTLS', '身份认证与加密']
    ],
    3: [
        ['安全组件', '实现方式', '防护级别'],
        ['API网关', 'Kong/APISIX', '流量控制'],
        ['WAF防火墙', 'ModSecurity', '攻击防护'],
        ['OAuth 2.0', '授权码模式', '身份认证'],
        ['mTLS', '双向证书', '通道加密']
    ],
    4: [
        ['部署策略', '实现方式', '可用性'],
        ['多活部署', 'K8s StatefulSet', '99.99%'],
        ['自动扩缩容', 'HPA/VPA', '弹性应对'],
        ['健康检查', 'Liveness/Readiness', '故障自愈'],
        ['蓝绿发布', 'Istio', '零停机升级']
    ],
    5: [
        ['优化维度', '策略', '预期收益'],
        ['网络优化', 'HTTP/2、gRPC', '延迟降低40%'],
        ['消息批量', '批量聚合', '吞吐量提升2x'],
        ['缓存策略', 'Redis集群', '响应快3x'],
        ['并发处理', '异步队列', '容量提升5x']
    ],
    6: [
        ['案例场景', '业务价值', '技术亮点'],
        ['供应链管理', '效率提升40%', '多Agent协作'],
        ['金融风控', '风险降低35%', '实时决策'],
        ['智能办公', '生产力提升50%', '自动化流程'],
        ['医疗诊断', '准确率提升25%', '专业知识整合']
    ]
}

CHAPTER_RESOURCES = {
    1: [
        '官方文档: https://a2a-protocol.org',
        'Linux Foundation: https://linuxfoundation.org/press-release/a2a-protocol/',
        'DeepLearning.AI课程: https://www.deeplearning.ai/courses/intro-to-a2a-protocol/',
        'GitHub仓库: https://github.com/a2aproject'
    ],
    2: [
        'JSON-RPC 2.0规范: https://www.jsonrpc.org/specification',
        'HTTP/2协议: https://http2.github.io/',
        'gRPC官方文档: https://grpc.io/docs/',
        'QUIC协议: https://datatracker.ietf.org/wg/quic/about/'
    ],
    3: [
        'OAuth 2.0规范: https://oauth.net/2/',
        'mTLS指南: https://www.envoyproxy.io/docs/envoy/latest/security/mozilla',
        'WAF配置: https://www.modsecurity.org/CRS/Documentation/',
        'Kong网关: https://docs.konghq.com/'
    ],
    4: [
        'Kubernetes文档: https://kubernetes.io/zh-cn/docs/',
        'Prometheus监控: https://prometheus.io/docs/introduction/overview/',
        'Grafana可视化: https://grafana.com/docs/grafana/latest/',
        'Istio服务网格: https://istio.io/latest/zh/docs/'
    ],
    5: [
        'Redis缓存: https://redis.io/docs/',
        'gRPC性能优化: https://grpc.io/docs/guides/performance/',
        '批量处理: https://docs.python.org/3/library/concurrent.futures.html',
        'CDN加速: https://www.cloudflare.com/learning/cdn/what-is-a-cdn/'
    ],
    6: [
        '供应链案例: https://www.supplychaindive.com/',
        '金融风控案例: https://www.fintechnexus.com/',
        '多Agent系统: https://arxiv.org/abs/2401.07580',
        '最佳实践: https://www.agentprotocol.io/'
    ]
}

def add_ai_element(slide, chapter_num, colors):
    """在幻灯片右侧添加AI元素装饰"""
    shapes = slide.shapes

    if chapter_num == 1:
        left = Inches(14)
        top = Inches(1)
        width = Inches(1.5)
        height = Inches(1.5)
        hexagon = shapes.add_shape(MSO_SHAPE.HEXAGON, left, top, width, height)
        hexagon.fill.solid()
        hexagon.fill.fore_color.rgb = colors['accent']
        hexagon.fill.transparency = 0.4
        hexagon.line.fill.background()

        left = Inches(14.5)
        top = Inches(2.5)
        width = Inches(0.8)
        height = Inches(0.8)
        oval = shapes.add_shape(MSO_SHAPE.OVAL, left, top, width, height)
        oval.fill.solid()
        oval.fill.fore_color.rgb = colors['accent']
        oval.fill.transparency = 0.5
        oval.line.fill.background()

    elif chapter_num == 2:
        left = Inches(14.2)
        top = Inches(1.5)
        width = Inches(0.6)
        height = Inches(2)
        rect = shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        rect.fill.solid()
        rect.fill.fore_color.rgb = colors['accent']
        rect.fill.transparency = 0.5
        rect.line.fill.background()

        left = Inches(14.8)
        top = Inches(1.8)
        width = Inches(0.5)
        height = Inches(1.5)
        rect2 = shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        rect2.fill.solid()
        rect2.fill.fore_color.rgb = colors['accent']
        rect2.fill.transparency = 0.3
        rect2.line.fill.background()

    elif chapter_num == 3:
        left = Inches(14)
        top = Inches(1.5)
        width = Inches(1.2)
        height = Inches(1.2)
        oval = shapes.add_shape(MSO_SHAPE.OVAL, left, top, width, height)
        oval.fill.solid()
        oval.fill.fore_color.rgb = colors['accent']
        oval.fill.transparency = 0.4
        oval.line.fill.background()

        left = Inches(14.3)
        top = Inches(2.8)
        width = Inches(0.6)
        height = Inches(0.6)
        oval2 = shapes.add_shape(MSO_SHAPE.OVAL, left, top, width, height)
        oval2.fill.solid()
        oval2.fill.fore_color.rgb = colors['highlight']
        oval2.fill.transparency = 0.3
        oval2.line.fill.background()

    elif chapter_num == 4:
        left = Inches(14)
        top = Inches(1.2)
        width = Inches(1.5)
        height = Inches(0.4)
        rect = shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        rect.fill.solid()
        rect.fill.fore_color.rgb = colors['accent']
        rect.fill.transparency = 0.4
        rect.line.fill.background()

        left = Inches(14)
        top = Inches(1.8)
        width = Inches(1.5)
        height = Inches(0.4)
        rect2 = shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        rect2.fill.solid()
        rect2.fill.fore_color.rgb = colors['accent']
        rect2.fill.transparency = 0.3
        rect2.line.fill.background()

        left = Inches(14)
        top = Inches(2.4)
        width = Inches(1.5)
        height = Inches(0.4)
        rect3 = shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        rect3.fill.solid()
        rect3.fill.fore_color.rgb = colors['accent']
        rect3.fill.transparency = 0.2
        rect3.line.fill.background()

    elif chapter_num == 5:
        left = Inches(14.3)
        top = Inches(1.5)
        width = Inches(0.8)
        height = Inches(1.5)
        rect = shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        rect.fill.solid()
        rect.fill.fore_color.rgb = colors['accent']
        rect.fill.transparency = 0.4
        rect.line.fill.background()

        left = Inches(14.6)
        top = Inches(2)
        width = Inches(0.5)
        height = Inches(1)
        rect2 = shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        rect2.fill.solid()
        rect2.fill.fore_color.rgb = colors['accent']
        rect2.fill.transparency = 0.2
        rect2.line.fill.background()

    elif chapter_num == 6:
        left = Inches(14)
        top = Inches(1.3)
        width = Inches(1.3)
        height = Inches(1.3)
        hexagon = shapes.add_shape(MSO_SHAPE.HEXAGON, left, top, width, height)
        hexagon.fill.solid()
        hexagon.fill.fore_color.rgb = colors['accent']
        hexagon.fill.transparency = 0.4
        hexagon.line.fill.background()

        left = Inches(14.3)
        top = Inches(2.8)
        width = Inches(0.7)
        height = Inches(0.7)
        oval = shapes.add_shape(MSO_SHAPE.OVAL, left, top, width, height)
        oval.fill.solid()
        oval.fill.fore_color.rgb = colors['accent']
        oval.fill.transparency = 0.3
        oval.line.fill.background()

def add_chapter_background(slide, chapter_num):
    """添加章节特定风格背景"""
    colors = CHAPTER_COLORS.get(chapter_num, CHAPTER_COLORS[1])

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = colors['bg']

    shapes = slide.shapes

    left = Inches(10) if chapter_num % 2 == 0 else Inches(0)
    top = Inches(0) if chapter_num % 2 == 0 else Inches(4)
    width = Inches(8)
    height = Inches(6)

    oval = shapes.add_shape(MSO_SHAPE.OVAL, left, top, width, height)
    oval.fill.solid()
    oval.fill.fore_color.rgb = colors['accent']
    oval.fill.transparency = 0.15
    oval.line.fill.background()

    bar = shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(8.6), Inches(16), Inches(0.15))
    bar.fill.solid()
    bar.fill.fore_color.rgb = colors['accent']
    bar.line.fill.background()

    return colors

def create_title_slide(prs):
    """创建封面页"""
    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(10, 15, 25)

    shapes = slide.shapes
    oval = shapes.add_shape(MSO_SHAPE.OVAL, Inches(8), Inches(0), Inches(10), Inches(8))
    oval.fill.solid()
    oval.fill.fore_color.rgb = RGBColor(0, 100, 200)
    oval.fill.transparency = 0.2

    hexagon = shapes.add_shape(MSO_SHAPE.HEXAGON, Inches(13), Inches(1), Inches(2), Inches(2))
    hexagon.fill.solid()
    hexagon.fill.fore_color.rgb = RGBColor(0, 150, 255)
    hexagon.fill.transparency = 0.5
    hexagon.line.fill.background()

    title_box = slide.shapes.add_textbox(Inches(2), Inches(2.5), Inches(12), Inches(2))
    title_frame = title_box.text_frame
    p = title_frame.add_paragraph()
    p.text = "🤖 A2A协议企业级深度解析"
    p.font.size = Pt(36)
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

    subtitle_box = slide.shapes.add_textbox(Inches(3), Inches(4.5), Inches(10), Inches(1))
    subtitle_frame = subtitle_box.text_frame
    p = subtitle_frame.add_paragraph()
    p.text = "Agent-to-Agent通信标准与实战指南"
    p.font.size = Pt(20)
    p.font.color.rgb = RGBColor(0, 180, 255)
    p.alignment = PP_ALIGN.CENTER

    presenter_box = slide.shapes.add_textbox(Inches(3), Inches(5.5), Inches(10), Inches(1))
    presenter_frame = presenter_box.text_frame
    p = presenter_frame.add_paragraph()
    p.text = "【主讲人：何晓冬】"
    p.font.size = Pt(18)
    p.font.color.rgb = RGBColor(255, 200, 100)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

    info_box = slide.shapes.add_textbox(Inches(3), Inches(7), Inches(10), Inches(1))
    info_frame = info_box.text_frame
    p = info_frame.add_paragraph()
    p.text = "版本: v2.0 | 日期: 2026年5月"
    p.font.size = Pt(14)
    p.font.color.rgb = RGBColor(150, 160, 180)
    p.alignment = PP_ALIGN.CENTER

    return slide

def create_chapter_slide(prs, chapter):
    """创建章节幻灯片（含表格、AI元素、红色重点和拓展资源）"""
    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)

    colors = add_chapter_background(slide, chapter['num'])

    add_ai_element(slide, chapter['num'], colors)

    title_box = slide.shapes.add_textbox(Inches(1), Inches(0.4), Inches(12), Inches(0.8))
    title_frame = title_box.text_frame
    p = title_frame.add_paragraph()
    p.text = chapter['title']
    p.font.size = Pt(20)
    p.font.color.rgb = colors['accent']
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

    if chapter['tables']:
        table_data = chapter['tables'][0]
        create_table(slide, table_data, colors)

    resources = CHAPTER_RESOURCES.get(chapter['num'], [])
    if resources:
        create_resources_box(slide, resources, colors)

    return slide

def create_table(slide, table_data, colors):
    """在幻灯片中创建表格，红色标记重点内容"""
    num_rows = len(table_data)
    num_cols = len(table_data[0]) if num_rows > 0 else 3

    left = Inches(1)
    top = Inches(1.3)
    width = Inches(13)
    height = Inches(5)

    table = slide.shapes.add_table(num_rows, num_cols, left, top, width, height).table

    highlight_keywords = ['核心', '关键', '重要', '必须', '最佳', '提升', '降低', '99', 'SOC2', '百万']

    for i, row in enumerate(table_data):
        for j, cell in enumerate(row):
            cell_text = cell[:22] + '..' if len(cell) > 22 else cell

            table.cell(i, j).text = cell_text

            paragraph = table.cell(i, j).text_frame.paragraphs[0]
            paragraph.font.size = Pt(11)
            paragraph.alignment = PP_ALIGN.CENTER

            if i == 0:
                paragraph.font.color.rgb = RGBColor(255, 255, 255)
                paragraph.font.bold = True
                table.cell(i, j).fill.solid()
                table.cell(i, j).fill.fore_color.rgb = colors['accent']
            else:
                is_highlight = any(keyword in cell for keyword in highlight_keywords)
                if is_highlight:
                    paragraph.font.color.rgb = colors['highlight']
                    paragraph.font.bold = True
                else:
                    paragraph.font.color.rgb = colors['text']
                table.cell(i, j).fill.solid()
                table.cell(i, j).fill.fore_color.rgb = RGBColor(30, 35, 45)
                table.cell(i, j).fill.transparency = 0.3

def create_resources_box(slide, resources, colors):
    """在幻灯片底部创建拓展资源区域"""
    res_box = slide.shapes.add_textbox(Inches(1), Inches(6.5), Inches(13), Inches(1.8))
    res_frame = res_box.text_frame
    res_frame.word_wrap = True

    p = res_frame.add_paragraph()
    p.text = "📚 拓展学习资源"
    p.font.size = Pt(11)
    p.font.color.rgb = RGBColor(100, 200, 255)
    p.font.bold = True

    for res in resources[:2]:
        p = res_frame.add_paragraph()
        p.text = res
        p.font.size = Pt(9)
        p.font.color.rgb = RGBColor(180, 190, 200)

def create_summary_slide(prs):
    """创建总结页"""
    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(15, 20, 30)

    shapes = slide.shapes
    bar = shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(8.6), Inches(16), Inches(0.15))
    bar.fill.solid()
    bar.fill.fore_color.rgb = RGBColor(0, 180, 255)

    oval = shapes.add_shape(MSO_SHAPE.OVAL, Inches(7), Inches(0), Inches(9), Inches(9))
    oval.fill.solid()
    oval.fill.fore_color.rgb = RGBColor(0, 80, 150)
    oval.fill.transparency = 0.85

    title_box = slide.shapes.add_textbox(Inches(3), Inches(0.8), Inches(10), Inches(1))
    title_frame = title_box.text_frame
    p = title_frame.add_paragraph()
    p.text = "🎯 核心要点总结"
    p.font.size = Pt(26)
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

    summary_data = [
        ['章节', '核心内容', '关键价值'],
        ['第一章', '去中心化Agent协作架构', '高可用、弹性扩展'],
        ['第二章', 'JSON-RPC 2.0协议规范', '跨平台互操作性'],
        ['第三章', 'OAuth2 + mTLS安全体系', '企业级安全保障'],
        ['第四章', 'K8s高可用部署实践', '99.99%可用性'],
        ['第五章', '缓存+批量性能优化', '性能提升3倍'],
        ['第六章', '供应链+金融风控案例', '业务价值验证']
    ]

    table = slide.shapes.add_table(7, 3, Inches(1), Inches(2), Inches(14), Inches(5)).table

    for i, row in enumerate(summary_data):
        for j, cell in enumerate(row):
            table.cell(i, j).text = cell
            paragraph = table.cell(i, j).text_frame.paragraphs[0]
            paragraph.font.size = Pt(12)
            paragraph.alignment = PP_ALIGN.CENTER

            if i == 0:
                paragraph.font.color.rgb = RGBColor(255, 255, 255)
                paragraph.font.bold = True
                table.cell(i, j).fill.solid()
                table.cell(i, j).fill.fore_color.rgb = RGBColor(0, 180, 255)
            else:
                paragraph.font.color.rgb = RGBColor(220, 225, 235)
                table.cell(i, j).fill.solid()
                table.cell(i, j).fill.fore_color.rgb = RGBColor(30, 35, 45)

    return slide

def create_thank_you_slide(prs):
    """创建感谢页"""
    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(10, 15, 25)

    shapes = slide.shapes

    oval = shapes.add_shape(MSO_SHAPE.OVAL, Inches(5), Inches(1), Inches(6), Inches(6))
    oval.fill.solid()
    oval.fill.fore_color.rgb = RGBColor(0, 100, 200)
    oval.fill.transparency = 0.7

    hexagon = shapes.add_shape(MSO_SHAPE.HEXAGON, Inches(7.5), Inches(3), Inches(1.5), Inches(1.5))
    hexagon.fill.solid()
    hexagon.fill.fore_color.rgb = RGBColor(0, 180, 255)
    hexagon.fill.transparency = 0.4
    hexagon.line.fill.background()

    thank_box = slide.shapes.add_textbox(Inches(2), Inches(4.5), Inches(12), Inches(2))
    thank_frame = thank_box.text_frame
    p = thank_frame.add_paragraph()
    p.text = "THANK YOU"
    p.font.size = Pt(48)
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

    p = thank_frame.add_paragraph()
    p.text = "谢谢"
    p.font.size = Pt(32)
    p.font.color.rgb = RGBColor(0, 180, 255)
    p.alignment = PP_ALIGN.CENTER

    presenter_box = slide.shapes.add_textbox(Inches(3), Inches(7), Inches(10), Inches(1))
    presenter_frame = presenter_box.text_frame
    p = presenter_frame.add_paragraph()
    p.text = "【主讲人：何晓冬】"
    p.font.size = Pt(18)
    p.font.color.rgb = RGBColor(255, 200, 100)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

    return slide

def parse_markdown_for_tables(md_content):
    """解析Markdown，提取章节表格数据，按正确顺序排列"""
    chapters = {}

    lines = md_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith('# 第') and '章：' in line:
            title = line[2:].strip()

            chapter_num = None
            for idx, expected_title in enumerate(CHAPTER_TITLES, 1):
                if title.startswith(expected_title[:5]):
                    chapter_num = idx
                    break

            if chapter_num is None:
                i += 1
                continue

            tables = []
            i += 1

            while i < len(lines):
                if lines[i].startswith('|'):
                    table_data = []
                    while i < len(lines) and lines[i].startswith('|'):
                        row = lines[i].strip().split('|')
                        row = [cell.strip() for cell in row if cell.strip()]
                        table_data.append(row)
                        i += 1
                    if len(table_data) > 1:
                        tables.append(table_data)
                elif lines[i].startswith('# 第') and '章：' in lines[i]:
                    break
                elif lines[i].startswith('---'):
                    i += 1
                    continue
                else:
                    i += 1

            if not tables and chapter_num in DEFAULT_TABLES:
                tables.append(DEFAULT_TABLES[chapter_num])

            if tables:
                chapters[chapter_num] = {
                    'num': chapter_num,
                    'title': title,
                    'tables': tables
                }

        i += 1

    result = []
    for num in range(1, 7):
        if num in chapters:
            result.append(chapters[num])
        elif num in DEFAULT_TABLES:
            result.append({
                'num': num,
                'title': CHAPTER_TITLES[num-1],
                'tables': [DEFAULT_TABLES[num]]
            })

    return result

def create_pptx_compact(chapters, output_path):
    """创建精简版PPTX文件"""
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)

    create_title_slide(prs)

    for chapter in chapters:
        create_chapter_slide(prs, chapter)

    create_summary_slide(prs)
    create_thank_you_slide(prs)

    prs.save(output_path)
    print(f"PPTX文件已生成: {output_path}")
    print(f"共生成 {len(chapters) + 3} 页幻灯片")

if __name__ == '__main__':
    md_file = r'f:\个人作品\legal-rag-qa-system\A2A_ENTERPRISE_PPT.md'
    output_file = r'f:\个人作品\legal-rag-qa-system\A2A_ENTERPRISE_PPT_V2.pptx'

    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    chapters = parse_markdown_for_tables(md_content)
    print(f"检测到 {len(chapters)} 个章节")
    for ch in chapters:
        print(f"  第{ch['num']}章: {ch['title']}")

    create_pptx_compact(chapters, output_file)