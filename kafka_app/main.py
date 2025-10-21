# app/main.py
from threading import Thread
from app.controllers import consumer_controller, producer_controller, topic_controller

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

if __name__ == "__main__":
    # יוצרים את כל הנושאים
    topic_controller.create_topics(NEWS_TOPICS)

    # מריצים את ה-consumer ב-thread
    consumer_thread = Thread(target=consumer_controller.run_consumer)
    consumer_thread.start()

    print("Producer and Consumer are running for all news topics...")
    consumer_thread.join()
