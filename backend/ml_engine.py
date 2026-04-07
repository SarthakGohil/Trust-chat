import re

EMOJI = {
    "joy": {"😀", "😄", "😁", "😊", "😍", "😂", "🤣", "❤", "❤️", "✨", "👍"},
    "anger": {"😡", "🤬", "😠", "👎"},
    "fear": {"😨", "😰", "😱"},
    "sadness": {"😢", "😭", "☹", "🙁"},
    "surprise": {"😲", "😮", "🤯"},
}

KW = {
    "joy": {"happy", "great", "awesome", "love", "nice", "good", "amazing", "lol", "haha", "thanks"},
    "anger": {"angry", "mad", "hate", "annoying", "worst", "wtf", "shut", "damn", "sucks"},
    "fear": {"scared", "afraid", "worried", "anxious", "panic", "terrified", "nervous"},
    "sadness": {"sad", "sorry", "miss", "lonely", "tired", "hurt", "cry"},
    "surprise": {"wow", "omg", "really", "seriously", "what", "unexpected", "no way"},
}

POLITE = {"please", "thanks", "thank", "sorry"}
TOXIC = {"idiot", "stupid", "hate", "sucks", "wtf"}

def tokens(text: str):
    return re.findall(r"[a-z']+|\d+", (text or "").lower())

def emotion_label(text: str) -> str:
    raw = text or ""
    tks = tokens(raw)
    scores = {k: 0 for k in ["joy", "anger", "fear", "sadness", "surprise"]}
    for emo, emjs in EMOJI.items():
        if any(e in raw for e in emjs):
            scores[emo] += 2
    for emo, kws in KW.items():
        scores[emo] += sum(1 for w in tks if w in kws)
    scores["surprise"] += min(2, raw.count("!") // 2 + raw.count("?") // 2)
    if sum(scores.values()) == 0:
        return "neutral"
    return max(scores.items(), key=lambda kv: kv[1])[0]

def is_sarcasm(text: str) -> bool:
    raw = (text or "").strip()
    low = raw.lower()
    if "/s" in low or "#sarcasm" in low:
        return True
    if any(p in low for p in ["yeah right", "sure buddy", "as if", "nice one", "great job", "thanks a lot"]):
        return True
    if "..." in raw and any(w in tokens(raw) for w in {"great", "amazing", "love", "nice"}):
        return True
    if raw.count("!") >= 3 and any(w in tokens(raw) for w in {"sure", "ok", "okay"}):
        return True
    return False

def trust_score(text: str, emotion: str, sarcasm: bool) -> int:
    if emotion in {"joy", "neutral"}:
        score = 90
    elif emotion in {"surprise", "sadness"}:
        score = 65
    else:
        score = 35
    tks = set(tokens(text))
    if sarcasm:
        score -= 12
    if tks & POLITE:
        score += 3
    if tks & TOXIC:
        score -= 10
    return max(0, min(100, int(score)))

def analyze(text: str):
    emotion = emotion_label(text)
    sarcasm = is_sarcasm(text)
    score = trust_score(text, emotion, sarcasm)
    return {"emotion": emotion, "trust_score": score, "is_sarcasm": sarcasm}
