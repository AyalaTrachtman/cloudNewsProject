import sys
import os

# מוסיף את התיקייה של kafka/app לפרויקט ל-Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from topic_controller import create_topics

if __name__ == "__main__":
    create_topics(["news_topic", "user_activity"])
