import sys
import os
import json
import re

# מוסיף את תיקיית הפרויקט הראשית ל-Python path כדי למצוא את המודולים המקומיים
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from firebase_admin import credentials, firestore, initialize_app
from kafka import KafkaProducer
from kafka_app.app.models.message_model import Message  # מתאים למבנה שלך

# הנתיב המלא לקובץ JSON של Firebase
cred_path = os.path.join(os.path.dirname(__file__), '../FireBaseKey.json')
cred = credentials.Certificate(cred_path)

# אתחול Firebase
initialize_app(cred)
db = firestore.client()

# הגדרת שרת Kafka
KAFKA_BROKER = "localhost:9092"
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda m: m.to_json().encode('utf-8')
)

def send_message_to_kafka(doc):
    """שולח מסמך ל-Kafka תוך טיפול ב-topic חוקי"""
    msg = Message(
        id=doc.get('id'),
        title=doc.get('title'),
        content=doc.get('content'),
        url=doc.get('url'),
        source=doc.get('source'),
        image_url=doc.get('image_url'),
        classification=doc.get('classification'),
        entities=doc.get('entities', [])
    )

    classification = doc.get('classification')
    if isinstance(classification, dict):
        topic = classification.get('label', 'World')
    else:
        topic = classification or 'World'

    # ממיר ל-str ומחליף תווים לא חוקיים
    topic = re.sub(r'[^a-zA-Z0-9._-]', '_', str(topic))

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

# שולח את כל המסמכים הישנים
send_existing_documents()

# מאזין למסמכים חדשים בזמן אמת
col_ref = db.collection('news')
col_ref.on_snapshot(on_snapshot)

print("[Producer] Listening to Firebase for new documents...")
