try:
    from .ml_engine import analyze, emotion_label, is_sarcasm, trust_score
except ImportError:
    from ml_engine import analyze, emotion_label, is_sarcasm, trust_score

async def get_emotion(text: str) -> str:
    return emotion_label(text)

async def get_sarcasm(text: str) -> bool:
    return is_sarcasm(text)

async def get_trust_score(text: str) -> int:
    emotion = await get_emotion(text)
    sarcasm = await get_sarcasm(text)
    return trust_score(text, emotion, sarcasm)

async def analyze_message(text: str):
    return analyze(text)
