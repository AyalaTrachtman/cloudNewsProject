from apscheduler.schedulers.background import BackgroundScheduler
from .news_api import fetch_and_save_news

def start_scheduler():
    scheduler = BackgroundScheduler()
    #scheduler.add_job(fetch_and_save_news, 'interval', hours=1)
    scheduler.add_job(fetch_and_save_news, 'interval', minutes=1)
    scheduler.start()
