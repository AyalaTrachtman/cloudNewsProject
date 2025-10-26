import sys
import os
import json
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from firebase_admin import credentials, firestore, initialize_app
from kafka import KafkaProducer
from kafka_app.app.models.message_model import Message

cred_path = os.path.join(os.path.dirname(__file__), '../FireBaseKey.json')
cred = credentials.Certificate(cred_path)

initialize_app(cred)
db = firestore.client()

KAFKA_BROKER = "localhost:9092"
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda m: m.to_json().encode('utf-8')
)

VALID_TOPICS = [
    "Politics", "Finance", "Science", "Culture", "Sport",
    "Technology", "Health", "World"
]

# ✅ נוסיף סט שיזהה אילו כתבות כבר נשלחו
sent_urls = set()

def send_message_to_kafka(doc):
    """שולח מסמך ל-Kafka תוך טיפול ב-topic חוקי"""
    url = doc.get('url')
    if not url:
        return

    # ✅ לא נשלח אם כבר שלחנו כתבה עם אותו URL
    if url in sent_urls:
        print(f"[Producer] Skipping duplicate: {url}")
        return
    sent_urls.add(url)

    msg = Message(
        id=doc.get('id'),
        title=doc.get('title'),
        content=doc.get('content'),
        url=url,
        source=doc.get('source'),
        image_url=doc.get('image_url'),
        classification=doc.get('classification'),
        entities=doc.get('entities', []),
        published_at=doc.get('published_at')
    )

    classification = doc.get('classification')
    if isinstance(classification, dict):
        topic = classification.get('label', 'World')
    else:
        topic = classification or 'World'

    topic = re.sub(r'[^a-zA-Z0-9._-]', '_', str(topic))

    if topic not in VALID_TOPICS:
        print(f"[Producer] ⚠️ Invalid topic '{topic}', using 'World' instead.")
        topic = "World"

    print(f"[Producer] Sending to topic '{topic}' ({type(topic)})")
    producer.send(topic, msg)
    print(f"[Producer] Sent: {msg.title}")

def send_existing_documents():
    """שולח את כל המסמכים הקיימים במסד ל-Kafka"""
    print("[Producer] Sending existing documents to Kafka...")
    docs = db.collection('news').stream()
    for doc in docs:
        send_message_to_kafka(doc.to_dict())

def on_snapshot(col_snapshot, changes, read_time):
    """מאזין לשינויים בזמן אמת ומעביר ל-Kafka"""
    for change in changes:
        if change.type.name == 'ADDED':
            send_message_to_kafka(change.document.to_dict())

send_existing_documents()

col_ref = db.collection('news')
col_ref.on_snapshot(on_snapshot)

print("[Producer] Listening to Firebase for new documents...")
