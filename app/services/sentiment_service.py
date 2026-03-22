from collections import Counter


POSITIVE_TERMS = {
    "beat",
    "bullish",
    "surge",
    "gain",
    "upside",
    "growth",
    "upgrade",
    "momentum",
    "record",
    "strong",
}
NEGATIVE_TERMS = {
    "miss",
    "bearish",
    "drop",
    "loss",
    "downgrade",
    "weak",
    "risk",
    "selloff",
    "fall",
    "concern",
}


def score_headlines(headlines: list[dict]) -> dict:
    if not headlines:
        return {"sentiment_score": 0.0, "confidence": 0.0, "headline_count": 0}

    token_counter = Counter()
    polarity = 0.0
    for item in headlines:
        words = [word.strip(".,:;!?").lower() for word in item["headline"].split()]
        token_counter.update(words)
        polarity += sum(1 for word in words if word in POSITIVE_TERMS)
        polarity -= sum(1 for word in words if word in NEGATIVE_TERMS)

    normalized = max(min(polarity / (len(headlines) * 3), 1.0), -1.0)
    confidence = min(0.45 + len(headlines) * 0.1, 0.85)
    return {
        "sentiment_score": round(normalized, 2),
        "confidence": round(confidence, 2),
        "headline_count": len(headlines),
        "token_snapshot": token_counter.most_common(5),
    }
