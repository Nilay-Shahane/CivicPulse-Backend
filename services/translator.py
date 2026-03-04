import time
from langdetect import detect
from deep_translator import GoogleTranslator
from core.config import MAX_RETRIES

translator_auto = GoogleTranslator(source="auto", target="en")
translator_hi = GoogleTranslator(source="hi", target="en")

def is_hinglish(text):
    hindi_words = ["hai", "nahi", "accha", "acha", "kya", "kyun"]
    t = text.lower()
    return any(word in t for word in hindi_words)

def translate_text(text):
    text = str(text).strip()
    if not text:
        return ""

    for _ in range(MAX_RETRIES):
        try:
            if is_hinglish(text):
                return translator_hi.translate(text)

            lang = detect(text)
            if lang != "en":
                return translator_auto.translate(text)

            return text
        except:
            time.sleep(0.3)

    return text

def translate_batch(records):
    for r in records:
        r["translated_comment"] = translate_text(r["comment"])
    return records