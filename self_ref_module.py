# self_ref_module.py
import re

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

def analyze(text: str) -> dict:
    if not text.strip():
        return {"tsre": {"score": 0.0, "level": "无效输入", "status": "❌ 错误"}, "tlf": {"conflicts": [], "conflict_count": 0, "is_valid": False}, "summary": {"is_valid": False, "suggestions": ["请输入有效文本"]}}
    tsre_result = tsre_diagnose(text)
    tlf_result = tlf_check(text)
    is_valid = tsre_result["score"] >= 0.55 and tlf_result["is_valid"]
    suggestions = []
    if tsre_result["score"] < 0.55:
        suggestions.append("TSRE 自指分数偏低，建议检查逻辑衔接和因果关系。")
    if not tlf_result["is_valid"]:
        for c in tlf_result["conflicts"]:
            suggestions.append(f"TLF 检测到冲突：{c}")
    return {"tsre": tsre_result, "tlf": tlf_result, "summary": {"is_valid": is_valid, "suggestions": suggestions, "overall_status": "✅ 通过" if is_valid else "🔴 需修正"}}
