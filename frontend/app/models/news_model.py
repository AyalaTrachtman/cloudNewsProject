# app/models/news_model.py

class NewsItem:
    def __init__(self, title, description, image_url, tags):
        self.title = title
        self.description = description
        self.image_url = image_url
        self.tags = tags
