# self_ref_module.py（TLF 规则增强版 v1.2）
import re
from datetime import datetime

# ============================================================
# TSRE 核心（保持不变）
# ============================================================

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

# ============================================================
# TLF 核心（规则增强版 v1.2）
# ============================================================

def tlf_check(text: str) -> dict:
    conflicts = []

    # ----- 规则1：矛盾检测 -----
    if "是" in text and "不是" in text:
        conflicts.append("存在'是'和'不是'的矛盾")
    if "有" in text and "没有" in text:
        conflicts.append("存在'有'和'没有'的矛盾")
    if "存在" in text and "不存在" in text:
        conflicts.append("存在'存在'和'不存在'的矛盾")

    # ----- 规则2：循环检测 -----
    if "包含" in text:
        parts = text.split("包含")
        if len(parts) == 2:
            a = parts[0].strip()[-5:]
            b = parts[1].strip()[:5]
            if a and b and a == b:
                conflicts.append(f"循环依赖：'{a}' 包含自身")

    # ----- 规则3：因果倒置检测 -----
    cause_patterns = [
        (r'因为(.*?)，所以(.*?)', r'因此(.*?)，因为(.*?)'),
        (r'由于(.*?)，导致(.*?)', r'导致(.*?)，由于(.*?)'),
    ]
    for pat1, pat2 in cause_patterns:
        match1 = re.search(pat1, text)
        match2 = re.search(pat2, text)
        if match1 and match2:
            # 如果同时存在正反两种因果表述，可能表示混淆
            conflicts.append(f"因果表述不一致：'因为...所以...' 与 '因此...因为...' 同时出现")
        elif match2 and not match1:
            # 仅有倒置的因果表述
            conflicts.append(f"可能的因果倒置：{match2.group(0)}")

    # ----- 规则4：时序混乱检测 -----
    time_order = [
        (r'先(.*?)，然后(.*?)', r'然后(.*?)，先(.*?)'),
        (r'首先(.*?)，接着(.*?)', r'接着(.*?)，首先(.*?)'),
    ]
    for pat1, pat2 in time_order:
        match1 = re.search(pat1, text)
        match2 = re.search(pat2, text)
        if match2 and not match1:
            conflicts.append(f"可能的时序倒置：{match2.group(0)}")

    # ----- 规则5：主谓不一致检测 -----
    subject_predicate_pairs = [
        (r'苹果是(动物|汽车|石头)', "苹果不是动物/汽车/石头"),
        (r'太阳是(行星|卫星|彗星)', "太阳是恒星，不是行星/卫星/彗星"),
        (r'月亮是(恒星|行星|彗星)', "月亮是卫星，不是恒星/行星/彗星"),
    ]
    for pattern, message in subject_predicate_pairs:
        if re.search(pattern, text):
            conflicts.append(f"主谓不一致：{message}")

    # ----- 规则6：量词逻辑冲突 -----
    if "所有" in text and "没有" in text:
        # 粗略检测：如果同时出现"所有..."和"没有..."，可能表示冲突
        all_match = re.search(r'所有(.*?)[，。]', text)
        none_match = re.search(r'没有(.*?)[，。]', text)
        if all_match and none_match and all_match.group(1) == none_match.group(1):
            conflicts.append(f"量词冲突：'所有{all_match.group(1)}' 与 '没有{none_match.group(1)}' 同时出现")

    # ----- 规则7：矛盾修辞检测（简化版） -----
    oxymorons = [
        (r'无声的(雷鸣|呐喊|爆炸)', "矛盾修辞：无声的雷鸣"),
        (r'黑暗的(光芒|阳光|灯光)', "矛盾修辞：黑暗的光芒"),
        (r'永恒的(瞬间|刹那)', "矛盾修辞：永恒的瞬间"),
        (r'巨大的(尘埃|微粒|细菌)', "矛盾修辞：巨大的尘埃"),
    ]
    for pattern, message in oxymorons:
        if re.search(pattern, text):
            conflicts.append(message)

    # ----- 规则8：定义不一致（原有规则保留） -----
    entities = re.findall(r'[A-Za-z\u4e00-\u9fa5]{2,}', text)
    for ent in set(entities):
        defs = re.findall(rf'{ent}是(\w+)', text)
        defs += re.findall(rf'{ent}为(\w+)', text)
        if len(set(defs)) > 1:
            conflicts.append(f"实体'{ent}'定义不一致：{list(set(defs))}")

    return {
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
        "is_valid": len(conflicts) == 0
    }

# ============================================================
# 全局状态与认知事件（第四层）
# ============================================================

class GlobalState:
    def __init__(self, text: str, tsre_result: dict, tlf_result: dict):
        self.text = text
        self.tsre = tsre_result
        self.tlf = tlf_result
        self.timestamp = datetime.now().isoformat()
        self.status = self._compute_status()
        self.event = self._trigger_event()

    def _compute_status(self) -> str:
        if self.tsre["score"] >= 0.72 and self.tlf["is_valid"]:
            return "CONSCIOUS"
        elif self.tsre["score"] >= 0.55 and self.tlf["is_valid"]:
            return "STABLE"
        elif self.tsre["score"] >= 0.72 and not self.tlf["is_valid"]:
            return "TENSION"
        else:
            return "FRAGMENTED"

    def _trigger_event(self) -> dict:
        events = {
            "CONSCIOUSNESS": {"level": "info", "message": "系统达到认知状态，逻辑自洽。", "action": "NONE"},
            "STABLE": {"level": "info", "message": "系统处于稳定状态，建议保持。", "action": "NONE"},
            "TENSION": {"level": "warning", "message": "检测到逻辑张力，建议检查冲突。", "action": "REVIEW_CONFLICTS"},
            "FRAGMENTED": {"level": "error", "message": "文本碎片化，建议整合结构。", "action": "RESTRUCTURE"}
        }
        return events.get(self.status, {})

    def to_dict(self) -> dict:
        return {
            "text": self.text[:60] + "..." if len(self.text) > 60 else self.text,
            "tsre_score": self.tsre["score"],
            "tsre_level": self.tsre["level"],
            "tlf_conflicts": self.tlf["conflicts"],
            "status": self.status,
            "event": self.event,
            "timestamp": self.timestamp
        }

# ============================================================
# 统一分析入口
# ============================================================

def analyze(text: str) -> dict:
    if not text.strip():
        return {"error": "文本为空", "tsre": {"score": 0.0, "level": "无效输入", "status": "❌ 错误"}, "tlf": {"conflicts": [], "conflict_count": 0, "is_valid": False}, "global_state": None}
    tsre_result = tsre_diagnose(text)
    tlf_result = tlf_check(text)
    gs = GlobalState(text, tsre_result, tlf_result)
    return {
        "tsre": tsre_result,
        "tlf": tlf_result,
        "global_state": gs.to_dict(),
        "summary": {
            "is_valid": tsre_result["score"] >= 0.55 and tlf_result["is_valid"],
            "suggestions": (["TSRE 自指分数偏低，建议检查逻辑衔接和因果关系。"] if tsre_result["score"] < 0.55 else []) + ([f"TLF 检测到冲突：{c}" for c in tlf_result["conflicts"]] if not tlf_result["is_valid"] else []),
            "overall_status": "✅ 通过" if tsre_result["score"] >= 0.55 and tlf_result["is_valid"] else "🔴 需修正"
        }
    }

# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("太初架构 · TLF 规则增强版 v1.2 测试")
    print("="*60)

    test_texts = [
        "太阳是恒星，地球是行星。",
        "太阳是恒星，太阳不是恒星。",
        "苹果是动物。",
        "因为下雨，所以地面湿了。",
        "因为地面湿了，所以下雨。",
        "他先吃饭，然后起床。",
        "他先起床，然后吃饭。",
        "无声的雷鸣。",
        "所有人都来了，没有人缺席。"
    ]

    for text in test_texts:
        print(f"\n文本：{text}")
        result = analyze(text)
        if result.get("global_state"):
            gs = result["global_state"]
            print(f"  状态：{gs['status']}")
            print(f"  冲突数：{result['tlf']['conflict_count']}")
            if result['tlf']['conflicts']:
                for c in result['tlf']['conflicts']:
                    print(f"    - {c}")
