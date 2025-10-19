from kafka import KafkaConsumer
import json
import queue
import threading

# Queue עולמית ל-Gradio / שימוש פנימי
news_queue = queue.Queue()

KAFKA_BROKER = "localhost:9092"
TOPIC = "World"  # topic lowercase

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',    # קבלת הודעות ישנות
    enable_auto_commit=False,
   group_id = 'news_consumer_test'  # חדש כדי לקבל את כל ההודעות הישנות
,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

def start_consumer():
    print(f"[Consumer] Listening to topic '{TOPIC}'...")
    for message in consumer:
        data = message.value

        news_item = type("NewsItem", (), {})()
        news_item.title = data.get("title", "")
        news_item.description = data.get("content", "")
        news_item.image_url = data.get("image_url", "")
        classification = data.get("classification", "World")
        news_item.tags = [classification]

        news_queue.put(news_item)
        #print(f"[Consumer] Received from topic '{message.topic}': {news_item.title} (Category: {classification})")

if __name__ == "__main__":
    t = threading.Thread(target=start_consumer, daemon=True)
    t.start()
  #  print("[Test] Consumer thread started. Listening for messages...")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[Test] Stopped by user")
