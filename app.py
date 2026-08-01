import streamlit as st
import sys, os, time, io, re
sys.path.insert(0, os.path.dirname(__file__))
from self_ref_module import analyze
from docx import Document
import PyPDF2

# ---------- 页面配置 ----------
st.set_page_config(page_title="太初 · 自指诊断系统", page_icon="🔍", layout="wide")

# ---------- 深色模式 ----------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

# 自定义CSS
if st.session_state.dark_mode:
    st.markdown("""
    <style>
    .stApp { background-color: #1e1e1e; color: #d4d4d4; }
    .stTextArea textarea, .stButton button, .stSelectbox, .stFileUploader { 
        background-color: #2d2d2d !important; color: #d4d4d4 !important; 
        border-color: #555 !important;
    }
    .st-b7 { background-color: #2d2d2d !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------- 标题和主题切换 ----------
col_title, col_theme = st.columns([4, 1])
with col_title:
    st.title("🔍 太初 · 自指诊断系统")
    st.markdown("**TSRE + TLF 统一集成 v1.3** — 支持文本/文件/高亮/历史")
with col_theme:
    if st.button("🌙" if not st.session_state.dark_mode else "☀️"):
        toggle_theme()
        st.rerun()

# ---------- 快速示例 ----------
st.markdown("### 📌 快速示例")
cols = st.columns(4)
if cols[0].button("⚖️ 稳定"):
    st.session_state.text_input = "太阳是恒星，地球是行星。"
if cols[1].button("⚠️ 张力"):
    st.session_state.text_input = "太阳是恒星，太阳不是恒星。"
if cols[2].button("🧩 碎片"):
    st.session_state.text_input = "这个句子包含五个词。"
if cols[3].button("🧠 认知"):
    st.session_state.text_input = "我思故我在。思维是存在的本质，存在通过思维被确认。思维与存在的同一性在此达成闭合。"

# ---------- 输入区域 ----------
col_input, col_upload = st.columns([3, 1])
with col_input:
    text_input = st.text_area("输入文本", height=200, key="text_input")
with col_upload:
    st.markdown("### 📤 上传文件")
    uploaded = st.file_uploader("支持 .txt/.docx/.pdf", type=["txt","docx","pdf"])
    if uploaded:
        # 提取文本（简化版，实际使用与之前相同）
        content = uploaded.read()
        if uploaded.type == "text/plain":
            text_input = content.decode("utf-8", errors="ignore")
        elif uploaded.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(io.BytesIO(content))
            text_input = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif uploaded.type == "application/pdf":
            pdf = PyPDF2.PdfReader(io.BytesIO(content))
            text_input = "\n".join([page.extract_text() or "" for page in pdf.pages])
        st.session_state.text_input = text_input
        st.success(f"已加载 {len(text_input)} 字符")

# ---------- 字数统计 + 清空 ----------
col_cnt, col_clr = st.columns([6,1])
with col_cnt:
    st.caption(f"字数：{len(text_input)} 字符")
with col_clr:
    if st.button("🗑️ 清空"):
        st.session_state.text_input = ""
        st.rerun()

# ---------- 诊断按钮 ----------
if st.button("🚀 开始诊断"):
    if not text_input.strip():
        st.warning("请输入文本或上传文件")
    else:
        # ----- 进度条模拟 -----
        progress = st.progress(0)
        status_text = st.empty()
        status_text.text("⏳ 步骤 1/3: 计算自指分数...")
        time.sleep(0.3)
        progress.progress(30)

        status_text.text("⏳ 步骤 2/3: 检测逻辑冲突...")
        time.sleep(0.3)
        progress.progress(60)

        # 执行分析
        result = analyze(text_input)
        progress.progress(90)
        status_text.text("⏳ 步骤 3/3: 生成诊断报告...")
        time.sleep(0.2)
        progress.progress(100)
        status_text.text("✅ 诊断完成")
        time.sleep(0.2)
        status_text.empty()
        progress.empty()

        # ----- 显示结果（打字机效果：逐行输出） -----
        placeholder = st.empty()
        lines = []

        # 收集要输出的行
        lines.append(f"📊 **TSRE 自指分数**：{result['tsre']['score']:.4f}（{result['tsre']['level']}）")
        lines.append(f"📊 **TLF 逻辑冲突**：{result['tlf']['conflict_count']} 个")
        lines.append(f"📊 **整体状态**：{result['summary']['overall_status']}")

        gs = result.get('global_state')
        if gs:
            status = gs['status']
            status_labels = {"CONSCIOUS":"🧠 认知","STABLE":"⚖️ 稳定","TENSION":"⚠️ 张力","FRAGMENTED":"🧩 碎片"}
            color_map = {"CONSCIOUS":"#00c853","STABLE":"#2979ff","TENSION":"#ff9100","FRAGMENTED":"#ff1744"}
            label = status_labels.get(status, status)
            color = color_map.get(status, "#888")
            lines.append(f"📊 **全局状态**：<span style='color:{color};'>{label}</span>")
            lines.append(f"📊 **事件**：{gs['event'].get('message', '无')}")

        # 逐行输出（打字机模拟）
        for i, line in enumerate(lines):
            placeholder.markdown(line + "\n\n" if i==0 else line + "\n\n", unsafe_allow_html=True)
            time.sleep(0.3)

        # ----- 高亮文本显示 -----
        st.divider()
        st.subheader("🔍 高亮显示冲突位置")
        highlighted = result.get('highlighted_text', text_input)
        st.markdown(f"<div style='padding:10px; border:1px solid #ddd; border-radius:8px;'>{highlighted}</div>", unsafe_allow_html=True)

        # ----- 详细冲突列表 -----
        st.subheader("📋 冲突详情")
        if result['tlf']['conflicts']:
            st.error("❌ 检测到以下冲突：")
            for c in result['tlf']['conflicts']:
                st.write(f"- {c}")
        else:
            st.success("✅ 未检测到逻辑冲突")

        # ----- 优化建议 -----
        if result['summary']['suggestions']:
            st.info("💡 优化建议：")
            for s in result['summary']['suggestions']:
                st.write(f"- {s}")

        # ----- 导出报告 -----
        report = f"""# 太初·诊断报告
时间：{gs['timestamp'] if gs else '未知'}
TSRE分数：{result['tsre']['score']:.4f}
TLF冲突数：{result['tlf']['conflict_count']}
状态：{status if gs else '未知'}
冲突列表：
{chr(10).join(['- '+c for c in result['tlf']['conflicts']]) if result['tlf']['conflicts'] else '无'}
建议：
{chr(10).join(['- '+s for s in result['summary']['suggestions']]) if result['summary']['suggestions'] else '无'}
"""
        st.download_button("📄 导出报告", data=report, file_name="taichu_report.md", mime="text/markdown")

        # ----- 保存历史记录 -----
        if "history" not in st.session_state:
            st.session_state.history = []
        # 只保存摘要（前20字）
        summary = text_input[:30] + "..." if len(text_input)>30 else text_input
        st.session_state.history.insert(0, {
            "text": summary,
            "status": result['summary']['overall_status'],
            "tsre": result['tsre']['score'],
            "conflicts": result['tlf']['conflict_count']
        })
        if len(st.session_state.history) > 5:
            st.session_state.history.pop()

# ---------- 侧边栏：历史记录 ----------
with st.sidebar:
    st.header("📜 历史记录")
    if "history" in st.session_state and st.session_state.history:
        for idx, record in enumerate(st.session_state.history):
            st.markdown(f"**{idx+1}.** {record['text']}")
            st.caption(f"状态：{record['status']}  |  TSRE：{record['tsre']:.2f}  |  冲突：{record['conflicts']}")
            st.divider()
    else:
        st.info("暂无诊断记录")

st.divider()
st.caption("太初架构 v1.3 | 包含进度条·打字机·深色模式·历史记录·高亮 | MIT License")
