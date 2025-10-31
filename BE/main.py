from fastapi import FastAPI
from .views.news_views import router as news_router
from .controllers.scheduler import start_scheduler
from .controllers.news_api import fetch_and_save_news
import time

app = FastAPI()
app.include_router(news_router)

# הפעלת ה-scheduler
start_scheduler()

if __name__ == "_main_":
    INTERVAL = 300  # כל 5 דקות
    print("Starting continuous news fetching loop (Ctrl+C to stop)...\n")

    try:
        while True:
            print(f" Fetching latest news at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
            fetch_and_save_news(country="us")
            print("Fetch completed, sleeping...\n")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl+C). Exiting gracefully.")