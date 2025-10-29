from kafka import KafkaConsumer
import json
import queue
import threading

# --- קטגוריות ---
CATEGORIES = ["Politics", "Finance", "Science", "Culture", "Sport", "Technology", "Health", "World"]

# --- יצירת תורים נפרדים לכל קטגוריה ---
news_queues = {cat: queue.Queue() for cat in CATEGORIES}

KAFKA_BROKER = "localhost:9092"

# --- יצירת KafkaConsumer ---
consumer = KafkaConsumer(
    *CATEGORIES,  # מאזין לכל הטופיקים
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',  # מאזין רק להודעות חדשות
    enable_auto_commit=True,       # שומר את המיקום האחרון שקרא
    group_id='news_consumer_group',  # מזהה קבוצה ייחודי לצרכן
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

def consume_messages():
    """מאזין להודעות חדשות בלבד ומכניס לתורים הרלוונטיים"""
    print(f"[Consumer] ✅ Listening for NEW messages on topics: {', '.join(CATEGORIES)}")
    for message in consumer:
        data = message.value
        print(f"[Consumer] Raw message received: {data}")

        # יצירת אובייקט כתבה
        news_item = type("NewsItem", (), {})()
        news_item.title = data.get("title", "")
        news_item.description = data.get("content", "")
        news_item.image_url = data.get("image_url", "")
        news_item.link = data.get("url", "")
        news_item.published_at = data.get("published_at", "")

        # קביעת קטגוריה מתוך ה-topic
        topic_name = message.topic
        category = topic_name if topic_name in news_queues else data.get("classification", "World")
        if category not in news_queues:
            category = "World"

        news_queues[category].put(news_item)
        print(f"[Consumer] 📰 New article: {news_item.title} (Topic: {topic_name})")
def clear_news_queues():
    for q in news_queues.values():
        while not q.empty():
            q.get()
    print("[Consumer] 🗑 All news queues cleared")

def start_consumer():
    """מפעיל את הצרכן ברקע (thread)"""
    t = threading.Thread(target=consume_messages, daemon=True)
    t.start()
    print("[Consumer] 🚀 Consumer started and waiting for new messages...")

if _name_ == "_main_":
    clear_news_queues()
    start_consumer()