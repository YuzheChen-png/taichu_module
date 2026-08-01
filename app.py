import streamlit as st
import sys, os, time, io, re, hashlib, logging, traceback
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from self_ref_module import analyze

# ---------- 日志配置 ----------
LOG_FILE = os.path.join(os.path.dirname(__file__), "taichu_error.log")
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ---------- 文档处理 ----------
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

# ---------- 页面配置 ----------
st.set_page_config(page_title="太初 · 自指诊断系统 v2.0", page_icon="🔍", layout="wide")

# ---------- 初始化 session_state ----------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "cache" not in st.session_state:
    st.session_state.cache = {}
if "history" not in st.session_state:
    st.session_state.history = []
if "text_input" not in st.session_state:
    st.session_state.text_input = ""

# ---------- 深色模式 ----------
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

# ---------- 标题 ----------
col_title, col_theme = st.columns([4, 1])
with col_title:
    st.title("🔍 太初 · 自指诊断系统")
    st.markdown("**v2.0** — 完整优化版：缓存·快捷键·日志·高亮·多维度·自动修正")
    st.caption(f"缓存大小：{len(st.session_state.cache)} 条")
with col_theme:
    if st.button("🌙" if not st.session_state.dark_mode else "☀️"):
        toggle_theme()
        st.rerun()

# ---------- 快速示例 ----------
st.markdown("### 📌 快速示例")
cols = st.columns(4)
if cols[0].button("⚖️ 稳定"): st.session_state.text_input = "太阳是恒星，地球是行星。"
if cols[1].button("⚠️ 张力"): st.session_state.text_input = "太阳是恒星，太阳不是恒星。苹果是水果。"
if cols[2].button("🧩 碎片"): st.session_state.text_input = "这个句子包含五个词。苹果是动物。"
if cols[3].button("🧠 认知"): st.session_state.text_input = "我思故我在。思维是存在的本质，存在通过思维被确认。思维与存在的同一性在此达成闭合。"

# ---------- 输入区域 ----------
col_input, col_upload = st.columns([3, 1])
with col_input:
    text_input = st.text_area("输入文本（Ctrl+Enter 快速诊断）", height=200, key="text_input",
                               placeholder="支持多段落文本...")
with col_upload:
    st.markdown("### 📤 上传文件")
    uploaded = st.file_uploader("支持 .txt/.docx/.pdf", type=["txt","docx","pdf"])
    if uploaded:
        try:
            content = uploaded.read()
            if uploaded.type == "text/plain":
                text_input = content.decode("utf-8", errors="ignore")
            elif uploaded.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" and HAS_DOCX:
                doc = Document(io.BytesIO(content)); text_input = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            elif uploaded.type == "application/pdf" and HAS_PDF:
                pdf = PyPDF2.PdfReader(io.BytesIO(content)); text_input = "\n".join([page.extract_text() or "" for page in pdf.pages])
            else:
                st.warning("文件格式不支持或缺少依赖库")
            st.session_state.text_input = text_input
            st.success(f"已加载 {len(text_input)} 字符")
        except Exception as e:
            st.error(f"读取文件失败：{str(e)}")

col_cnt, col_clr = st.columns([6,1])
with col_cnt:
    st.caption(f"字数：{len(text_input)} 字符")
with col_clr:
    if st.button("🗑️ 清空"):
        st.session_state.text_input = ""
        st.rerun()

# ---------- Ctrl+Enter 快捷键 ----------
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        var buttons = document.querySelectorAll('button');
        for (var btn of buttons) {
            if (btn.innerText.includes('开始诊断')) {
                btn.click(); e.preventDefault(); break;
            }
        }
    }
});
</script>
""", unsafe_allow_html=True)

# ---------- 诊断 ----------
if st.button("🚀 开始诊断"):
    if not text_input.strip():
        st.warning("请输入文本或上传文件")
    else:
        try:
            # 检查缓存
            text_hash = hashlib.md5(text_input.encode()).hexdigest()
            if text_hash in st.session_state.cache:
                result = st.session_state.cache[text_hash]
                st.info("⚡ 从缓存加载结果（文本未变化）")
                cached = True
            else:
                cached = False

                # 进度条
                progress = st.progress(0); status_text = st.empty()
                status_text.text("⏳ 步骤 1/4: 计算自指分数..."); time.sleep(0.2); progress.progress(25)
                status_text.text("⏳ 步骤 2/4: 检测逻辑冲突..."); result = analyze(text_input); time.sleep(0.2); progress.progress(50)
                status_text.text("⏳ 步骤 3/4: 多维度评分..."); time.sleep(0.2); progress.progress(75)
                status_text.text("⏳ 步骤 4/4: 生成修正建议..."); time.sleep(0.2); progress.progress(100)
                status_text.text("✅ 诊断完成"); time.sleep(0.3); status_text.empty(); progress.empty()

                # 存入缓存（限制100条）
                st.session_state.cache[text_hash] = result
                if len(st.session_state.cache) > 100:
                    st.session_state.cache.pop(next(iter(st.session_state.cache)))

            # ---------- 显示结果 ----------
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
                labels = {"CONSCIOUS":"🧠 认知","STABLE":"⚖️ 稳定","TENSION":"⚠️ 张力","FRAGMENTED":"🧩 碎片"}
                colors = {"CONSCIOUS":"#00c853","STABLE":"#2979ff","TENSION":"#ff9100","FRAGMENTED":"#ff1744"}
                label = labels.get(status, status); color = colors.get(status, "#888")
                st.markdown(f"""
                <div style="background-color:{color}22; border-left:6px solid {color}; padding:15px; border-radius:8px; margin:10px 0;">
                    <h3 style="margin:0; color:{color};">{label} 状态</h3>
                    <p style="margin:8px 0 0 0;">{gs['event'].get('message', '')}</p>
                    <p style="margin:4px 0 0 0; font-size:14px; color:#888;">建议操作：{gs['event'].get('action', '无')}</p>
                </div>
                """, unsafe_allow_html=True)

            # 高亮显示
            st.divider()
            st.subheader("🔍 高亮冲突句子")
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

            # 修正建议
            fix_suggestions = result.get('fix_suggestions', [])
            if fix_suggestions:
                st.subheader("🛠️ 自动修正建议")
                for s in fix_suggestions:
                    st.info(s)

            # 综合建议
            if result['summary']['suggestions']:
                st.info("💡 综合优化建议：")
                for s in result['summary']['suggestions']:
                    st.write(f"- {s}")

            # 导出报告
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
            st.download_button("📄 导出报告", data=report, file_name=f"taichu_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", mime="text/markdown")

            # 保存历史
            summary = text_input[:30] + "..." if len(text_input)>30 else text_input
            st.session_state.history.insert(0, {
                "text": summary, "status": result['summary']['overall_status'],
                "tsre": result['tsre']['score'], "conflicts": result['tlf']['conflict_count']
            })
            if len(st.session_state.history) > 5:
                st.session_state.history.pop()

        except Exception as e:
            error_msg = traceback.format_exc()
            logging.error(error_msg)
            st.error(f"❌ 诊断过程出错：{str(e)}")
            st.caption("错误已记录到日志文件，请稍后重试。")

# ---------- 侧边栏 ----------
with st.sidebar:
    st.header("📜 历史记录")
    if st.session_state.history:
        for idx, record in enumerate(st.session_state.history):
            st.markdown(f"**{idx+1}.** {record['text']}")
            st.caption(f"状态：{record['status']}  |  TSRE：{record['tsre']:.2f}  |  冲突：{record['conflicts']}")
            st.divider()
    else:
        st.info("暂无诊断记录")

    st.divider()
    st.caption(f"缓存条目：{len(st.session_state.cache)}")
    if st.button("🗑️ 清空缓存"):
        st.session_state.cache = {}
        st.rerun()

st.divider()
st.caption("太初架构 v2.0 | MIT License | 错误日志：taichu_error.log")
