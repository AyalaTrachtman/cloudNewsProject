# app/controllers/consumer_controller.py
from kafka import KafkaConsumer
from app.models.message_model import Message
from app.views.terminal_view import show_message_received

KAFKA_BROKER = "localhost:9092"
NEWS_TOPICS = [
    "Politics",
    "Finance",
    "Science",
    "Culture",
    "Sport",
    "Technology",
    "Health",
    "World"
]

consumer = KafkaConsumer(
    *NEWS_TOPICS,
    bootstrap_servers=[KAFKA_BROKER],
    value_deserializer=lambda m: Message.from_json(m.decode('utf-8'))
)

def run_consumer():
    for msg in consumer:
        show_message_received(msg)
