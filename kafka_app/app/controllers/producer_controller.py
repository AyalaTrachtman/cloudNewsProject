import sys
import os
import json
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from firebase_admin import credentials, firestore, initialize_app
from kafka import KafkaProducer
from kafka_app.app.models.message_model import Message
from kafka_app.app.views.terminal_view import TerminalView  # ✅ נוספה השורה הזו

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

# סט כדי למנוע שליחה כפולה של כתבות
sent_urls = set()
sent_count = 0  # מונה של כתבות שנכנסו ל-Kafka


def send_message_to_kafka(doc):
    """שולח מסמך ל-Kafka תוך טיפול ב-topic חוקי"""
    global sent_count
    url = doc.get('url')
    if not url or url in sent_urls:
        return  # כבר נשלח או אין URL
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

    topic = re.sub(r'[^a-zA-Z0-9.-]', '', str(topic))
    if topic not in VALID_TOPICS:
        topic = "World"

    producer.send(topic, msg)
    producer.flush()

    sent_count += 1  # עדכון המונה
    TerminalView.show_producer_event(topic, msg.title)  # ✅ שימוש ב־TerminalView


def send_existing_documents():
    """שולח את כל המסמכים הקיימים במסד ל-Kafka"""
    docs = db.collection('news').stream()
    for doc in docs:
        send_message_to_kafka(doc.to_dict())

    TerminalView.show_message(f"Total documents sent to Kafka: {sent_count}")  # ✅ שימוש ב־TerminalView


def on_snapshot(col_snapshot, changes, read_time):
    """מאזין לשינויים בזמן אמת ומעביר ל-Kafka"""
    for change in changes:
        if change.type.name == 'ADDED':
            send_message_to_kafka(change.document.to_dict())

    TerminalView.show_message(f"Total documents sent to Kafka: {sent_count}")  # ✅ שימוש ב־TerminalView


# שליחת מסמכים קיימים
send_existing_documents()

# מאזין למסמכים חדשים בזמן אמת
# col_ref = db.collection('news')
# col_ref.on_snapshot(on_snapshot)

TerminalView.show_message("Listening to Firebase for new documents...")  # ✅ שימוש ב־TerminalView