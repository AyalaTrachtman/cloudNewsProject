# app/controllers/producer_controller.py
from firebase_admin import firestore, initialize_app
from kafka import KafkaProducer
from app.models.message_model import Message

# אתחול Firebase
initialize_app()
db = firestore.client()

# הגדרת שרת Kafka
KAFKA_BROKER = "localhost:9092"
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda m: m.to_json().encode('utf-8')
)

def on_snapshot(col_snapshot, changes, read_time):
    """מאזין לשינויים במסד הנתונים (Firestore) ושולח לקפקא"""
    for change in changes:
        if change.type.name == 'ADDED':
            doc = change.document.to_dict()

            # נבנה את האובייקט לפי המבנה החדש שלך
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

            # נחליט לאיזה topic לשלוח (לפי הנושא)
            topic = doc.get('classification', 'World') or 'World'

            # שולחים את ההודעה לקפקא
            producer.send(topic, msg)
            print(f"[Producer] Sent to topic '{topic}': {msg.title}")

# מאזין בזמן אמת למסד הנתונים
col_ref = db.collection('articles')  # תשני לפי שם הקולקשן שלך
col_ref.on_snapshot(on_snapshot)