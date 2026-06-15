from flask import request


ROUTE_LESSONS = {
    "login": {
        "url": "/login",
        "function": "login()",
        "template": "login.html",
    },
    "dashboard": {
        "url": "/",
        "function": "dashboard()",
        "template": "dashboard.html",
    },
    "chat": {
        "url": "/chat",
        "function": "chat()",
        "template": "chat.html",
    },
    "activity_log": {
        "url": "/activity",
        "function": "activity_log()",
        "template": "activity_log.html",
    },
}


def register_teaching_banner(app):
    """Make route details available to every rendered page."""

    @app.context_processor
    def teaching_banner():
        return {
            "route_lesson": ROUTE_LESSONS.get(request.endpoint),
        }
