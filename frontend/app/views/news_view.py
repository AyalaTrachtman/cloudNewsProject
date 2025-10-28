import gradio as gr
import threading
import time
import sys
import os
import queue
import json

# --- מוסיף את תיקיית הפרויקט הראשית ל-Python path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- ייבוא הקונסומר החדש ---
from cloudNewsProject.kafka_app.consumer_controller import start_consumer  # או הנתיב הנכון אצלך

# --- Queue עולמית לעדכון חדשות ---
news_queue = queue.Queue()

# --- פונקציה שתופעל כשמגיעה כתבה חדשה ---
def on_new_news_id(news_id):
    print(f"[GRADIO] New news ID arrived: {news_id}")
    # כאן אפשר לקרוא ל-Firebase לפי ה-ID ולרענן את התצוגה
    # לדוגמה:
    # news_data = firebase_get_news_by_id(news_id)
    # news_queue.put(news_data)

# --- הפעלת הצרכן ברקע ---
threading.Thread(target=start_consumer, args=(on_new_news_id,), daemon=True).start()

# --- שאר הקוד שלך נשאר בדיוק אותו דבר ---
CATEGORIES = ["Politics", "Finance", "Science", "Culture", "Sport", "Technology", "Health", "World"]
news_by_category = {cat: [] for cat in CATEGORIES}

def update_news():
    while True:
        while not news_queue.empty():
            news_item = news_queue.get()
            category = getattr(news_item, "tags", ["World"])[0]
            if category not in news_by_category:
                news_by_category[category] = []
            news_by_category[category].append(news_item)
        time.sleep(0.5)

threading.Thread(target=update_news, daemon=True).start()

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

with gr.Blocks() as demo:
    with gr.Row():
        category_buttons = []
        for cat in CATEGORIES:
            btn = gr.Button(cat)
            category_buttons.append(btn)
        news_output = gr.Markdown()
        for btn, cat in zip(category_buttons, CATEGORIES):
            btn.click(fn=lambda c=cat: get_news_for_category(c), inputs=[], outputs=[news_output])

demo.launch(inbrowser=True)
