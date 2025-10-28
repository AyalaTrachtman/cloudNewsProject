# app/controllers/consumer_controller.py
from kafka_app import KafkaConsumer
from app.models.news_model import NewsItem
import json
from queue import Queue

# Queue שמכיל הודעות חדשות מ-Kafka
news_queue = Queue()

KAFKA_BROKER = "localhost:9092"
TOPIC = "news"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    group_id='gradio-consumer',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

def start_consumer():
    """ריצה ברקע של Consumer שממלא את ה-Queue"""
    import threading
    def consume():
        for message in consumer:
            data = message.value
            news_item = NewsItem(
                title=data['title'],
                description=data['description'],
                image_url=data['image_url'],
                tags=data.get('tags', []),
                published_at=data.get('published_at', "Unknown date")
            )
            news_queue.put(news_item)
            print(f"[Consumer] Received: {news_item.title}")

    t = threading.Thread(target=consume, daemon=True)
    t.start()
