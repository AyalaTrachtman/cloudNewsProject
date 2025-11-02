# main.py
import threading
from  cloudNewsProject.kafka_app.app.controllers.producer_controller import send_existing_documents, on_snapshot, db # זה מה שהכנת קודם
from cloudNewsProject. frontend.views.news_view import demo  # זה הקובץ שלך עם Gradio (הכל בתוך demo)  
def start_producer():
    """ריצה של ה-Producer: שולח כתבות קיימות ומאזין לשינויים"""
    print("[Main] Starting Producer...")
    send_existing_documents()          # שולח את כל הכתבות הקיימות
    on_snapshot(on_snapshot)   # מאזין לשינויים בזמן אמת
    print("[Main] Producer is listening to Firebase...")

if __name__ == "_main_":
    # מריצים את Producer ב-thread נפרד
    threading.Thread(target=start_producer, daemon=True).start()

    # מריצים את Gradio UI
    print("[Main] Starting Gradio UI...")
    demo.launch(inbrowser=True)