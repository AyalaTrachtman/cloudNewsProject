# app/controllers/producer_controller.py
from firebase_admin import firestore, initialize_app
from kafka_app import KafkaProducer
from app.models.news_model import NewsItem
import json

# אתחול Firebase
initialize_app()
db = firestore.client()

# הגדרת שרת Kafka
KAFKA_BROKER = "localhost:9092"
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda m: json.dumps(m).encode('utf-8')
)

def on_snapshot(col_snapshot, changes, read_time):
    """מאזין לשינויים במסד הנתונים (Firestore) ושולח ל-Kafka"""
    for change in changes:
        if change.type.name == 'ADDED':
            doc = change.document.to_dict()

            # בונה אובייקט ל-Kafka
            msg = {
                'title': doc.get('title'),
                'description': doc.get('description'),
                'image_url': doc.get('image_url'),
                'tags': doc.get('tags', []),
                'published_at': doc.get('published_at', "Unknown date") 
            }

            topic = doc.get('classification', 'World') or 'World'

            producer.send(topic, msg)
            producer.flush()  # שולח מייד
            print(f"[Producer] Sent to topic '{topic}': {msg['title']}")

# מאזין בזמן אמת למסד הנתונים
col_ref = db.collection('news')
col_ref.on_snapshot(on_snapshot)
