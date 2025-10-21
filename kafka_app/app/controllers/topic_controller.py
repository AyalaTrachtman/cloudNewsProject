# app/controllers/topic_controller.py
from kafka.admin import KafkaAdminClient, NewTopic

KAFKA_BROKER = "localhost:9092"

# רשימת טופיקים חוקיים בלבד
VALID_TOPICS = [
    "Politics", "Finance", "Science", "Culture",
    "Sport", "Technology", "Health", "World"
]

def create_topics(topics_list):
    # מסנן רק טופיקים חוקיים
    valid_topics = [t for t in topics_list if t in VALID_TOPICS]

    if not valid_topics:
        print("[TopicController] ⚠️ No valid topics to create.")
        return

    admin_client = KafkaAdminClient(
        bootstrap_servers=KAFKA_BROKER,
        client_id='admin'
    )

    topic_objects = [
        NewTopic(name=topic_name, num_partitions=1, replication_factor=1)
        for topic_name in valid_topics
    ]

    try:
        admin_client.create_topics(new_topics=topic_objects, validate_only=False)
        print(f"[TopicController] ✅ Topics created: {valid_topics}")
    except Exception as e:
        print(f"[TopicController] ❌ Error creating topics: {e}")
    finally:
        admin_client.close()
