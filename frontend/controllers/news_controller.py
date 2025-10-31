import gradio as gr
import threading
import time
import sys
import os
import queue
import json
from kafka import KafkaConsumer
from datetime import datetime
from cloudNewsProject.kafka_app.app.controllers.producer_controller import send_existing_documents

CATEGORIES = ["Politics", "Finance", "Science", "Culture", "Sport", "Technology", "Health", "World"]
# --- Colors per category ---
CATEGORY_COLORS = {
    "Politics": "#FF5733",
    "Finance": "#33B5FF",
    "Science": "#8D33FF",
    "Culture": "#FF33A8",
    "Sport": "#33FF57",
    "Technology": "#FFC300",
    "Health": "#33FFF0",
    "World": "#AAAAAA"
}
# --- Queue per category ---
news_queues = {cat: queue.Queue() for cat in CATEGORIES}
news_by_category = {cat: [] for cat in CATEGORIES}

# --- Kafka setup ---
KAFKA_BROKER = "localhost:9092"
consumer = KafkaConsumer(
    *CATEGORIES,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    group_id='news_consumer_test',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)
def start_consumer():
    print(f"[Consumer] Listening to topics: {', '.join(CATEGORIES)}")
    for message in consumer:
        data = message.value
        news_item = type("NewsItem", (), {})()
        news_item.title = data.get("title", "")
        news_item.description = data.get("content", "")
        news_item.image_url = data.get("image_url", "")
        news_item.link = data.get("url", "")
        news_item.published_at = data.get("published_at", "Unknown date")
        topic_name = message.topic
        category = topic_name if topic_name in news_queues else data.get("classification", "World")
        if category not in news_queues:
            category = "World"

        news_item.category = category
        news_queues[category].put(news_item)
        print(f"[Consumer] Received: {news_item.title} (Topic: {message.topic}, Category: {category})")

def update_news():
 seen_urls = set()  # נשמור אילו כתבות כבר נוספו
 while True:
    for cat in CATEGORIES:
        while not news_queues[cat].empty():
            news_item = news_queues[cat].get()
            # בדיקה אם כבר ראינו את הכתבה ולוודא שיש לה URL תקין
            if getattr(news_item, "link", None) and news_item.link not in seen_urls:
                news_by_category[cat].append(news_item)
                seen_urls.add(news_item.link)

                # מיון לפי תאריך – הכי חדש ראשון
                news_by_category[cat].sort(
                    key=lambda x: datetime.fromisoformat(
                        getattr(x, "published_at", "1970-01-01").replace("Z", "+00:00")
                    ),
                    reverse=True
                )
    time.sleep(0.5)


threading.Thread(target=start_consumer, daemon=True).start()
threading.Thread(target=update_news, daemon=True).start()