from collections import deque
import threading
import time

from flask import request, session

from classroom_app.extensions import db
from classroom_app.models import User


activity_events = deque(maxlen=200)
activity_condition = threading.Condition()
activity_sequence = 0


def current_user():
    """Load the logged-in student's User model."""
    if "user_id" not in session:
        return None

    return db.session.get(User, session["user_id"])


def activity_user_name():
    """Return the student's first name, or their username if none is set."""
    cached_name = session.get("activity_name") or session.get("username")
    if cached_name:
        return cached_name

    user = current_user()
    if not user:
        return "Unknown user"

    name = user.first_name or user.username
    session["username"] = user.username
    session["activity_name"] = name
    return name


def record_activity(message):
    """Publish one Python activity message to the live classroom feed."""
    global activity_sequence

    with activity_condition:
        activity_sequence += 1
        event = {
            "id": activity_sequence,
            "time": time.strftime("%H:%M:%S"),
            "message": message,
        }
        activity_events.append(event)
        activity_condition.notify_all()

    print(f"[ACTIVITY] {message}", flush=True)


def register_activity_logging(app):
    """Attach automatic page-visit logging to the Flask app."""

    @app.before_request
    def log_page_visit():
        page_names = {
            "dashboard": "dashboard",
            "chat": "chat",
            "activity_log": "Python activity",
        }
        page_name = page_names.get(request.endpoint)

        if request.method == "GET" and page_name and session.get("user_id"):
            record_activity(f"{activity_user_name()} visited the {page_name} page")
