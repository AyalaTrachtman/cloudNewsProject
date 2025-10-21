from kafka import KafkaConsumer
import json
import queue
import threading

# --- הגדרת קטגוריות ---
CATEGORIES = ["Politics", "Finance", "Science", "Culture", "Sport", "Technology", "Health", "World"]

# --- יצירת תורים נפרדים לכל קטגוריה ---
news_queues = {cat: queue.Queue() for cat in CATEGORIES}

KAFKA_BROKER = "localhost:9092"
TOPIC = "World"  # או כל טופיק שתרצי

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',     # קבלת הודעות מההתחלה
    enable_auto_commit=False,
    group_id='news_consumer_test',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)


def start_consumer():
    print(f"[Consumer] Listening to topic '{TOPIC}'...")
    for message in consumer:
        data = message.value

        # יצירת אובייקט כתבה
        news_item = type("NewsItem", (), {})()
        news_item.title = data.get("title", "")
        news_item.description = data.get("content", "")
        news_item.image_url = data.get("image_url", "")
        classification = data.get("classification", "World")

        # אם הקטגוריה קיימת ברשימה — שלחי לתור שלה
        if classification in news_queues:
            news_queues[classification].put(news_item)
        else:
            # אם קטגוריה לא מוכרת, הכניסי ל-World כברירת מחדל
            news_queues["World"].put(news_item)

        print(f"[Consumer] Received: {news_item.title} (Category: {classification})")


if __name__ == "__main__":
    t = threading.Thread(target=start_consumer, daemon=True)
    t.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[Test] Stopped by user")
