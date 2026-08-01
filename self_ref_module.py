# self_ref_module.py（第四层增强版）
import re
from datetime import datetime

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

def tlf_check(text: str) -> dict:
    conflicts = []
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
    return {"conflicts": conflicts, "conflict_count": len(conflicts), "is_valid": len(conflicts) == 0}

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

if __name__ == "__main__":
    print("="*60)
    print("太初架构 · 第四层（全局工作空间）测试")
    print("="*60)
    test_texts = ["太阳是恒星，地球是行星。", "太阳是恒星，太阳不是恒星。", "这个句子包含五个词。"]
    for text in test_texts:
        print(f"\n文本：{text}")
        result = analyze(text)
        if result.get("global_state"):
            gs = result["global_state"]
            print(f"  状态：{gs['status']}")
            print(f"  事件：{gs['event'].get('message', '无事件')}")
            print(f"  建议：{result['summary']['suggestions'] if result['summary']['suggestions'] else '无'}")
