import gradio as gr
import threading
import time
import sys
import os
import queue
import json
from kafka import KafkaConsumer

# --- Path setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- Categories ---
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

        topic_name = message.topic
        category = topic_name if topic_name in news_queues else data.get("classification", "World")
        if category not in news_queues:
            category = "World"

        news_item.category = category
        news_queues[category].put(news_item)
        print(f"[Consumer] Received: {news_item.title} (Topic: {message.topic}, Category: {category})")

def update_news():
    while True:
        for cat in CATEGORIES:
            while not news_queues[cat].empty():
                news_item = news_queues[cat].get()
                news_by_category[cat].append(news_item)
        time.sleep(0.5)

threading.Thread(target=start_consumer, daemon=True).start()
threading.Thread(target=update_news, daemon=True).start()

# --- CSS ---
css = """
.category-btn-container { display: flex; justify-content: flex-start; align-items: center; overflow-x: auto; white-space: nowrap; padding: 14px 30px; position: fixed; top: 0; left: 0; width: 100%; background-color: #fff; z-index: 1000; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.logo { font-size: 24px; font-weight: bold; margin-right: 20px; }
.category-btn { border: none; padding: 0 4px; margin: 0 2px; border-radius: 12px; font-size: 22px; cursor: pointer; color: white; background-color: #555; flex: 0 0 auto; width: auto; min-width: 0; box-sizing: content-box; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; transition: transform 0.2s, background 0.2s; }
.category-btn:hover { transform: scale(1.05); }

.news-output { margin-top: 80px; padding: 20px; box-sizing: border-box; width: 100%; }

.news-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }

.news-item { border-radius: 12px; background-color: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.08); position: relative; overflow: hidden; transition: box-shadow 0.2s; }
.news-item:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.2); }

.news-item img { width: 100%; height: calc(100% - 170px); object-fit: cover; display: block; margin: 0; transition: transform 0.3s ease; }
.news-item:hover img { transform: scale(1.1); }

.news-item h2, .news-item h4 { margin: 0; padding: 5px 10px; transition: color 0.2s; color: #333; }
.news-item:hover h2, .news-item:hover h4 { color: inherit; }

.news-item p { margin: 0; padding: 0 10px 10px 10px; font-size: 14px; color: #555; line-height: 1.5; }

.main-news { grid-column: span 3; height: 400px; position: relative;}
.main-news img { width: 100%; height: calc(100% - 120px); display: block; margin: 0; transition: transform 0.3s ease; }
.main-news:hover img { transform: scale(1.1); }

.category-label { position: absolute; top: 10px; left: 10px; padding: 4px 8px; border-radius: 6px; color: white; font-size: 12px; font-weight: bold; text-transform: uppercase; z-index: 10; }

/* Hover colors by category */
.news-item:hover .category-label[data-category="Politics"] ~ h2,
.news-item:hover .category-label[data-category="Politics"] ~ h4 { color: #FF5733; }
.news-item:hover .category-label[data-category="Finance"] ~ h2,
.news-item:hover .category-label[data-category="Finance"] ~ h4 { color: #33B5FF; }
.news-item:hover .category-label[data-category="Science"] ~ h2,
.news-item:hover .category-label[data-category="Science"] ~ h4 { color: #8D33FF; }
.news-item:hover .category-label[data-category="Culture"] ~ h2,
.news-item:hover .category-label[data-category="Culture"] ~ h4 { color: #FF33A8; }
.news-item:hover .category-label[data-category="Sport"] ~ h2,
.news-item:hover .category-label[data-category="Sport"] ~ h4 { color: #33FF57; }
.news-item:hover .category-label[data-category="Technology"] ~ h2,
.news-item:hover .category-label[data-category="Technology"] ~ h4 { color: #FFC300; }
.news-item:hover .category-label[data-category="Health"] ~ h2,
.news-item:hover .category-label[data-category="Health"] ~ h4 { color: #33FFF0; }
.news-item:hover .category-label[data-category="World"] ~ h2,
.news-item:hover .category-label[data-category="World"] ~ h4 { color: #AAAAAA; }

@media (max-width: 1024px) { .news-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) { .news-grid { grid-template-columns: 1fr; } .category-btn { padding: 2px 6px; font-size: 10px; margin: 0 2px; } .news-item img { height: 140px; } }
"""

# --- HTML generator ---
def get_news_html(category):
    items = news_by_category.get(category, [])
    if not items:
        return "<p>No news yet...</p>"

    html = ""
    main = items[0]
    cat_color = CATEGORY_COLORS.get(main.category, "#333")

    html += f"<div class='news-item main-news'>"
    if getattr(main, "image_url", None):
        link = getattr(main, "link", "#")
        html += f"""
        <div class='category-label' data-category='{main.category}' style='background-color:{cat_color};'>{main.category}</div>
        <a href='{link}' target='_blank'><img src='{main.image_url}'/></a>
        """
    html += f"<h2>{main.title}</h2><p>{main.description}</p></div>"

    html += "<div class='news-grid'>"
    for item in items[1:]:
        item_cat = getattr(item, "category", "World")
        cat_color = CATEGORY_COLORS.get(item_cat, "#333")
        html += f"<div class='news-item'>"
        if getattr(item, "image_url", None):
            link = getattr(item, "link", "#")
            html += f"""
            <div class='category-label' data-category='{item_cat}' style='background-color:{cat_color};'>{item_cat}</div>
            <a href='{link}' target='_blank'><img src='{item.image_url}'/></a>
            """
        html += f"<h4>{item.title}</h4><p>{item.description}</p></div>"
    html += "</div>"

    return html

# --- Gradio UI ---
with gr.Blocks(css=css) as demo:
    category_buttons = []
    with gr.Row(elem_classes="category-btn-container"):
        gr.HTML("<div class='logo'>MyNews</div>")
        for cat in CATEGORIES:
            btn = gr.Button(value=cat[:6], elem_classes="category-btn", elem_id=cat)
            category_buttons.append((btn, cat))

    news_output = gr.HTML(elem_classes="news-output")

    def on_category_click(cat):
        html = get_news_html(cat)
        js_update = "<script>"
        js_update += f"document.querySelectorAll('.category-btn').forEach(btn => btn.style.backgroundColor='#555');"
        js_update += f"document.getElementById('{cat}').style.backgroundColor='{CATEGORY_COLORS.get(cat)}';"
        js_update += "</script>"
        return html + js_update

    for btn, cat in category_buttons:
        btn.click(fn=lambda c=cat: on_category_click(c), inputs=[], outputs=[news_output])

demo.launch(inbrowser=True)