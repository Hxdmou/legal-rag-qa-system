from pptx import Presentation

# 复制文件并重命名
import shutil
src = r"f:\个人作品\legal-rag-qa-system\A2A_PROTOCOL_AI_AGENT_V14_终极完整版.pptx"
dst = r"f:\个人作品\legal-rag-qa-system\AI_AGENT_PROTOCOL_FINAL_2026_最新完整版.pptx"

shutil.copy(src, dst)
print(f"✅ 已创建全新文件: {dst}")
print("\n💡 请从文件资源管理器打开这个文件！")