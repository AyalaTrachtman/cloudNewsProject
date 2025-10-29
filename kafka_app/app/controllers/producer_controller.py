# app/controllers/producer_controller.py
from firebase_admin import firestore, initialize_app
from kafka import KafkaProducer
from app.models.news_model import NewsItem
import json, queue

# אתחול Firebase
initialize_app()
db = firestore.client()

# הגדרת שרת Kafka
KAFKA_BROKER = "localhost:9092"
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda m: json.dumps(m).encode('utf-8')
)

# 🔹 יצירת תור פנימי לחדשות
news_queue = queue.Queue()

def on_snapshot(col_snapshot, changes, read_time):
    """מאזין לשינויים ב-Firestore ושולח ל-Kafka וגם מוסיף לתור"""
    for change in changes:
        if change.type.name == 'ADDED':
            doc = change.document.to_dict()

            msg = {
                'title': doc.get('title'),
                'description': doc.get('description'),
                'image_url': doc.get('image_url'),
                'tags': doc.get('tags', []),
                'published_at': doc.get('published_at', "Unknown date")
            }

            topic = doc.get('classification', 'World') or 'World'

            producer.send(topic, msg)
            producer.flush()
            news_queue.put(msg)  # 🔹 מוסיף את הכתבה החדשה לתור
            print(f"[Producer] Sent to topic '{topic}': {msg['title']}")

# מאזין בזמן אמת ל-Firestore
col_ref = db.collection('news')
col_ref.on_snapshot(on_snapshot)
