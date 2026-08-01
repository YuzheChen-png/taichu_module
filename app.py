import streamlit as st
import sys, os, time, io, re
sys.path.insert(0, os.path.dirname(__file__))
from self_ref_module import analyze
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

# 深色模式
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode
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

col_title, col_theme = st.columns([4, 1])
with col_title:
    st.title("🔍 太初 · 自指诊断系统")
    st.markdown("**TSRE + TLF v1.4** — 功能深度增强版：句子级高亮·多维度·自动修正")
with col_theme:
    if st.button("🌙" if not st.session_state.dark_mode else "☀️"):
        toggle_theme()
        st.rerun()

# 快速示例
st.markdown("### 📌 快速示例")
cols = st.columns(4)
if cols[0].button("⚖️ 稳定"):
    st.session_state.text_input = "太阳是恒星，地球是行星。"
if cols[1].button("⚠️ 张力"):
    st.session_state.text_input = "太阳是恒星，太阳不是恒星。苹果是水果。"
if cols[2].button("🧩 碎片"):
    st.session_state.text_input = "这个句子包含五个词。苹果是动物。"
if cols[3].button("🧠 认知"):
    st.session_state.text_input = "我思故我在。思维是存在的本质，存在通过思维被确认。思维与存在的同一性在此达成闭合。"

# 输入区域
col_input, col_upload = st.columns([3, 1])
with col_input:
    text_input = st.text_area("输入文本", height=200, key="text_input", placeholder="支持多段落文本...")
with col_upload:
    st.markdown("### 📤 上传文件")
    uploaded = st.file_uploader("支持 .txt/.docx/.pdf", type=["txt","docx","pdf"])
    if uploaded:
        content = uploaded.read()
        if uploaded.type == "text/plain":
            text_input = content.decode("utf-8", errors="ignore")
        elif uploaded.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" and HAS_DOCX:
            doc = Document(io.BytesIO(content))
            text_input = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif uploaded.type == "application/pdf" and HAS_PDF:
            pdf = PyPDF2.PdfReader(io.BytesIO(content))
            text_input = "\n".join([page.extract_text() or "" for page in pdf.pages])
        else:
            st.warning("文件格式不支持或缺少依赖库")
        st.session_state.text_input = text_input
        st.success(f"已加载 {len(text_input)} 字符")

col_cnt, col_clr = st.columns([6,1])
with col_cnt:
    st.caption(f"字数：{len(text_input)} 字符")
with col_clr:
    if st.button("🗑️ 清空"):
        st.session_state.text_input = ""
        st.rerun()

if st.button("🚀 开始诊断"):
    if not text_input.strip():
        st.warning("请输入文本或上传文件")
    else:
        # 进度条
        progress = st.progress(0)
        status_text = st.empty()
        status_text.text("⏳ 步骤 1/4: 计算自指分数...")
        time.sleep(0.3)
        progress.progress(25)

        status_text.text("⏳ 步骤 2/4: 检测逻辑冲突...")
        result = analyze(text_input)
        time.sleep(0.3)
        progress.progress(50)

        status_text.text("⏳ 步骤 3/4: 多维度评分...")
        time.sleep(0.2)
        progress.progress(75)

        status_text.text("⏳ 步骤 4/4: 生成修正建议...")
        time.sleep(0.2)
        progress.progress(100)
        status_text.text("✅ 诊断完成")
        time.sleep(0.3)
        status_text.empty()
        progress.empty()

        # 显示核心指标（含多维度）
        col1, col2, col3 = st.columns(3)
        col1.metric("TSRE 自指分数", f"{result['tsre']['score']:.4f}", result['tsre']['level'])
        col2.metric("TLF 逻辑冲突", result['tlf']['conflict_count'], "有冲突" if result['tlf']['conflicts'] else "无冲突")
        col3.metric("整体状态", result['summary']['overall_status'])

        # 多维度评分
        st.subheader("📊 多维度评分")
        ms = result.get('multi_scores', {})
        if ms:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("逻辑密度", f"{ms.get('logic_density', 0):.2f}", help="冲突越少，密度越高")
            col_b.metric("结构复杂度", f"{ms.get('structure_complexity', 0):.2f}", help="句子长度与连接词综合")
            col_c.metric("语义连贯性", f"{ms.get('semantic_coherence', 0):.2f}", help="相邻句子相似度")

        # 全局状态卡片
        gs = result.get('global_state')
        if gs:
            status = gs['status']
            status_labels = {"CONSCIOUS":"🧠 认知","STABLE":"⚖️ 稳定","TENSION":"⚠️ 张力","FRAGMENTED":"🧩 碎片"}
            color_map = {"CONSCIOUS":"#00c853","STABLE":"#2979ff","TENSION":"#ff9100","FRAGMENTED":"#ff1744"}
            label = status_labels.get(status, status)
            color = color_map.get(status, "#888")
            st.markdown(f"""
            <div style="background-color:{color}22; border-left:6px solid {color}; padding:15px; border-radius:8px; margin:10px 0;">
                <h3 style="margin:0; color:{color};">{label} 状态</h3>
                <p style="margin:8px 0 0 0;">{gs['event'].get('message', '')}</p>
                <p style="margin:4px 0 0 0; font-size:14px; color:#888;">建议操作：{gs['event'].get('action', '无')}</p>
            </div>
            """, unsafe_allow_html=True)

        # 高亮显示（句子级）
        st.divider()
        st.subheader("🔍 高亮冲突句子（红色背景 + 标签）")
        highlighted = result.get('highlighted_text', text_input)
        st.markdown(f"<div style='padding:10px; border:1px solid #ddd; border-radius:8px;'>{highlighted}</div>", unsafe_allow_html=True)

        # 冲突详情
        st.subheader("📋 冲突详情")
        if result['tlf']['conflicts']:
            st.error("❌ 检测到以下冲突：")
            for c in result['tlf']['conflicts']:
                st.write(f"- {c}")
        else:
            st.success("✅ 未检测到逻辑冲突")

        # 自动修正建议
        fix_suggestions = result.get('fix_suggestions', [])
        if fix_suggestions:
            st.subheader("🛠️ 自动修正建议")
            for s in fix_suggestions:
                st.info(s)

        # 优化建议汇总
        if result['summary']['suggestions']:
            st.info("💡 综合优化建议：")
            for s in result['summary']['suggestions']:
                st.write(f"- {s}")

        # 导出报告（扩展版本）
        report = f"""# 太初·深度诊断报告
时间：{gs.get('timestamp', '未知') if gs else '未知'}
TSRE分数：{result['tsre']['score']:.4f}
TLF冲突数：{result['tlf']['conflict_count']}
多维度评分：
- 逻辑密度：{ms.get('logic_density', 0)}
- 结构复杂度：{ms.get('structure_complexity', 0)}
- 语义连贯性：{ms.get('semantic_coherence', 0)}
冲突列表：
{chr(10).join(['- '+c for c in result['tlf']['conflicts']]) if result['tlf']['conflicts'] else '无'}
修正建议：
{chr(10).join(['- '+s for s in fix_suggestions]) if fix_suggestions else '无'}
综合建议：
{chr(10).join(['- '+s for s in result['summary']['suggestions']]) if result['summary']['suggestions'] else '无'}
"""
        st.download_button("📄 导出报告", data=report, file_name="taichu_report.md", mime="text/markdown")

        # 保存历史
        if "history" not in st.session_state:
            st.session_state.history = []
        summary = text_input[:30] + "..." if len(text_input)>30 else text_input
        st.session_state.history.insert(0, {
            "text": summary,
            "status": result['summary']['overall_status'],
            "tsre": result['tsre']['score'],
            "conflicts": result['tlf']['conflict_count']
        })
        if len(st.session_state.history) > 5:
            st.session_state.history.pop()

# 侧边栏历史
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
st.caption("太初架构 v1.4 | 功能深度增强（句子级高亮·多维度·自动修正）| MIT License")
