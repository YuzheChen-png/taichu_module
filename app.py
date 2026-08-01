import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from self_ref_module import analyze

# 文件处理库
import io
import re

# 尝试导入文档处理库（如果未安装，st.file_uploader 仍可工作但会提示）
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

st.set_page_config(page_title="太初 · 自指诊断系统", page_icon="🔍", layout="wide")

st.title("🔍 太初 · 自指诊断系统")
st.markdown("**TSRE + TLF 统一集成 v1.2** — 支持文本输入和文件上传")

# ============================================================
# 文件内容提取函数
# ============================================================

def extract_text_from_file(uploaded_file) -> str:
    """从上传的文件中提取文本"""
    file_type = uploaded_file.type
    content = uploaded_file.read()

    # TXT 文件
    if file_type == "text/plain":
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return content.decode("gbk")
            except:
                return "无法解码文件，请确认文件编码为 UTF-8 或 GBK。"

    # DOCX 文件
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        if not HAS_DOCX:
            return "⚠️ 需要安装 python-docx 库才能读取 .docx 文件。请运行：pip install python-docx"
        try:
            doc = Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            return text if text.strip() else "文档内容为空。"
        except Exception as e:
            return f"读取 .docx 文件失败：{str(e)}"

    # PDF 文件
    elif file_type == "application/pdf":
        if not HAS_PDF:
            return "⚠️ 需要安装 PyPDF2 库才能读取 .pdf 文件。请运行：pip install PyPDF2"
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text if text.strip() else "PDF 内容为空（可能为扫描件）。"
        except Exception as e:
            return f"读取 .pdf 文件失败：{str(e)}"

    # 其他格式
    else:
        return f"暂不支持的文件格式：{file_type}。请上传 .txt、.docx 或 .pdf 文件。"

# ============================================================
# 布局：文本输入 + 文件上传 并排
# ============================================================

col_input, col_upload = st.columns([3, 1])

with col_input:
    text_input = st.text_area(
        "输入文本",
        height=200,
        placeholder="粘贴你要诊断的文本...",
        key="text_input"
    )

with col_upload:
    st.markdown("### 📤 上传文件")
    uploaded_file = st.file_uploader(
        "支持 .txt / .docx / .pdf",
        type=["txt", "docx", "pdf"],
        key="file_uploader"
    )

    if uploaded_file is not None:
        st.success(f"✅ 已上传：{uploaded_file.name}")
        st.caption(f"大小：{uploaded_file.size} 字节")

        # 自动提取文件内容
        extracted_text = extract_text_from_file(uploaded_file)
        if extracted_text.startswith("⚠️") or extracted_text.startswith("无法"):
            st.warning(extracted_text)
        else:
            # 将提取的文本填入输入框
            text_input = extracted_text
            st.info(f"已提取 {len(extracted_text)} 个字符")
            # 使用 session_state 更新文本输入框
            st.session_state.text_input = extracted_text

# 如果 session_state 中有文本，更新 text_input
if "text_input" in st.session_state and st.session_state.text_input:
    text_input = st.session_state.text_input

# ============================================================
# 诊断按钮
# ============================================================

if st.button("🚀 开始诊断"):
    if not text_input.strip():
        st.warning("请先输入文本或上传文件")
    else:
        with st.spinner("分析中..."):
            result = analyze(text_input)

        # ========== 第一行：核心指标 ==========
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("TSRE 自指分数", f"{result['tsre']['score']:.4f}", result['tsre']['level'])
        col2.metric("TLF 逻辑冲突", result['tlf']['conflict_count'], "有冲突" if result['tlf']['conflicts'] else "无冲突")
        col3.metric("整体状态", result['summary']['overall_status'])

        # ========== 全局状态卡片 ==========
        gs = result.get('global_state')
        if gs:
            status = gs['status']
            event = gs['event']

            status_map = {
                "CONSCIOUS": {"color": "#00c853", "icon": "🧠", "label": "认知状态"},
                "STABLE": {"color": "#2979ff", "icon": "⚖️", "label": "稳定状态"},
                "TENSION": {"color": "#ff9100", "icon": "⚠️", "label": "张力状态"},
                "FRAGMENTED": {"color": "#ff1744", "icon": "🧩", "label": "碎片状态"}
            }
            info = status_map.get(status, {"color": "#gray", "icon": "❓", "label": "未知"})

            st.markdown(f"""
            <div style="
                background-color: {info['color']}22;
                border-left: 6px solid {info['color']};
                padding: 20px;
                border-radius: 8px;
                margin: 10px 0;
            ">
                <h3 style="margin:0; color:{info['color']};">
                    {info['icon']} 全局状态：{info['label']}（{status}）
                </h3>
                <p style="margin:8px 0 0 0; font-size:16px;">
                    {event.get('message', '无事件')}
                </p>
                <p style="margin:4px 0 0 0; font-size:14px; color:#888;">
                    建议操作：{event.get('action', '无')}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # ========== 详细结果 ==========
        st.divider()
        st.subheader("📋 详细诊断结果")

        if result['tlf']['conflicts']:
            st.error("❌ 检测到逻辑冲突：")
            for c in result['tlf']['conflicts']:
                st.write(f"- {c}")
        else:
            st.success("✅ TLF 未检测到逻辑冲突")

        if result['summary']['suggestions']:
            st.info("💡 优化建议：")
            for s in result['summary']['suggestions']:
                st.write(f"- {s}")

        if result['summary']['is_valid']:
            st.success("✅ 文本通过统一诊断，逻辑自洽性良好。")
        else:
            st.error("❌ 文本未通过统一诊断，请根据建议优化。")

        if gs and gs.get('timestamp'):
            st.caption(f"诊断时间：{gs['timestamp']}")

st.divider()
st.caption("太初架构 · 自指模块层 v1.2 | 支持文件上传 | MIT License")
