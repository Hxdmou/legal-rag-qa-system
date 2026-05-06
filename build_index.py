import os
import shutil
from rag import load_multiple_documents, chunk2vector, embeddings
from config.settings import SYSTEM_CONFIGS

def build_index_for_system(system_name, doc_paths):
    """为指定系统构建知识库索引"""
    index_dir = f"{system_name}_faiss_index"
    
    # 删除旧索引
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)
        print(f"已删除旧索引: {index_dir}")
    
    if not doc_paths or len(doc_paths) == 0:
        print(f"警告: {system_name} 没有文档文件可用于构建索引")
        return False
    
    try:
        print(f"正在为 {system_name} 加载文档...")
        docs = load_multiple_documents(doc_paths)
        
        if not docs:
            print(f"警告: {system_name} 文档加载为空")
            return False
        
        print(f"正在为 {system_name} 创建向量索引...")
        vector_store = chunk2vector(docs, embeddings)
        vector_store.save_local(index_dir)
        
        print(f"✅ {system_name} 知识库索引构建成功，共 {len(docs)} 份文档")
        return True
    except Exception as e:
        print(f"❌ {system_name} 索引构建失败: {str(e)}")
        return False

def create_sample_knowledge_base():
    """创建各系统的示例知识库文档"""
    # 创建数据目录
    os.makedirs("knowledge_bases", exist_ok=True)
    
    # 医疗健康示例数据
    medical_content = """# 医疗健康知识手册

## 常见疾病

### 感冒
- 症状：发烧、咳嗽、流鼻涕、喉咙痛
- 治疗：多喝水、休息、服用感冒药
- 预防：勤洗手、保持通风、接种疫苗

### 高血压
- 症状：头痛、头晕、心悸
- 治疗：低盐饮食、规律运动、药物治疗
- 注意：定期监测血压

## 健康生活方式
- 均衡饮食：多吃蔬菜水果，减少油腻食物
- 规律运动：每周至少150分钟中等强度运动
- 充足睡眠：每天7-8小时睡眠
- 戒烟限酒：避免吸烟，限制饮酒量

## 用药安全
- 遵医嘱用药，不要自行增减剂量
- 注意药物过敏史
- 药物过期后请勿使用
- 多种药物同时服用时需咨询医生
"""
    with open("knowledge_bases/medical_health.txt", "w", encoding="utf-8") as f:
        f.write(medical_content)
    
    # 教育学习示例数据
    education_content = """# 教育学习指南

## 学习方法
### 主动学习
- 积极提问，主动思考
- 做笔记，整理知识体系
- 讲解给他人听，检验理解

### 时间管理
- 制定学习计划，合理安排时间
- 使用番茄工作法，提高专注度
- 劳逸结合，避免过度疲劳

## 考试技巧
- 考前复习重点，不要临时抱佛脚
- 仔细审题，理解题意
- 先易后难，合理分配答题时间
- 检查答案，避免粗心错误

## 学科学习
### 数学
- 理解概念，多做练习
- 建立错题本，定期复习
- 掌握解题思路和方法

### 语文
- 多读经典名著，积累词汇
- 练习写作，提高表达能力
- 背诵古诗文，增强语感
"""
    with open("knowledge_bases/education_guide.txt", "w", encoding="utf-8") as f:
        f.write(education_content)
    
    # 金融投资示例数据
    finance_content = """# 金融投资知识

## 投资原则
### 风险与收益
- 高风险高回报，低风险低回报
- 根据风险承受能力选择投资产品
- 不要把所有鸡蛋放在一个篮子里

### 投资类型
- 股票：高风险高收益，适合长期投资
- 基金：分散投资，风险适中
- 债券：低风险，稳定收益
- 存款：保本保息，收益较低

## 投资策略
- 定期定额投资，平均成本
- 长期持有，避免频繁交易
- 关注市场动态，但不盲目跟风

## 理财规划
- 设定明确的理财目标
- 建立应急储备金（3-6个月生活费）
- 合理配置资产，平衡风险与收益

⚠️ 投资有风险，入市需谨慎。本信息仅供参考，不构成投资建议。
"""
    with open("knowledge_bases/finance_investment.txt", "w", encoding="utf-8") as f:
        f.write(finance_content)
    
    # IT技术示例数据
    tech_content = """# IT技术手册

## 编程基础
### Python
- 简洁易读，适合初学者
- 广泛应用于数据分析、人工智能
- 丰富的第三方库支持

### JavaScript
- 网页开发必备语言
- 支持前端和后端开发（Node.js）
- 事件驱动，异步编程

## 开发工具
- Git：版本控制工具
- VS Code：轻量级代码编辑器
- Docker：容器化部署
- Jenkins：持续集成/持续部署

## 架构设计
- 微服务架构：将应用拆分为独立服务
- RESTful API：标准化接口设计
- 数据库设计：合理设计表结构，建立索引
- 缓存策略：使用Redis等缓存提高性能

## 安全注意
- 输入验证：防止SQL注入、XSS攻击
- 密码加密：使用强哈希算法存储密码
- HTTPS：确保数据传输安全
- 定期更新依赖，修复安全漏洞
"""
    with open("knowledge_bases/tech_guide.txt", "w", encoding="utf-8") as f:
        f.write(tech_content)
    
    print("✅ 示例知识库文档创建完成")

def main():
    print("=" * 60)
    print("开始为所有系统构建知识库索引")
    print("=" * 60)
    
    # 创建示例知识库
    create_sample_knowledge_base()
    
    # 为每个系统构建索引
    systems = {
        "general": {
            "name": "通用RAG智能问答系统",
            "docs": [
                "knowledge_bases/medical_health.txt",
                "knowledge_bases/education_guide.txt",
                "knowledge_bases/finance_investment.txt",
                "knowledge_bases/tech_guide.txt"
            ]
        },
        "legal": {
            "name": "法律知识问答系统",
            "docs": [os.path.join("legal_knowledge_base", f) for f in os.listdir("legal_knowledge_base") if f.endswith(".pdf")]
        },
        "medical": {
            "name": "医疗健康问答系统",
            "docs": ["knowledge_bases/medical_health.txt"]
        },
        "education": {
            "name": "教育学习问答系统",
            "docs": ["knowledge_bases/education_guide.txt"]
        },
        "finance": {
            "name": "金融投资问答系统",
            "docs": ["knowledge_bases/finance_investment.txt"]
        },
        "tech": {
            "name": "IT技术问答系统",
            "docs": ["knowledge_bases/tech_guide.txt"]
        }
    }
    
    success_count = 0
    total_count = len(systems)
    
    for system_key, system_info in systems.items():
        print(f"\n--- 正在处理: {system_info['name']} ---")
        if build_index_for_system(system_key, system_info['docs']):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"索引构建完成！成功: {success_count}/{total_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
