# app/controllers/topic_controller.py
from kafka.admin import KafkaAdminClient, NewTopic

KAFKA_BROKER = "localhost:9092"

def create_topics(topics_list):
    admin_client = KafkaAdminClient(
        bootstrap_servers=KAFKA_BROKER,
        client_id='admin'
    )

    topic_objects = [
        NewTopic(name=topic_name, num_partitions=1, replication_factor=1)
        for topic_name in topics_list
    ]

    try:
        admin_client.create_topics(new_topics=topic_objects, validate_only=False)
        print(f"[TopicController] Topics created: {topics_list}")
    except Exception as e:
        print(f"[TopicController] Error creating topics: {e}")
    finally:
        admin_client.close()
