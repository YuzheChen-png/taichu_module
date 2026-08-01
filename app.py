import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from self_ref_module import analyze

st.set_page_config(page_title="太初 · 自指诊断系统", page_icon="🔍", layout="wide")
st.title("🔍 太初 · 自指诊断系统")
st.markdown("**TSRE + TLF 统一集成 v1.0** — 同时检测文本的自指程度与逻辑冲突")
text_input = st.text_area("请输入要检测的文本", height=200, placeholder="粘贴你的文本...")
if st.button("🚀 开始诊断"):
    if not text_input.strip():
        st.warning("请输入文本")
    else:
        with st.spinner("分析中..."):
            result = analyze(text_input)
        col1, col2, col3 = st.columns(3)
        col1.metric("TSRE 自指分数", f"{result['tsre']['score']:.4f}", result['tsre']['level'])
        col2.metric("TLF 逻辑冲突", result['tlf']['conflict_count'], "有冲突" if result['tlf']['conflicts'] else "无冲突")
        col3.metric("整体状态", result['summary']['overall_status'])
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
st.divider()
st.caption("太初架构 · 自指模块层 v1.0 | MIT License | 无需安装，仅需浏览器")
