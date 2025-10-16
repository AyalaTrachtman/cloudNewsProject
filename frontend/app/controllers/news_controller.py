from app.models.news_model import NewsItem
from services.api_service import get_news_by_topic

def show_news_controller(topic):
    raw_news = get_news_by_topic(topic)
    news_items = [NewsItem(n['title'], n['description'], n['image_url'], n['tags']) for n in raw_news]
    return news_items
