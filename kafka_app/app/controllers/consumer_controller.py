from kafka import KafkaConsumer
import json
import queue
import threading

# --- הגדרת קטגוריות ---
CATEGORIES = ["Politics", "Finance", "Science", "Culture", "Sport", "Technology", "Health", "World"]

# --- יצירת תורים נפרדים לכל קטגוריה ---
news_queues = {cat: queue.Queue() for cat in CATEGORIES}

KAFKA_BROKER = "localhost:9092"

# --- יצירת KafkaConsumer שמאזין לכל 8 הקטגוריות ---
consumer = KafkaConsumer(
    *CATEGORIES,  # מאזין לכל הטופיקים
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',  # קבלת הודעות מההתחלה
    enable_auto_commit=False,
    group_id='news_consumer_test',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

def start_consumer():
    print(f"[Consumer] Listening to topics: {', '.join(CATEGORIES)}")
    for message in consumer:
        data = message.value

        # יצירת אובייקט כתבה
        news_item = type("NewsItem", (), {})()
        news_item.title = data.get("title", "")
        news_item.description = data.get("content", "")
        news_item.image_url = data.get("image_url", "")
        news_item.link = data.get("url", "")

        # קביעת קטגוריה מתוך ה-topic שנשלח בפועל
        topic_name = message.topic
        category = topic_name if topic_name in news_queues else data.get("classification", "World")

        # אם הקטגוריה לא קיימת, נכניס כברירת מחדל ל-"World"
        if category not in news_queues:
            category = "World"

        news_queues[category].put(news_item)
        print(f"[Consumer] Received: {news_item.title} (Topic: {message.topic}, Category: {category})")

if _name_ == "_main_":
    t = threading.Thread(target=start_consumer, daemon=True)
    t.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[Test] Stopped by user")