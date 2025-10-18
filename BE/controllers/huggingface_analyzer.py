from transformers import pipeline

# מודלים מוכנים של Hugging Face
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
ner = pipeline("ner", grouped_entities=True, model="dslim/bert-base-NER")

def analyze_article(title: str, content: str):
    """
    מפעיל ניתוח טקסט על כתבה:
    1. סיווג לפי נושא (פוליטיקה, טכנולוגיה, ספורט וכו’)
    2. זיהוי ישויות (שמות, מקומות וכו’)
    """

    text = f"{title}. {content or ''}"

    # נושאים אפשריים
    candidate_labels = ["politics", "technology", "sports", "business", "entertainment", "health"]

    # שלב 1 – סיווג
    classification = classifier(text, candidate_labels)
    top_label = classification["labels"][0]
    confidence = classification["scores"][0]

    # שלב 2 – זיהוי ישויות (NER)
    entities = ner(text)
    named_entities = [
        {"entity": e["entity_group"], "word": e["word"], "score": round(e["score"], 2)}
        for e in entities
    ]

    # נחזיר תוצאה מסודרת
    return {
        "classification": {"label": top_label, "confidence": round(confidence, 2)},
        "entities": named_entities
    }
