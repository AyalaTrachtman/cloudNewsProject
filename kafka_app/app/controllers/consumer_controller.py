from kafka import KafkaConsumer
import json
import queue
import time
from kafka_app.app.views.terminal_view import TerminalView  # ✅ נוספה השורה הזו

# --- הגדרת קטגוריות ---
CATEGORIES = ["Politics", "Finance", "Science", "Culture", "Sport", "Technology", "Health", "World"]

news_queues = {cat: queue.Queue() for cat in CATEGORIES}

KAFKA_BROKER = "localhost:9092"

consumer = KafkaConsumer(
    *CATEGORIES,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',  # מתחיל מהודעות ראשונות
    enable_auto_commit=True,
    group_id='news_consumer_group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

total_count = 0
no_new_data_seconds = 0  # סופר כמה זמן עבר בלי הודעות חדשות
check_interval = 1       # poll כל שנייה
max_no_new_data = 5      # מפסיק אחרי 5 שניות בלי הודעות חדשות

while True:
    records = consumer.poll(timeout_ms=1000)  # מושך הודעות זמינות
    if records:
        no_new_data_seconds = 0
        for tp, messages in records.items():
            for message in messages:
                data = message.value
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
                total_count += 1

                # ✅ משתמשים ב־TerminalView להציג כל כתבה שנקלטה
                TerminalView.show_consumer_event(topic_name, news_item.title)
    else:
        no_new_data_seconds += check_interval

    if no_new_data_seconds >= max_no_new_data:
        break

consumer.close()
TerminalView.show_message(f"📰 Total articles processed: {total_count}")  # ✅ שימוש ב־TerminalView