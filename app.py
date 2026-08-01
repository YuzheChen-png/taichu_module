import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from self_ref_module import analyze

st.set_page_config(page_title="太初 · 自指诊断系统", page_icon="🔍", layout="wide")

st.title("🔍 太初 · 自指诊断系统")
st.markdown("**TSRE + TLF 统一集成 v1.1** — 全局工作空间已启用")

text_input = st.text_area("请输入要检测的文本", height=200, placeholder="粘贴你的文本...")

if st.button("🚀 开始诊断"):
    if not text_input.strip():
        st.warning("请输入文本")
    else:
        with st.spinner("分析中..."):
            result = analyze(text_input)

        # ========== 第一行：核心指标 ==========
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("TSRE 自指分数", f"{result['tsre']['score']:.4f}", result['tsre']['level'])
        col2.metric("TLF 逻辑冲突", result['tlf']['conflict_count'], "有冲突" if result['tlf']['conflicts'] else "无冲突")
        col3.metric("整体状态", result['summary']['overall_status'])

        # ========== 全局状态卡片（第四层核心） ==========
        gs = result.get('global_state')
        if gs:
            status = gs['status']
            event = gs['event']
            
            # 状态-颜色-图标映射
            status_map = {
                "CONSCIOUS": {"color": "#00c853", "icon": "🧠", "label": "认知状态"},
                "STABLE": {"color": "#2979ff", "icon": "⚖️", "label": "稳定状态"},
                "TENSION": {"color": "#ff9100", "icon": "⚠️", "label": "张力状态"},
                "FRAGMENTED": {"color": "#ff1744", "icon": "🧩", "label": "碎片状态"}
            }
            info = status_map.get(status, {"color": "#gray", "icon": "❓", "label": "未知"})
            
            # 显示状态卡片
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

        # 显示时间戳（如果有）
        if gs and gs.get('timestamp'):
            st.caption(f"诊断时间：{gs['timestamp']}")

st.divider()
st.caption("太初架构 · 自指模块层 v1.1 | 全局工作空间已启用 | MIT License")
