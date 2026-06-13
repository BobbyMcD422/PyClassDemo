import json

from flask import Response, redirect, render_template, request, session, stream_with_context, url_for

from classroom_app.activity import (
    activity_condition,
    activity_events,
    activity_user_name,
    current_user,
    record_activity,
)
from classroom_app.application import create_app
from classroom_app.database import wait_for_database
from classroom_app.extensions import db
from classroom_app.models import Message, User


app = create_app()


@app.route("/login", methods=["GET", "POST"])
def login():
    """Show the login form and handle the fake classroom login."""
    if current_user():
        return redirect(url_for("dashboard"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = db.session.scalar(
            db.select(User).filter_by(username=username, password=password)
        )

        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            session["activity_name"] = user.first_name or user.username
            record_activity(f"{activity_user_name()} logged in")
            return redirect(url_for("dashboard"))

        error = "That demo username or password did not match."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    if session.get("user_id"):
        record_activity(f"{activity_user_name()} logged out")
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def dashboard():
    """Main classroom page: browser -> Flask -> SQLAlchemy -> HTML."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    message_count = db.session.scalar(
        db.select(db.func.count()).select_from(Message)
    )

    return render_template(
        "dashboard.html",
        user=user,
        message_count=message_count,
    )


@app.route("/profile", methods=["POST"])
def update_profile():
    """Update the student's User model through SQLAlchemy."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    first_name = request.form.get("first_name", "").strip() or user.username
    favorite_color = request.form.get("favorite_color", "#2563eb").strip()

    if not favorite_color.startswith("#") or len(favorite_color) != 7:
        favorite_color = "#2563eb"

    user.first_name = first_name
    user.favorite_color = favorite_color
    db.session.commit()

    session["activity_name"] = first_name
    return redirect(url_for("dashboard"))


@app.route("/chat", methods=["GET", "POST"])
def chat():
    """Show a simple classroom chat and save new messages."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        message = request.form.get("message", "").strip()

        if message:
            db.session.add(Message(user=user, message=message))
            db.session.commit()

        return redirect(url_for("chat"))

    messages = db.session.scalars(
        db.select(Message)
        .order_by(Message.created_at.desc())
        .limit(30)
    ).all()

    return render_template("chat.html", user=user, messages=messages)


@app.route("/activity")
def activity_log():
    """Show live activity messages published by the Python application."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    return render_template("activity_log.html", user=user)


@app.route("/activity/stream")
def activity_stream():
    """Stream Python activity messages to the browser as Server-Sent Events."""
    if not current_user():
        return Response("Log in to view Python activity.", status=401)

    def generate_events():
        try:
            last_event_id = int(request.headers.get("Last-Event-ID", "0"))
        except ValueError:
            last_event_id = 0

        yield "retry: 3000\n\n"
        yield "event: ready\ndata: {}\n\n"

        while True:
            with activity_condition:
                new_events = [
                    event for event in activity_events if event["id"] > last_event_id
                ]

                if not new_events:
                    activity_condition.wait(timeout=15)
                    new_events = [
                        event for event in activity_events
                        if event["id"] > last_event_id
                    ]

            if not new_events:
                yield ": keep-alive\n\n"
                continue

            for event in new_events:
                last_event_id = event["id"]
                yield f"id: {event['id']}\ndata: {json.dumps(event)}\n\n"

    return Response(
        stream_with_context(generate_events()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/reset-demo", methods=["POST"])
def reset_demo():
    """Clear classroom chat messages while preserving student accounts."""
    if not current_user():
        return redirect(url_for("login"))

    db.session.execute(db.delete(Message))
    db.session.commit()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    wait_for_database(app)
    app.run(host="0.0.0.0", port=5000, debug=True)
