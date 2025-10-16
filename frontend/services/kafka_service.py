import os
import json
from kafka import KafkaConsumer
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER_URL")  # localhost:9092

def subscribe_to_topic(topic: str):
    """
    מנוי ל־Kafka Topic והדפסת הודעות בזמן אמת
    """
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    print(f"Subscribed to topic: {topic}")
    for message in consumer:
        print("New message received:", message.value)
        # אפשר להחזיר או לשלוח את זה ל-Controller/Frontend
''