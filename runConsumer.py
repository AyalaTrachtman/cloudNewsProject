# run_consumer.py
from kafka import KafkaConsumer
import json
import queue
import threading

# Queue עולמית לשמירת הודעות חדשות
news_queue = queue.Queue()

KAFKA_BROKER = "localhost:9092"
TOPIC = "world"

# צור קונסיומר חדש עם group ייחודי כדי לקבל גם הודעות ישנות
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',  # קבלת הודעות ישנות
    enable_auto_commit=False,       # לא לעדכן offsets
    group_id='test_group_1',        # group חדש
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

def start_consumer():
    """מאזין להודעות בקונסיומר ומכניס ל-queue"""
    print(f"[Consumer] Listening to topic '{TOPIC}'...")
    for message in consumer:
        data = message.value

        # אם ההודעה היא string, ננסה להמיר ל-json
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                print("[Consumer] Warning: could not decode JSON, skipping message")
                continue

        # צור אובייקט דינמי לחדשות
        news_item = type("NewsItem", (), {})()
        news_item.title = data.get("title", "")
        news_item.description = data.get("content", "")
        news_item.image_url = data.get("image_url", "")
        classification = data.get("classification", "World")
        if not isinstance(classification, str):
            classification = str(classification)
        news_item.tags = [classification]

        # דחוף ל-queue
        news_queue.put(news_item)
        print(f"[Consumer] Received: {news_item.title} (Category: {classification})")

if __name__ == "__main__":
    # הרץ את הקונסיומר ברקע ב-thread
    t = threading.Thread(target=start_consumer, daemon=True)
    t.start()
    print("[Test] Consumer thread started. Listening for messages...")

    # השאר את התכנית רצה כדי להאזין להודעות
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[Test] Stopped by user")
