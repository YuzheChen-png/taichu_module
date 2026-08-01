# self_ref_module.py（含高亮功能）
import re
from datetime import datetime

# ---------- TSRE 核心 ----------
def tsre_score(text: str) -> float:
    if not text.strip():
        return 0.0
    variants = [
        text,
        text[::-1],
        text[:len(text)//2] + text[len(text)//2:][::-1],
        ' '.join(text.split()[::-1]) if len(text.split()) > 1 else text + ' random',
        text + ' ' + text[::-1],
    ]
    def char_vector(s):
        freq = {}
        for ch in s:
            freq[ch] = freq.get(ch, 0) + 1
        common = sorted(freq.items(), key=lambda x: -x[1])[:50]
        vec = [0]*50
        for i, (ch, _) in enumerate(common):
            vec[i] = freq.get(ch, 0)
        return vec
    vectors = [char_vector(s) for s in variants]
    def cosine_sim(a, b):
        dot = sum(x*y for x,y in zip(a,b))
        norm_a = sum(x*x for x in a)**0.5
        norm_b = sum(y*y for y in b)**0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    sims = [cosine_sim(vectors[0], vectors[i]) for i in range(1, len(vectors))]
    if not sims:
        return 0.0
    weights = [1.0, 0.8, 0.6, 0.4]
    weighted = sum(s * w for s, w in zip(sims, weights[:len(sims)]))
    total_weight = sum(weights[:len(sims)])
    raw_score = weighted / total_weight if total_weight > 0 else 0.0
    calibrated = raw_score + 0.15 + (raw_score - 0.5) * 0.08
    return max(0.1, min(0.98, calibrated))

def tsre_diagnose(text: str) -> dict:
    score = tsre_score(text)
    if score >= 0.72:
        level = "高自指（逻辑自洽）"; status = "✅ 良好"
    elif score >= 0.55:
        level = "中自指（存在冗余）"; status = "⚠️ 注意"
    else:
        level = "低自指（结构松散）"; status = "🔴 需修正"
    return {"score": round(score, 4), "level": level, "status": status}

# ---------- TLF 核心 ----------
def tlf_check(text: str) -> dict:
    conflicts = []
    # 原有规则...（此处省略，与之前一致）
    if "是" in text and "不是" in text:
        conflicts.append("存在'是'和'不是'的矛盾")
    if "有" in text and "没有" in text:
        conflicts.append("存在'有'和'没有'的矛盾")
    if "包含" in text:
        parts = text.split("包含")
        if len(parts) == 2:
            a = parts[0].strip()[-5:]; b = parts[1].strip()[:5]
            if a and b and a == b:
                conflicts.append(f"循环依赖：'{a}' 包含自身")
    entities = re.findall(r'[A-Za-z\u4e00-\u9fa5]{2,}', text)
    for ent in set(entities):
        defs = re.findall(rf'{ent}是(\w+)', text) + re.findall(rf'{ent}为(\w+)', text)
        if len(set(defs)) > 1:
            conflicts.append(f"实体'{ent}'定义不一致：{list(set(defs))}")
    # 新增因果/时序倒置检测（简化版）
    if re.search(r'因为.*所以', text) and re.search(r'所以.*因为', text):
        conflicts.append("因果表述冲突（'因为...所以...'与'所以...因为...'并存）")
    if re.search(r'先.*然后', text) and re.search(r'然后.*先', text):
        conflicts.append("时序表述冲突（'先...然后...'与'然后...先...'并存）")
    # 矛盾修辞检测
    if re.search(r'无声的(雷鸣|呐喊|爆炸)', text):
        conflicts.append("矛盾修辞：'无声的雷鸣'等")
    if re.search(r'黑暗的(光芒|阳光)', text):
        conflicts.append("矛盾修辞：'黑暗的光芒'等")
    return {"conflicts": conflicts, "conflict_count": len(conflicts), "is_valid": len(conflicts)==0}

# ---------- 全局状态 ----------
class GlobalState:
    def __init__(self, text, tsre_result, tlf_result):
        self.text = text
        self.tsre = tsre_result
        self.tlf = tlf_result
        self.timestamp = datetime.now().isoformat()
        self.status = self._compute_status()
        self.event = self._trigger_event()

    def _compute_status(self):
        if self.tsre["score"] >= 0.72 and self.tlf["is_valid"]:
            return "CONSCIOUS"
        elif self.tsre["score"] >= 0.55 and self.tlf["is_valid"]:
            return "STABLE"
        elif self.tsre["score"] >= 0.72 and not self.tlf["is_valid"]:
            return "TENSION"
        else:
            return "FRAGMENTED"

    def _trigger_event(self):
        events = {
            "CONSCIOUSNESS": {"level": "info", "message": "系统达到认知状态，逻辑自洽。", "action": "NONE"},
            "STABLE": {"level": "info", "message": "系统处于稳定状态，建议保持。", "action": "NONE"},
            "TENSION": {"level": "warning", "message": "检测到逻辑张力，建议检查冲突。", "action": "REVIEW_CONFLICTS"},
            "FRAGMENTED": {"level": "error", "message": "文本碎片化，建议整合结构。", "action": "RESTRUCTURE"}
        }
        return events.get(self.status, {})

    def to_dict(self):
        return {
            "text": self.text[:60] + "..." if len(self.text)>60 else self.text,
            "tsre_score": self.tsre["score"],
            "tsre_level": self.tsre["level"],
            "tlf_conflicts": self.tlf["conflicts"],
            "status": self.status,
            "event": self.event,
            "timestamp": self.timestamp
        }

# ---------- 高亮生成函数 ----------
def generate_highlighted_text(text: str, conflicts: list) -> str:
    """根据冲突列表，在文本中用红色背景高亮关键词"""
    if not conflicts:
        return text
    # 定义冲突类型到关键词的映射
    keyword_map = {
        "存在'是'和'不是'的矛盾": ["是", "不是"],
        "存在'有'和'没有'的矛盾": ["有", "没有"],
        "循环依赖": ["包含"],
        "实体.*定义不一致": ["是", "为"],
        "因果表述冲突": ["因为", "所以"],
        "时序表述冲突": ["先", "然后"],
        "矛盾修辞": ["无声", "黑暗"],
    }
    highlighted = text
    # 按冲突类型提取关键词并高亮
    for conflict in conflicts:
        for pattern, keywords in keyword_map.items():
            if re.search(pattern, conflict):
                for kw in keywords:
                    # 使用正则替换，避免替换已高亮的部分
                    highlighted = re.sub(rf'(?<!<span[^>]*>){re.escape(kw)}(?!</span>)', 
                                         f'<span style="background-color: #ffcccc; font-weight: bold;">{kw}</span>', 
                                         highlighted)
                break
    return highlighted

# ---------- 统一分析入口 ----------
def analyze(text: str) -> dict:
    if not text.strip():
        return {"error": "文本为空", "tsre": {"score": 0.0, "level": "无效", "status": "❌"}, 
                "tlf": {"conflicts": [], "conflict_count": 0, "is_valid": False}, 
                "global_state": None, "highlighted_text": ""}
    tsre_result = tsre_diagnose(text)
    tlf_result = tlf_check(text)
    gs = GlobalState(text, tsre_result, tlf_result)
    highlighted = generate_highlighted_text(text, tlf_result["conflicts"])
    return {
        "tsre": tsre_result,
        "tlf": tlf_result,
        "global_state": gs.to_dict(),
        "highlighted_text": highlighted,
        "summary": {
            "is_valid": tsre_result["score"] >= 0.55 and tlf_result["is_valid"],
            "suggestions": (["TSRE 自指分数偏低，建议检查逻辑衔接。"] if tsre_result["score"] < 0.55 else []) 
                         + ([f"TLF 冲突：{c}" for c in tlf_result["conflicts"]] if not tlf_result["is_valid"] else []),
            "overall_status": "✅ 通过" if tsre_result["score"] >= 0.55 and tlf_result["is_valid"] else "🔴 需修正"
        }
    }

if __name__ == "__main__":
    # 简单测试
    test = "太阳是恒星，太阳不是恒星。"
    result = analyze(test)
    print(result["highlighted_text"])
