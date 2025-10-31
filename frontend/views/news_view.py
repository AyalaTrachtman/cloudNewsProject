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
from cloudNewsProject.frontend.controllers.news_controller import (
    start_consumer,
    update_news,
    news_by_category,
    news_queues,
    CATEGORIES,
    CATEGORY_COLORS
)
from cloudNewsProject.frontend.models.news_models import format_date
LOGO_URL = "https://res.cloudinary.com/dvzpm0jir/image/upload/v1761764104/%D7%AA%D7%9E%D7%95%D7%A0%D7%94_%D7%A9%D7%9C_WhatsApp_2025-10-29_%D7%91%D7%A9%D7%A2%D7%94_20.47.33_4cdcbad6_iur3fx.jpg"

# --- Path setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.append(project_root)
# --- CSS מעודכן ---
css = """
body, .gradio-container {
    background-color: #fffaf0  !important;  /* רקע בז' רך */
}

.category-btn-container {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    overflow-x: auto;
    padding: 6px 15px;        /* מספיק מקום לשמות מלאים */
    flex: 0 0 auto;           /* למנוע מהכפתורים להתכווץ */
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    background-color: rgba(255, 255, 255, 0.5);
    z-index: 1000;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.logo { 
    font-size: 24px; 
    font-weight: bold; 
    margin-right: 20px; 
}

.category-btn {
    border: none;
    padding: 0 10px;
    margin: 0 2px;
    border-radius: 12px;
    font-size: 22px;
    cursor: pointer;
    color: #333;
    background-color: transparent;
    flex: 0 0 auto;
    width: auto;
    min-width: 0;
    box-sizing: content-box;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    transition: transform 0.2s, background 0.2s, color 0.2s;
}

.category-btn:hover { 
    transform: scale(1.05); 
    background-color: #aaa; 
    color: white; 
}

.news-output { 
    margin-top: 20px; 
    padding: 20px; 
    box-sizing: border-box; 
    width: 100%; 
}

.news-grid { 
    display: grid; 
    grid-template-columns: repeat(3, 1fr); 
    gap: 20px; 
}

.news-item {
    display: flex;             /* מאפשר סידור תוכן מלמעלה למטה */
    flex-direction: column;    /* תוכן מהכותרת עד התאריך */
    border-radius: 12px;
    background-color: #fff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.2s;
}


.news-item:hover { 
    box-shadow: 0 4px 15px rgba(0,0,0,0.2); 
}

.img-container { 
    width: 100%; 
    height: 200px; 
    overflow: hidden; 
}

.img-container img { 
    width: 100%; 
    height: 100%; 
    object-fit: cover; 
    transition: transform 0.5s ease; 
}

.news-item:hover .img-container img { 
    transform: scale(1.1); 
}

.news-item h2, 
.news-item h4 { 
    margin: 0; 
    padding: 5px 10px; 
    transition: color 0.2s; 
    color: #333; 
}

.news-item:hover h2, 
.news-item:hover h4 { 
    color: inherit; 
}

.news-item p { 
    margin: 0; 
    padding: 0 10px 10px 10px; 
    font-size: 14px; 
    color: #555; 
    line-height: 1.5; 
}

/* --- כתבה גדולה --- */
.main-news {
    grid-column: span 3;
    height: 350px;
    position: relative;
    margin-bottom: 30px;
    overflow: hidden;
    border-radius: 12px;
}

.main-news .img-container {
    width: 100%;
    height: 100%;
    overflow: hidden;
}

.main-news .img-container img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.5s ease;
}

.main-news:hover .img-container img {
    transform: scale(1.1);
}

/* Overlay עבור כותרת ותקציר */
.main-news .overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    padding: 20px;
    background: linear-gradient(to top, rgba(0,0,0,0.7), rgba(0,0,0,0));
    color: white;
    box-sizing: border-box;
}

.main-news .overlay h2 {
    font-size: 35px;
    font-weight: 1600;
    margin: 0 0 10px 0;
}

.main-news .overlay p {
    font-size: 16px;
    margin: 0;
}

.main-news .overlay h2,
.main-news .overlay p {
    color: white;
}

.main-news:hover .overlay h2,
.main-news:hover .overlay p {
    color: inherit;
}

/* --- תווית קטגוריה --- */
.category-label {
    position: absolute;
    top: 10px;
    left: 10px;
    padding: 4px 8px;
    border-radius: 6px;
    color: white;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
    z-index: 10;
} 
/* --- תווית קטגוריה בכתבה הגדולה --- */
.main-news .category-label {
    top: 2px;           /* מזיז את התווית יותר למעלה */
    left: 25px;
    padding: 4px 8px;
    border-radius: 6px;
    color: white;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
    z-index: 10;
}


/* --- תאריך בתחתית הכתבה הקטנה --- */
.news-item:not(.main-news) {
    display: flex;
    flex-direction: column;    /* תוכן מהכותרת עד התאריך */
    justify-content: space-between; /* דוחף את התאריך למטה */
    height: 100%;             /* חשוב כדי שהדחיפה תעבוד */
}

.news-item:not(.main-news) .news-footer {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    font-size: 12px;
    color: #777;
    margin: 0 10px 5px 10px;  /* שוליים עליונים ותחתי + שמאל וימין */
    padding: 2px 0 0 0;       /* מרים קצת את השורה למעלה */
    box-shadow: none;
    flex-wrap: nowrap;
}

/* פס דק כמעט לאורך כל הכתבה, עם רווח קטן מכל צד */
.news-item:not(.main-news) .news-footer span {
    display: inline-block;
    border-top: 1px solid rgba(0, 0, 0, 0.10); /* פס כמעט בלתי נראה */
    width: calc(100% - 20px);                  /* פס כמעט לכל הרוחב, 10px מכל צד */
    margin: 0 5px 0 10px;                     /* רווחים מכל צד */
    padding-top: 0;                             /* אין רווח מעל */
}

/* אייקון בתאריך */
.news-item:not(.main-news) .news-footer img {
    width: 14px;
    height: 14px;
    margin-right: 3px;
    opacity: 0.7;
    flex-shrink: 0;
}


/* --- תאריך בכתבה הגדולה --- */
.main-news .news-footer {
    border-top: none;
    box-shadow: none;
    padding-top: 6px;
    font-size: 14px;
    color: #777 !important;      /* צבע אפור */
    justify-content: flex-start;
    display: flex;
    align-items: center;
    flex-wrap: nowrap;            /* שורה אחת */
}

/* אייקון בתאריך בכתבה הגדולה */
.main-news .news-footer img {
    width: 16px;
    height: 16px;
    margin-right: 6px;
    opacity: 1;
    filter: none;                 /* לא להפוך ללבן */
    flex-shrink: 0;
}

/* תאריך עצמו */
.news-footer span {
    color: inherit;               /* לוקח את צבע ההורה */
    margin-left: 4px;             /* רווח בין האייקון לתאריך */
    white-space: nowrap;          /* כדי שלא ירד שורה */
}
/* תאריך עצמו בכתבה הגדולה */
.main-news .news-footer span {
    color: white !important;  /* FORCE צבע לבן */
    margin-left: 4px;
    white-space: nowrap;
}


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

@media (max-width: 1024px) {
    .news-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
    .news-grid { grid-template-columns: 1fr; }
    .category-btn { padding: 2px 6px; font-size: 10px; margin: 0 2px; }
    .img-container { height: 140px; }
    .main-news { height: 250px; }
}

"""


# --- HTML generator מעודכן ---
def get_news_html(category):
    items = news_by_category.get(category, [])
    if not items:
        return "<p>No news yet...</p>"

    html = ""
    main = items[0]
    cat_color = CATEGORY_COLORS.get(main.category, "#333")
    clock_icon = "https://img.icons8.com/ios-filled/50/ffffff/clock.png"  # לכתבה הגדולה
    small_clock_icon = "https://img.icons8.com/ios-filled/50/777777/clock.png"  # לשאר הכתבות

    # --- כתבה גדולה ---
    html += f"<div class='news-item main-news'>"
    if getattr(main, "image_url", None):
        link = getattr(main, "link", "#")
        html += f"""
        <div class='img-container'><a href='{link}' target='_blank'><img src='{main.image_url}'/></a></div>
        <div class='overlay'>
            <div class='category-label' data-category='{main.category}' style='background-color:{cat_color};'>{main.category}</div>
            <h2>{main.title}</h2>
            <p>{main.description}</p>
            <div class='news-footer'>
                <img src='{clock_icon}' alt='clock'/>
                <span>{format_date(getattr(main, "published_at", "Unknown date"))}</span>
            </div>
        </div>
        """
    html += "</div>"

    # --- שאר הכתבות ---
    html += "<div class='news-grid'>"
    for item in items[1:]:
        item_cat = getattr(item, "category", "World")
        cat_color = CATEGORY_COLORS.get(item_cat, "#333")
        html += f"<div class='news-item'>"
        if getattr(item, "image_url", None):
            link = getattr(item, "link", "#")
            html += f"""
            <div class='category-label' data-category='{item_cat}' style='background-color:{cat_color};'>{item_cat}</div>
            <div class='img-container'><a href='{link}' target='_blank'><img src='{item.image_url}'/></a></div>
            """
        html += f"""
        <h4>{item.title}</h4>
        <p>{item.description}</p>
        <div class='news-footer'>
            <img src='{small_clock_icon}' alt='clock'/>
             <span>{format_date(getattr(main, "published_at", "Unknown date"))}</span>

        </div>
        </div>
        """
    html += "</div>"

    return html
# --- Producer ברקע ---
def periodic_producer():
    while True:
        try:
            # נשלח כתבות קיימות לקפקא – עם מגבלה כדי למנוע עומס
            send_existing_documents()
            print("[Producer] Sent news batch to Kafka")
        except Exception as e:
            print(f"[Producer] Error: {e}")
        time.sleep(60)  # ריצה כל דקה

# מפעיל Thread ברקע (daemon=True מבטיח שלא יעכב את ה־UI)
threading.Thread(target=periodic_producer, daemon=True).start()


# --- Gradio UI ---
with gr.Blocks(css=css) as demo:
    category_buttons = []
    with gr.Row(elem_classes="category-btn-container"):
        gr.HTML(f"""
            <div style="display:flex; align-items:center; justify-content:flex-start;">
                <img src="{LOGO_URL}" alt="Logo" width="120" height="120" style="object-fit:contain;">
            </div>
        """)
        for cat in CATEGORIES:
            btn = gr.Button(value=cat, elem_classes="category-btn", elem_id=cat)
            category_buttons.append((btn, cat))

    news_output = gr.HTML(elem_classes="news-output")
    current_category = CATEGORIES[0]

    def on_category_click(cat):
        """כשמשתמש לוחץ על קטגוריה – מציג את החדשות הרלוונטיות"""
        global current_category
        current_category = cat
        print(f"[UI] Clicked category: {cat}")
        html = get_news_html(cat)

        # הוספת JS לעדכון צבע הכפתור הנבחר
        js_update = f"""
        <script>
        document.querySelectorAll('.category-btn').forEach(btn => {{
            btn.style.backgroundColor = 'transparent';
            btn.style.color = '#333';
        }});
        const activeBtn = document.getElementById('{cat}');
        if (activeBtn) {{
            activeBtn.style.backgroundColor = '{CATEGORY_COLORS.get(cat, "#aaa")}';
            activeBtn.style.color = 'white';
        }}
        </script>
        """
        return html + js_update

    # תיקון ללולאת הלחצנים (שומר על ה-cat הנכון)
    for btn, cat in category_buttons:
        def make_click_handler(category):
            return lambda: on_category_click(category)
        btn.click(fn=make_click_handler(cat), inputs=[], outputs=[news_output])

    # עדכון אוטומטי כל 5 שניות לפי הקטגוריה הנוכחית
    timer = gr.Timer(value=5, active=True)
    timer.tick(
        fn=lambda: get_news_html(current_category),
        inputs=[],
        outputs=[news_output]
    )

# הפעלת הממשק
demo.launch(inbrowser=True)