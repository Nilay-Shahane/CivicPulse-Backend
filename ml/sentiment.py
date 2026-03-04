from transformers import pipeline
import torch

sentiment_model = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    device=0 if torch.cuda.is_available() else -1
)

def analyze_sentiment(text):
    result = sentiment_model(str(text)[:512])[0]
    return {
        "label": result["label"],
        "score": result["score"]
    }

def analyze_batch(records):
    for r in records:
        sentiment = analyze_sentiment(r["translated_comment"])
        r["sentiment_label"] = sentiment["label"]
        r["sentiment_score"] = sentiment["score"]
    return records