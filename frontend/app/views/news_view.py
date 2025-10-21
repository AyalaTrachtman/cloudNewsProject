import gradio as gr
import threading
import time
import sys
import os
import queue
import json
from kafka import KafkaConsumer

# --- מוסיף את תיקיית הפרויקט הראשית ל-Python path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- Queue עולמית לעדכון חדשות ---
news_queue = queue.Queue()

# --- Kafka settings ---
KAFKA_BROKER = "localhost:9092"
TOPIC = "World"

# --- Consumer setup ---
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    group_id='news_consumer_test',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

def consume_messages():
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

# --- Start Consumer in background thread ---
threading.Thread(target=consume_messages, daemon=True).start()

# --- Categories & dictionary ---
CATEGORIES = ["Politics", "Finance", "Science", "Culture", "Sport", "Technology", "Health", "World"]
news_by_category = {cat: [] for cat in CATEGORIES}

# --- Thread שמעדכן מילון חדשות מה-queue ---
def update_news():
    while True:
        while not news_queue.empty():
            news_item = news_queue.get()
            category = news_item.tags[0] if news_item.tags else 'World'
            if category not in news_by_category:
                news_by_category[category] = []
            news_by_category[category].append(news_item)
        time.sleep(0.5)

threading.Thread(target=update_news, daemon=True).start()

# --- פונקציה שמייצרת Markdown ל-Gradio ---
def get_news_for_category(category):
    items = news_by_category.get(category, [])
    display = ""
    for n in items[-10:]:
        display += f"### {n.title}\n{n.description}\n"
        if getattr(n, "image_url", None):
            display += f"![image]({n.image_url})\n"
        if getattr(n, "tags", None):
            display += f"Tags: {', '.join(n.tags)}\n\n"
    if not display:
        display = "No news yet..."
    return display

# --- Gradio UI עם שורה של כפתורים לכל קטגוריה ---
with gr.Blocks() as demo:
    with gr.Row():
        category_buttons = []
        for cat in CATEGORIES:
            btn = gr.Button(cat)
            category_buttons.append(btn)
        news_output = gr.Markdown()
        # לחיצה על כל כפתור מעדכנת את החדשות
        for btn, cat in zip(category_buttons, CATEGORIES):
            btn.click(fn=lambda c=cat: get_news_for_category(c), inputs=[], outputs=[news_output])


demo.launch(inbrowser=True)

