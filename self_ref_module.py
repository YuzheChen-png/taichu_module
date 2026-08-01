# self_ref_module.py（完整优化版 v2.0）
import re
from datetime import datetime
from collections import Counter
import hashlib

# ---------- 辅助函数 ----------
def split_sentences(text: str) -> list:
    sents = re.split(r'[。！？；\n]+', text)
    return [s.strip() for s in sents if s.strip()]

def semantic_similarity(s1: str, s2: str) -> float:
    set1 = set(s1); set2 = set(s2)
    if not set1 and not set2: return 1.0
    inter = set1 & set2; union = set1 | set2
    return len(inter) / len(union) if union else 0.0

# ---------- TSRE ----------
def tsre_score(text: str) -> float:
    if not text.strip(): return 0.0
    variants = [
        text, text[::-1],
        text[:len(text)//2] + text[len(text)//2:][::-1],
        ' '.join(text.split()[::-1]) if len(text.split()) > 1 else text + ' random',
        text + ' ' + text[::-1],
    ]
    def char_vector(s):
        freq = {}
        for ch in s: freq[ch] = freq.get(ch, 0) + 1
        common = sorted(freq.items(), key=lambda x: -x[1])[:50]
        vec = [0]*50
        for i, (ch, _) in enumerate(common): vec[i] = freq.get(ch, 0)
        return vec
    vectors = [char_vector(s) for s in variants]
    def cosine_sim(a, b):
        dot = sum(x*y for x,y in zip(a,b))
        na = sum(x*x for x in a)**0.5; nb = sum(y*y for y in b)**0.5
        if na == 0 or nb == 0: return 0.0
        return dot / (na * nb)
    sims = [cosine_sim(vectors[0], vectors[i]) for i in range(1, len(vectors))]
    if not sims: return 0.0
    weights = [1.0, 0.8, 0.6, 0.4]
    weighted = sum(s * w for s, w in zip(sims, weights[:len(sims)]))
    total_weight = sum(weights[:len(sims)])
    raw_score = weighted / total_weight if total_weight > 0 else 0.0
    calibrated = raw_score + 0.15 + (raw_score - 0.5) * 0.08
    return max(0.1, min(0.98, calibrated))

def tsre_diagnose(text: str) -> dict:
    score = tsre_score(text)
    if score >= 0.72: level = "高自指（逻辑自洽）"; status = "✅ 良好"
    elif score >= 0.55: level = "中自指（存在冗余）"; status = "⚠️ 注意"
    else: level = "低自指（结构松散）"; status = "🔴 需修正"
    return {"score": round(score, 4), "level": level, "status": status}

# ---------- TLF ----------
def tlf_check(text: str) -> dict:
    conflicts = []; conflict_details = []
    sentences = split_sentences(text)

    for idx, sent in enumerate(sentences):
        if "是" in sent and "不是" in sent:
            conflicts.append("存在'是'和'不是'的矛盾")
            conflict_details.append({"type": "矛盾", "sentence": sent, "keywords": ["是", "不是"]})
        if "有" in sent and "没有" in sent:
            conflicts.append("存在'有'和'没有'的矛盾")
            conflict_details.append({"type": "矛盾", "sentence": sent, "keywords": ["有", "没有"]})

    if "包含" in text:
        parts = text.split("包含")
        if len(parts) == 2:
            a = parts[0].strip()[-5:]; b = parts[1].strip()[:5]
            if a and b and a == b:
                conflicts.append(f"循环依赖：'{a}' 包含自身")
                conflict_details.append({"type": "循环", "sentence": text, "keywords": ["包含"]})

    entities = re.findall(r'[A-Za-z\u4e00-\u9fa5]{2,}', text)
    for ent in set(entities):
        defs = re.findall(rf'{ent}是(\w+)', text) + re.findall(rf'{ent}为(\w+)', text)
        if len(set(defs)) > 1:
            conflicts.append(f"实体'{ent}'定义不一致：{list(set(defs))}")
            for sent in sentences:
                if ent in sent:
                    conflict_details.append({"type": "定义不一致", "sentence": sent, "keywords": [ent]})
                    break

    cause_patterns = [(r'因为.*所以', '因果'), (r'所以.*因为', '因果'), (r'先.*然后', '时序'), (r'然后.*先', '时序')]
    for pattern, label in cause_patterns:
        if re.search(pattern, text):
            conflicts.append(f"{label}表述冲突")
            for sent in sentences:
                if re.search(pattern, sent):
                    conflict_details.append({"type": label, "sentence": sent, "keywords": [pattern]})
                    break

    oxymoron_patterns = [(r'无声的(雷鸣|呐喊|爆炸)', '无声的雷鸣等'), (r'黑暗的(光芒|阳光)', '黑暗的光芒等')]
    for pat, msg in oxymoron_patterns:
        if re.search(pat, text):
            conflicts.append(f"矛盾修辞：{msg}")
            for sent in sentences:
                if re.search(pat, sent):
                    conflict_details.append({"type": "矛盾修辞", "sentence": sent, "keywords": [pat]})
                    break

    for i in range(len(sentences)):
        for j in range(i+1, len(sentences)):
            sim = semantic_similarity(sentences[i], sentences[j])
            if sim > 0.7:
                if ("是" in sentences[i] and "不是" in sentences[j]) or \
                   ("不是" in sentences[i] and "是" in sentences[j]):
                    conflicts.append("语义相似但存在矛盾表述")
                    conflict_details.append({"type": "语义冲突", "sentence": f"{sentences[i]} ↔ {sentences[j]}", "keywords": ["是", "不是"]})

    return {"conflicts": conflicts, "conflict_count": len(conflicts), "is_valid": len(conflicts)==0, 
            "conflict_details": conflict_details, "sentences": sentences}

# ---------- 多维度评分 ----------
def multi_dimension_score(text: str, tsre_score: float, tlf_result: dict) -> dict:
    sentences = tlf_result.get("sentences", split_sentences(text))
    num_sents = len(sentences)
    if num_sents == 0: return {"logic_density": 0, "structure_complexity": 0, "semantic_coherence": 0}
    conflict_count = tlf_result["conflict_count"]
    logic_density = max(0, 1 - (conflict_count / num_sents))
    avg_len = sum(len(s) for s in sentences) / num_sents
    connectives = ["因为", "所以", "虽然", "但是", "然而", "并且", "而且"]
    conn_count = sum(text.count(c) for c in connectives)
    conn_density = min(conn_count / num_sents, 1.0)
    structure_complexity = 0.3 * min(avg_len/50, 1.0) + 0.7 * conn_density
    if num_sents > 1:
        sims = [semantic_similarity(sentences[i], sentences[i+1]) for i in range(num_sents-1)]
        semantic_coherence = sum(sims) / len(sims)
    else:
        semantic_coherence = 1.0
    return {"logic_density": round(logic_density, 4), "structure_complexity": round(structure_complexity, 4),
            "semantic_coherence": round(semantic_coherence, 4)}

# ---------- 自动修正建议 ----------
def generate_fix_suggestions(conflict_details: list, text: str) -> list:
    suggestions = []
    for detail in conflict_details:
        typ = detail.get("type", ""); sent = detail.get("sentence", "")
        if typ == "矛盾":
            if "是" in sent and "不是" in sent:
                suggestions.append(f"将 '{sent}' 中的'不是'改为'也是' 或删除其中一个相反表述。")
            elif "有" in sent and "没有" in sent:
                suggestions.append(f"将 '{sent}' 中的'没有'改为'还有' 或统一表述。")
        elif typ == "循环": suggestions.append(f"检查 '{sent}' 中的循环依赖，确保定义不指向自身。")
        elif typ == "定义不一致": suggestions.append(f"为实体 '{detail['keywords'][0]}' 统一一个定义。")
        elif typ == "因果" or typ == "时序": suggestions.append(f"修正 '{sent}' 中的因果关系/时序方向。")
        elif typ == "矛盾修辞": suggestions.append(f"替换 '{sent}' 中的矛盾修辞。")
        elif typ == "语义冲突": suggestions.append(f"合并或统一 '{sent}' 中的相似但矛盾的表述。")
    return list(set(suggestions))

# ---------- 全局状态 ----------
class GlobalState:
    def __init__(self, text, tsre_result, tlf_result, multi_scores):
        self.text = text; self.tsre = tsre_result; self.tlf = tlf_result
        self.multi_scores = multi_scores
        self.timestamp = datetime.now().isoformat()
        self.status = self._compute_status()
        self.event = self._trigger_event()
    def _compute_status(self):
        if self.tsre["score"] >= 0.72 and self.tlf["is_valid"]: return "CONSCIOUS"
        elif self.tsre["score"] >= 0.55 and self.tlf["is_valid"]: return "STABLE"
        elif self.tsre["score"] >= 0.72 and not self.tlf["is_valid"]: return "TENSION"
        else: return "FRAGMENTED"
    def _trigger_event(self):
        events = {
            "CONSCIOUSNESS": {"level": "info", "message": "系统达到认知状态，逻辑自洽。", "action": "NONE"},
            "STABLE": {"level": "info", "message": "系统处于稳定状态，建议保持。", "action": "NONE"},
            "TENSION": {"level": "warning", "message": "检测到逻辑张力，建议检查冲突。", "action": "REVIEW_CONFLICTS"},
            "FRAGMENTED": {"level": "error", "message": "文本碎片化，建议整合结构。", "action": "RESTRUCTURE"}
        }
        return events.get(self.status, {})
    def to_dict(self):
        return {"text": self.text[:60] + "..." if len(self.text)>60 else self.text,
                "tsre_score": self.tsre["score"], "tsre_level": self.tsre["level"],
                "tlf_conflicts": self.tlf["conflicts"], "multi_scores": self.multi_scores,
                "status": self.status, "event": self.event, "timestamp": self.timestamp}

# ---------- 高亮生成 ----------
def generate_highlighted_text(text: str, conflict_details: list) -> str:
    if not conflict_details: return text
    highlighted = text
    for detail in conflict_details:
        sent = detail.get("sentence", ""); typ = detail.get("type", "")
        if sent and sent in highlighted:
            tag = f"<span style='background-color: #ffcccc; border-left: 4px solid red; padding: 2px 6px;' title='{typ}'>{sent}</span>"
            highlighted = highlighted.replace(sent, tag)
    return highlighted

# ---------- 主入口 ----------
def analyze(text: str) -> dict:
    if not text.strip():
        return {"error": "文本为空", "tsre": {"score": 0.0, "level": "无效", "status": "❌"},
                "tlf": {"conflicts": [], "conflict_count": 0, "is_valid": False, "conflict_details": [], "sentences": []},
                "multi_scores": {}, "global_state": None, "highlighted_text": "", "fix_suggestions": []}
    tsre_result = tsre_diagnose(text)
    tlf_result = tlf_check(text)
    multi_scores = multi_dimension_score(text, tsre_result["score"], tlf_result)
    fix_suggestions = generate_fix_suggestions(tlf_result.get("conflict_details", []), text)
    gs = GlobalState(text, tsre_result, tlf_result, multi_scores)
    highlighted = generate_highlighted_text(text, tlf_result.get("conflict_details", []))
    return {
        "tsre": tsre_result, "tlf": tlf_result, "multi_scores": multi_scores,
        "fix_suggestions": fix_suggestions, "global_state": gs.to_dict(),
        "highlighted_text": highlighted,
        "summary": {
            "is_valid": tsre_result["score"] >= 0.55 and tlf_result["is_valid"],
            "suggestions": (["TSRE 自指分数偏低，建议检查逻辑衔接。"] if tsre_result["score"] < 0.55 else [])
                         + ([f"TLF 冲突：{c}" for c in tlf_result["conflicts"]] if not tlf_result["is_valid"] else []),
            "overall_status": "✅ 通过" if tsre_result["score"] >= 0.55 and tlf_result["is_valid"] else "🔴 需修正"
        }
    }
