# 法律知识问答系统 (Legal RAG QA System)
基于 RAG（检索增强生成）技术的智能法律问答系统。上传法律文档（PDF、TXT、Excel），系统自动建立向量索引，支持智能问答。
![演示截图](./demo_screenshot.png)
## 核心功能
- 📄 支持多格式文档（PDF、TXT、Excel）
- 🔍 混合检索（BM25 + 向量嵌入）提升准确性
- 💬 多轮对话，历史自动保存
- 📚 知识库可视化管理（增、删、查）
- ⚡ Streamlit Web 界面，开箱即用
## 快速开始
1. 安装依赖: `pip install -r requirements.txt`
2. 启动系统: `streamlit run medical_qa_fixed.py --server.port 7869`
3. 浏览器打开 `http://localhost:7869`
## 效果预览
用户提问: "劳动合同法规定员工试用期最长时间为多久？"
系统回答（基于《劳动合同法》第十九条）:
> 三年以上固定期限和无固定期限的劳动合同，试用期不得超过**六个月**。
📌 详见 [完整作品集](./法律知识问答系统.pdf) 和 [文档测试结果](./文档测试结果.pdf)
## 技术栈
- LangChain + Chroma/FAISS
- Streamlit
- DeepSeek / Qwen API
- 混合检索（BM25 + 向量）
## 联系作者
本系统可定制部署（本地/云端），也接受法律、医疗、金融等垂直领域的定制开发。
📧 邮箱: 979718240@qq.com
💬 微信: 15055256203
> 声明: 本系统仅供学习参考，具体法律问题请咨询专业律师。