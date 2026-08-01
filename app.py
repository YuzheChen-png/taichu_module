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
st.set_page_config(page_title="太初 · 自指诊断系统 v2.1", page_icon="🔍", layout="wide")

# ---------- 自定义 CSS（美化版） ----------
st.markdown("""
<style>
/* ===== 全局字体 ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, .stApp {
    font-family: 'Inter', sans-serif;
}

/* ===== 标题渐变 ===== */
.gradient-title {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 2.8rem;
    margin-bottom: 0.2rem;
}
.gradient-subtitle {
    color: #888;
    font-weight: 300;
    font-size: 1rem;
    margin-top: -0.2rem;
}

/* ===== 卡片样式 ===== */
.glass-card {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid rgba(255,255,255,0.5);
    margin-bottom: 16px;
    transition: all 0.2s ease;
}
.glass-card:hover {
    box-shadow: 0 6px 30px rgba(0,0,0,0.10);
}

/* ===== 状态徽章 ===== */
.badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.badge-conscious { background: #00c85322; color: #00c853; border: 1px solid #00c85344; }
.badge-stable { background: #2979ff22; color: #2979ff; border: 1px solid #2979ff44; }
.badge-tension { background: #ff910022; color: #ff9100; border: 1px solid #ff910044; }
.badge-fragmented { background: #ff174422; color: #ff1744; border: 1px solid #ff174444; }

/* ===== 按钮美化 ===== */
.stButton > button {
    border-radius: 30px !important;
    padding: 0.5rem 2rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: scale(1.02) !important;
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3) !important;
}
.stButton > button:active {
    transform: scale(0.97) !important;
}

/* ===== 输入框美化 ===== */
.stTextArea textarea {
    border-radius: 12px !important;
    border: 1px solid #e0e0e0 !important;
    transition: all 0.2s ease !important;
}
.stTextArea textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
}

/* ===== 分隔线 ===== */
.custom-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, #667eea44, transparent);
    margin: 24px 0;
    border: none;
}

/* ===== 淡入动画 ===== */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in {
    animation: fadeInUp 0.5s ease-out forwards;
}

/* ===== 深色模式适配 ===== */
.dark-mode .glass-card {
    background: rgba(30,30,30,0.85);
    border-color: rgba(255,255,255,0.08);
}
.dark-mode .stTextArea textarea {
    background: #2d2d2d !important;
    color: #d4d4d4 !important;
    border-color: #444 !important;
}
.dark-mode .gradient-title {
    background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
</style>
""", unsafe_allow_html=True)

# ---------- 深色模式 ----------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "cache" not in st.session_state:
    st.session_state.cache = {}
if "history" not in st.session_state:
    st.session_state.history = []
if "text_input" not in st.session_state:
    st.session_state.text_input = ""

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

if st.session_state.dark_mode:
    st.markdown("""
    <style>
    .stApp { background: #1a1a2e; }
    .glass-card { background: rgba(30,30,50,0.85); border-color: rgba(255,255,255,0.06); }
    .stTextArea textarea, .stFileUploader { background: #2d2d45 !important; color: #d4d4d4 !important; border-color: #444 !important; }
    .st-b7 { background: #2d2d45 !important; }
    .gradient-title { background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .stButton > button { background: #2d2d45 !important; color: #d4d4d4 !important; }
    .stButton > button:hover { background: #3d3d5a !important; }
    .custom-divider { background: linear-gradient(90deg, transparent, #7c3aed44, transparent); }
    </style>
    """, unsafe_allow_html=True)

# ---------- 标题 ----------
col_title, col_theme = st.columns([5, 1])
with col_title:
    st.markdown('<p class="gradient-title">🔍 太初 · 自指诊断</p>', unsafe_allow_html=True)
    st.markdown('<p class="gradient-subtitle">TSRE + TLF 统一集成 v2.1 · 智能认知诊断</p>', unsafe_allow_html=True)
    st.caption(f"⚡ 缓存 {len(st.session_state.cache)} 条 | 📋 历史 {len(st.session_state.history)} 条")
with col_theme:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🌙" if not st.session_state.dark_mode else "☀️", use_container_width=True):
        toggle_theme()

# ---------- 快速示例（美化按钮） ----------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("**📌 快速示例** — 点击填充测试文本")
cols = st.columns(4)
if cols[0].button("⚖️ 稳定", use_container_width=True):
    st.session_state.text_input = "太阳是恒星，地球是行星。"
if cols[1].button("⚠️ 张力", use_container_width=True):
    st.session_state.text_input = "太阳是恒星，太阳不是恒星。苹果是水果。"
if cols[2].button("🧩 碎片", use_container_width=True):
    st.session_state.text_input = "这个句子包含五个词。苹果是动物。"
if cols[3].button("🧠 认知", use_container_width=True):
    st.session_state.text_input = "我思故我在。思维是存在的本质，存在通过思维被确认。思维与存在的同一性在此达成闭合。"
st.markdown('</div>', unsafe_allow_html=True)

# ---------- 输入区域 ----------
col_input, col_upload = st.columns([3, 1])
with col_input:
    text_input = st.text_area(
        "📝 输入文本",
        height=200,
        key="text_input",
        placeholder="支持多段落文本...\n\n💡 按 Ctrl+Enter 快速诊断"
    )
with col_upload:
    st.markdown('<div class="glass-card" style="padding:16px;">', unsafe_allow_html=True)
    st.markdown("### 📤 上传文件")
    uploaded = st.file_uploader("支持 .txt / .docx / .pdf", type=["txt","docx","pdf"])
    if uploaded:
        try:
            content = uploaded.read()
            if uploaded.type == "text/plain":
                text_input = content.decode("utf-8", errors="ignore")
            elif uploaded.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" and HAS_DOCX:
                from docx import Document
                doc = Document(io.BytesIO(content))
                text_input = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            elif uploaded.type == "application/pdf" and HAS_PDF:
                import PyPDF2
                pdf = PyPDF2.PdfReader(io.BytesIO(content))
                text_input = "\n".join([page.extract_text() or "" for page in pdf.pages])
            else:
                st.warning("⚠️ 文件格式不支持或缺少依赖库")
            st.session_state.text_input = text_input
            st.success(f"✅ 已加载 {len(text_input)} 字符")
        except Exception as e:
            st.error(f"❌ 读取失败：{str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

col_cnt, col_clr = st.columns([6, 1])
with col_cnt:
    st.caption(f"📏 字数：{len(text_input)} 字符")
with col_clr:
    if st.button("🗑️ 清空", use_container_width=True):
        st.session_state.text_input = ""
        st.rerun()

# ---------- Ctrl+Enter ----------
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        var btns = document.querySelectorAll('button');
        for (var btn of btns) {
            if (btn.innerText.includes('开始诊断')) {
                btn.click(); e.preventDefault(); break;
            }
        }
    }
});
</script>
""", unsafe_allow_html=True)

# ---------- 诊断按钮 ----------
if st.button("🚀 开始诊断", use_container_width=True):
    if not text_input.strip():
        st.warning("⚠️ 请输入文本或上传文件")
    else:
        try:
            text_hash = hashlib.md5(text_input.encode()).hexdigest()
            if text_hash in st.session_state.cache:
                result = st.session_state.cache[text_hash]
                st.info("⚡ 从缓存加载结果（文本未变化）")
                cached = True
            else:
                cached = False
                progress = st.progress(0)
                status_text = st.empty()
                status_text.text("⏳ 计算自指分数..."); time.sleep(0.2); progress.progress(25)
                result = analyze(text_input); time.sleep(0.2); progress.progress(50)
                status_text.text("⏳ 多维度评分..."); time.sleep(0.2); progress.progress(75)
                status_text.text("⏳ 生成报告..."); time.sleep(0.2); progress.progress(100)
                status_text.text("✅ 诊断完成")
                time.sleep(0.3)
                status_text.empty()
                progress.empty()
                st.session_state.cache[text_hash] = result
                if len(st.session_state.cache) > 100:
                    st.session_state.cache.pop(next(iter(st.session_state.cache)))

            # ---------- 结果展示（淡入卡片） ----------
            st.markdown('<div class="fade-in">', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:0.8rem; color:#888;">TSRE 自指分数</div>
                    <div style="font-size:2rem; font-weight:700;">{result['tsre']['score']:.4f}</div>
                    <div style="font-size:0.9rem; color:#666;">{result['tsre']['level']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                conflict_count = result['tlf']['conflict_count']
                color = "#00c853" if conflict_count == 0 else "#ff9100" if conflict_count <= 2 else "#ff1744"
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:0.8rem; color:#888;">TLF 逻辑冲突</div>
                    <div style="font-size:2rem; font-weight:700; color:{color};">{conflict_count}</div>
                    <div style="font-size:0.9rem; color:#666;">{'✅ 无冲突' if conflict_count == 0 else '⚠️ 需关注'}</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                status_val = result['summary']['overall_status']
                color = "#00c853" if "✅" in status_val else "#ff1744"
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:0.8rem; color:#888;">整体状态</div>
                    <div style="font-size:1.6rem; font-weight:700; color:{color};">{status_val}</div>
                    <div style="font-size:0.9rem; color:#666;">{'通过' if '✅' in status_val else '需修正'}</div>
                </div>
                """, unsafe_allow_html=True)

            # ---------- 多维度评分 ----------
            ms = result.get('multi_scores', {})
            if ms:
                st.markdown("---")
                st.markdown("#### 📊 多维度评分")
                cols = st.columns(3)
                labels = [("逻辑密度", "logic_density"), ("结构复杂度", "structure_complexity"), ("语义连贯性", "semantic_coherence")]
                for i, (label, key) in enumerate(labels):
                    val = ms.get(key, 0)
                    color = "#00c853" if val >= 0.7 else "#ff9100" if val >= 0.4 else "#ff1744"
                    with cols[i]:
                        st.markdown(f"""
                        <div class="glass-card" style="text-align:center; padding:12px;">
                            <div style="font-size:0.8rem; color:#888;">{label}</div>
                            <div style="font-size:1.8rem; font-weight:700; color:{color};">{val:.2f}</div>
                            <div style="font-size:0.8rem; color:#666;">{'高' if val >= 0.7 else '中' if val >= 0.4 else '低'}</div>
                        </div>
                        """, unsafe_allow_html=True)

            # ---------- 状态卡片 ----------
            gs = result.get('global_state')
            if gs:
                status = gs['status']
                labels = {"CONSCIOUS":["🧠 认知状态","#00c853"], "STABLE":["⚖️ 稳定状态","#2979ff"],
                          "TENSION":["⚠️ 张力状态","#ff9100"], "FRAGMENTED":["🧩 碎片状态","#ff1744"]}
                label, color = labels.get(status, ["未知状态","#888"])
                st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid {color};">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:600; font-size:1.1rem; color:{color};">{label}</span>
                        <span class="badge badge-{status.lower()}">{status}</span>
                    </div>
                    <div style="margin-top:8px; color:#666;">{gs['event'].get('message', '')}</div>
                    <div style="font-size:0.85rem; color:#888; margin-top:4px;">建议操作：{gs['event'].get('action', '无')}</div>
                </div>
                """, unsafe_allow_html=True)

            # ---------- 高亮 ----------
            st.markdown("---")
            st.markdown("#### 🔍 高亮冲突句子")
            highlighted = result.get('highlighted_text', text_input)
            st.markdown(f"""
            <div class="glass-card" style="font-size:1rem; line-height:1.8;">
                {highlighted}
            </div>
            """, unsafe_allow_html=True)

            # ---------- 冲突详情 ----------
            st.markdown("#### 📋 冲突详情")
            if result['tlf']['conflicts']:
                st.error("❌ 检测到以下冲突：")
                for c in result['tlf']['conflicts']:
                    st.write(f"- {c}")
            else:
                st.success("✅ 未检测到逻辑冲突")

            # ---------- 修正建议 ----------
            fix_suggestions = result.get('fix_suggestions', [])
            if fix_suggestions:
                st.markdown("#### 🛠️ 自动修正建议")
                for s in fix_suggestions:
                    st.info(s)

            # ---------- 导出 ----------
            if result['summary']['suggestions']:
                st.info("💡 综合优化建议：")
                for s in result['summary']['suggestions']:
                    st.write(f"- {s}")

            report = f"""# 太初·深度诊断报告
时间：{gs.get('timestamp', '未知') if gs else '未知'}
TSRE分数：{result['tsre']['score']:.4f}
TLF冲突数：{result['tlf']['conflict_count']}
多维度评分：{ms}
冲突列表：{chr(10).join(['- '+c for c in result['tlf']['conflicts']]) if result['tlf']['conflicts'] else '无'}
修正建议：{chr(10).join(['- '+s for s in fix_suggestions]) if fix_suggestions else '无'}
"""
            st.download_button("📄 导出报告", data=report, file_name=f"taichu_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", mime="text/markdown")

            st.markdown('</div>', unsafe_allow_html=True)

            # ---------- 历史 ----------
            summary = text_input[:30] + "..." if len(text_input)>30 else text_input
            st.session_state.history.insert(0, {
                "text": summary,
                "status": result['summary']['overall_status'],
                "tsre": result['tsre']['score'],
                "conflicts": result['tlf']['conflict_count']
            })
            if len(st.session_state.history) > 5:
                st.session_state.history.pop()

        except Exception as e:
            logging.error(traceback.format_exc())
            st.error(f"❌ 诊断出错：{str(e)}")

# ---------- 侧边栏 ----------
with st.sidebar:
    st.markdown("### 📜 历史记录")
    if st.session_state.history:
        for idx, record in enumerate(st.session_state.history):
            st.markdown(f"""
            <div style="padding:8px 12px; border-radius:8px; background:rgba(0,0,0,0.03); margin-bottom:8px;">
                <div style="font-weight:500; font-size:0.9rem;">{record['text']}</div>
                <div style="font-size:0.75rem; color:#888;">{record['status']} · TSRE {record['tsre']:.2f} · 冲突 {record['conflicts']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("暂无诊断记录")

    st.divider()
    st.caption(f"⚡ 缓存：{len(st.session_state.cache)} 条")
    if st.button("🗑️ 清空缓存", use_container_width=True):
        st.session_state.cache = {}
        st.rerun()

st.divider()
st.caption("太初架构 v2.1 | MIT License | 错误日志：taichu_error.log")
