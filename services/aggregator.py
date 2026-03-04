def compute_stats(records):
    total = len(records)

    positive = sum(1 for r in records if r["sentiment_label"] == "POSITIVE")
    negative = sum(1 for r in records if r["sentiment_label"] == "NEGATIVE")
    neutral = total - positive - negative

    return {
        "total_comments": total,
        "positive_count": positive,
        "negative_count": negative,
        "neutral_count": neutral,
        "positive_percent": round((positive / total) * 100, 2) if total else 0,
        "negative_percent": round((negative / total) * 100, 2) if total else 0,
        "neutral_percent": round((neutral / total) * 100, 2) if total else 0,
    }