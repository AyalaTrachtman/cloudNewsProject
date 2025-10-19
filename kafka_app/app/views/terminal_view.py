# app/views/terminal_view.py

class TerminalView:
    @staticmethod
    def show_message(message: str):
        """מציג הודעה כללית"""
        print(f"[INFO] {message}")

    @staticmethod
    def show_producer_event(topic: str, msg):
        """מציג הודעה שנשלחה ע״י הפרודוסר"""
        print(f"[Producer] Sent to topic '{topic}': {msg}")

    @staticmethod
    def show_consumer_event(topic: str, msg):
        """מציג הודעה שהתקבלה מהקונסיומר"""
        print(f"[Consumer] Received from topic '{topic}': {msg}")
