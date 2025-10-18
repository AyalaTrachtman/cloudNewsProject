from fastapi import FastAPI
from .controllers.news_api import fetch_and_save_news
from .controllers.firebase_db import save_news, get_news, update_news, delete_news, get_all_news
from .models.news_model import News
from .controllers.scheduler import start_scheduler

app = FastAPI()
start_scheduler()
# CREATE
@app.post("/news/{news_id}")
def create_news(news_id: str, news: News):
    save_news(news_id, news.dict())
    return {"message": "News saved"}

# READ
@app.get("/news/{news_id}")
def read_news(news_id: str):
    data = get_news(news_id)
    if data:
        return data
    return {"error": "News not found"}

# UPDATE
@app.put("/news/{news_id}")
def edit_news(news_id: str, news: News):
    update_news(news_id, news.dict())
    return {"message": "News updated"}

# DELETE
@app.delete("/news/{news_id}")
def remove_news(news_id: str):
    delete_news(news_id)
    return {"message": "News deleted"}

# TEST Firebase
@app.get("/test-firebase")
def test_firebase():
    test_id = "1"
    test_data = {"title": "שלום עולם", "content": "זוהי ידיעה לדוגמה"}
    save_news(test_id, test_data)
    retrieved = get_news(test_id)
    return retrieved

# FETCH NEWS (כולל ניתוח Hugging Face)
@app.get("/fetch-news")
def fetch_news(country: str = "us", category: str = None):
    """
    שולף חדשות מ-API, מנתח עם Hugging Face ושומר ב-Firebase
    """
    result = fetch_and_save_news(country=country, category=category)
    return {
        "message": result["message"],
        "saved_count": len(result["articles"]),
        "ids": result["ids"]
    }

# READ ALL
@app.get("/news")
def read_all_news():
    return get_all_news()
