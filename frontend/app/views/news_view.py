import gradio as gr

def display_news(news_items):
    display = ""
    for n in news_items:
        display += f"{n.title}\n{n.description}\n{n.image_url}\nTags: {', '.join(n.tags)}\n\n"
    return display

def create_interface(controller_fn):
    iface = gr.Interface(
        fn=controller_fn,
        inputs=gr.Dropdown(["Politics", "Finance", "Science", "Culture", "Sport"]),
        outputs="text"
    )
    iface.launch()
