from cloudNewsProject.BE.controllers.news_api import classify_article
from cloudNewsProject.BE.controllers.firebase_db import get_all_news, update_news

def update_existing_classifications():
    all_articles = get_all_news()  # רשימה של מאמרים
    for article in all_articles:
        news_id = article.get("id")
        content = article.get("content")
        if not content or not news_id:
            continue
        classification = classify_article(content)
        print(f"Updating article '{article.get('title', '')}' to classification '{classification}'")
        update_news(news_id, {"classification": classification})

if __name__ == "__main__":
    update_existing_classifications()
