from app.controllers.producer_controller import news_queue

def process_news_queue(state):
    """שולפת חדשות חדשות מהתור ומחזירה רשימה מעודכנת"""
    new_items = []
    while not news_queue.empty():
        new_items.append(news_queue.get())

    if new_items:
        print(f"[Updater] Added {len(new_items)} new articles")
        state.extend(new_items)

    return state, new_items
