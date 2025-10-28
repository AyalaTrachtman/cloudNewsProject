from kafka import KafkaConsumer
import json
import queue
import threading

# --- הגדרת קטגוריות ---
CATEGORIES = ["Politics", "Finance", "Science", "Culture", "Sport", "Technology", "Health", "World"]

# --- יצירת תורים נפרדים לכל קטגוריה ---
news_queues = {cat: queue.Queue() for cat in CATEGORIES}

KAFKA_BROKER = "localhost:9092"
TOPIC = "World"  # אפשר לשנות לפי הצורך

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    group_id='news_consumer_test',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)


def start_consumer(on_new_news=None):
    """
    מאזין ל-Kafka ומעביר כל כתבה חדשה לפונקציית callback (אם הוגדרה),
    או פשוט שומר אותה בתור של הקטגוריה.
    """
    print(f"[Consumer] Listening to topic '{TOPIC}'...")

    for message in consumer:
        data = message.value
        print(f"[Consumer] Raw message received: {data}")

        news_id = data.get("id")  # מזהה הכתבה
        title = data.get("title", "")
        classification = data.get("classification", "World")

        # יצירת אובייקט כתבה פשוט
        news_item = type("NewsItem", (), {})()
        news_item.id = news_id
        news_item.title = title
        news_item.description = data.get("content", "")
        news_item.image_url = data.get("image_url", "")

        # הוספה לתור לפי קטגוריה
        if classification in news_queues:
            news_queues[classification].put(news_item)
        else:
            news_queues["World"].put(news_item)

        print(f"[Consumer] Received: {title} (Category: {classification})")

        # אם יש פונקציית callback (למשל מ-Gradio) — לקרוא לה
        if on_new_news and news_id:
            try:
                on_new_news(news_id)
                print(f"[Consumer] Triggered callback for news ID: {news_id}")
            except Exception as e:
                print(f"[Consumer] ⚠️ Error in callback: {e}")


if __name__ == "__main__":
    # מצב בדיקה: רק מדפיס הודעות
    t = threading.Thread(target=start_consumer, daemon=True)
    t.start()

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("Stopped")
