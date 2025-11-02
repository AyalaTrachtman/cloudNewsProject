from datetime import datetime
# --- Format date helper ---
def format_date(date_str):
    """מחזיר רק את התאריך בפורמט YYYY-MM-DD"""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str.split("T")[0]  # fallback
