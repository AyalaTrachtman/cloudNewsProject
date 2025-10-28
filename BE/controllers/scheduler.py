from apscheduler.schedulers.blocking import BlockingScheduler
from cloudNewsProject.BE.controllers.news_api import fetch_and_save_news
from cloudNewsProject.BE.controllers.firebase_db import get_all_news, save_news

def fetch_and_save_news_unique(country="us"):
    """
    שולף כתבות מ-NewsAPI ושומר רק כתבות חדשות ב-Firestore
    """
    # שליפת כתבות קיימות
    all_articles = get_all_news()
    existing_urls = {article['url'] for article in all_articles if 'url' in article}

    # שליפת כתבות חדשות מה-API
    new_articles_data = fetch_and_save_news(country=country)

    if "articles" not in new_articles_data:
        print("No articles received from NewsAPI.")
        return

    saved_count = 0
    for article in new_articles_data["articles"]:
        if article["url"] not in existing_urls:
            save_news(article["id"], article)
            saved_count += 1
            print(f"Saved new article: {article['title']}")

    print(f"Finished fetch cycle. {saved_count} new articles saved.")

def start_scheduler():
    scheduler = BlockingScheduler()
    # אפשר לשנות את ה-interval למספר דקות/שעות
    scheduler.add_job(fetch_and_save_news_unique, 'interval', minutes=1)
    print("Scheduler started. Fetching news every 1 minute...")
    scheduler.start()

if __name__ == "__main__":
    start_scheduler()