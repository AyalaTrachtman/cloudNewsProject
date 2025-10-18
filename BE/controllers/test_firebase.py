from firebase_db import save_news

test_data = {"title": "Test", "content": "This is a test"}
save_news("test_id", test_data)
print("Saved test article")
