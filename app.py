import json
import os
import queue
import socket
import threading
import time

import docker
import psycopg2
from flask import Flask, Response, redirect, render_template, request, session, stream_with_context, url_for
from psycopg2.extras import RealDictCursor


app = Flask(__name__)

# Flask uses this key to sign the classroom session cookie.
# Real apps should load a secret value from a private place, not hard-code it.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "classroom-demo-secret")


def get_db_connection():
    """Connect to the PostgreSQL database container."""
    # PSEUDO-CODE:
    # 1. Read the database address, name, username, and password.
    # 2. Open a connection to PostgreSQL.
    # 3. Return that connection so a route can run SQL.
    return psycopg2.connect(
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=os.environ.get("DATABASE_PORT", "5432"),
        dbname=os.environ.get("DATABASE_NAME", "demoapp"),
        user=os.environ.get("DATABASE_USER", "demo"),
        password=os.environ.get("DATABASE_PASSWORD", "demo"),
    )


def init_db():
    """Create the demo tables and seed fake users.

    PostgreSQL is where the app remembers users and form submissions.
    Docker Compose starts PostgreSQL in a separate "db" container, and the
    Flask "web" container connects to it using the DATABASE_* settings.
    """
    # PSEUDO-CODE:
    # 1. Make a list of fake classroom users.
    # 2. Connect to PostgreSQL.
    # 3. Create the users table if it is missing.
    # 4. Remove the old submissions table from an earlier version of the demo.
    # 5. Create the messages table if it is missing.
    # 6. Insert the fake users only if they do not already exist.
    demo_users = [
        ("user1", "sunnydesk", "#f97316"),
        ("user2", "bluepencil", "#2563eb"),
        ("user3", "greenmarker", "#16a34a"),
        ("user4", "purplepaper", "#9333ea"),
        ("user5", "redcanvas", "#dc2626"),
        ("user6", "goldfolder", "#ca8a04"),
        ("user7", "mintwindow", "#0d9488"),
        ("user8", "silverchair", "#64748b"),
        ("user9", "coralnotebook", "#fb7185"),
        ("user10", "indigobrush", "#4f46e5"),
        ("user11", "tealposter", "#0891b2"),
        ("user12", "amberpixel", "#d97706"),
        ("user13", "rosekeyboard", "#e11d48"),
        ("user14", "limeproject", "#65a30d"),
        ("user15", "navysketch", "#1e3a8a"),
        ("user16", "peachscreen", "#ea580c"),
        ("user17", "violetgrid", "#7c3aed"),
        ("user18", "aquaheader", "#0284c7"),
        ("user19", "olivebutton", "#4d7c0f"),
        ("user20", "rubyborder", "#be123c"),
        ("user21", "cyanlayout", "#06b6d4"),
        ("user22", "plumshadow", "#a855f7"),
        ("user23", "orangecard", "#f59e0b"),
        ("user24", "forestfont", "#15803d"),
        ("user25", "skyimage", "#0ea5e9"),
        ("user26", "pinkstyle", "#db2777"),
        ("user27", "slatewire", "#475569"),
        ("user28", "yellowspace", "#eab308"),
        ("user29", "magentalink", "#c026d3"),
        ("user30", "brownshape", "#92400e"),
    ]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    first_name TEXT NOT NULL DEFAULT '',
                    favorite_color TEXT NOT NULL
                );
                """
            )
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT NOT NULL DEFAULT '';")
            # This demo used to have a submissions table. Dropping it keeps the
            # classroom database focused on the current chat example.
            cur.execute("DROP TABLE IF EXISTS submissions;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Classroom-only shortcut: plain-text passwords are not appropriate
            # for real apps. Production apps need password hashing and stronger
            # authentication rules.
            for username, password, favorite_color in demo_users:
                cur.execute(
                    """
                    INSERT INTO users (username, password, favorite_color)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (username) DO NOTHING;
                    """,
                    (username, password, favorite_color),
                )


def wait_for_database():
    """Give the db container a few seconds to finish starting up."""
    for attempt in range(1, 11):
        try:
            init_db()
            return
        except psycopg2.OperationalError:
            if attempt == 10:
                raise
            time.sleep(1)


def current_user():
    # PSEUDO-CODE:
    # 1. Check the Flask session cookie for a saved user id.
    # 2. If there is no user id, the visitor is not logged in.
    # 3. If there is a user id, load that user row from PostgreSQL.
    if "user_id" not in session:
        return None

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, first_name, favorite_color FROM users WHERE id = %s;",
                (session["user_id"],),
            )
            return cur.fetchone()


def compose_containers():
    """Find the containers that belong to this Docker Compose project."""
    client = docker.from_env()
    this_container = client.containers.get(socket.gethostname())
    project_name = this_container.labels.get("com.docker.compose.project")

    if not project_name:
        raise RuntimeError("The web app is not running as a Docker Compose service.")

    containers = client.containers.list(
        all=True,
        filters={"label": f"com.docker.compose.project={project_name}"},
    )
    return sorted(
        containers,
        key=lambda container: container.labels.get("com.docker.compose.service", container.name),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Show the login form and handle the fake classroom login."""
    # PSEUDO-CODE:
    # GET request:
    #   Show the login page.
    # POST request:
    #   Read the username and password from the form.
    #   Look for a matching fake user in PostgreSQL.
    #   If found, remember the user id in the Flask session.
    #   If not found, show a simple error message.
    if current_user():
        return redirect(url_for("dashboard"))

    error = None

    # If information is sent to our login route, we will process the login
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # This is intentionally simple for teaching SQL and Flask routes.
                # Real apps should never check plain-text passwords like this.
                cur.execute(
                    """
                    SELECT id, username
                    FROM users
                    WHERE username = %s AND password = %s;
                    """,
                    (username, password),
                )
                user = cur.fetchone()

        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))

        error = "That demo username or password did not match."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def dashboard():
    """Main classroom page: browser -> Flask route -> PostgreSQL -> HTML."""
    # PSEUDO-CODE:
    # 1. Find out who is logged in.
    # 2. If nobody is logged in, send them to /login.
    # 3. Count chat messages from PostgreSQL.
    # 4. Render dashboard.html with the user and database values.
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS total FROM messages;")
            message_count = cur.fetchone()["total"]

    return render_template(
        "dashboard.html",
        user=user,
        message_count=message_count,
    )


@app.route("/profile", methods=["POST"])
def update_profile():
    """Update the student's fake profile row in PostgreSQL."""
    # PSEUDO-CODE:
    # 1. Find the logged-in student.
    # 2. Read first name and favorite color from the form.
    # 3. Update that student's row in the users table.
    # 4. Redirect back to / so the refreshed page shows the new values.
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    first_name = request.form.get("first_name", "").strip()
    favorite_color = request.form.get("favorite_color", "#2563eb").strip()

    if not first_name:
        first_name = user["username"]

    if not favorite_color.startswith("#") or len(favorite_color) != 7:
        favorite_color = "#2563eb"

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET first_name = %s, favorite_color = %s
                WHERE id = %s;
                """,
                (first_name, favorite_color, user["id"]),
            )

    return redirect(url_for("dashboard"))


@app.route("/chat", methods=["GET", "POST"])
def chat():
    """Show a simple classroom chat and save new messages."""
    # PSEUDO-CODE:
    # GET request:
    #   Read recent messages from PostgreSQL.
    #   Render chat.html so the browser can display them.
    # POST request:
    #   Read the message from the form.
    #   Insert the message into PostgreSQL.
    #   Redirect back to /chat, which causes a fresh GET request.
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        message = request.form.get("message", "").strip()

        if message:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO messages (user_id, message)
                        VALUES (%s, %s);
                        """,
                        (user["id"], message),
                    )

        return redirect(url_for("chat"))

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT messages.id,
                       users.username,
                       users.first_name,
                       users.favorite_color,
                       messages.message,
                       messages.created_at
                FROM messages
                JOIN users ON messages.user_id = users.id
                ORDER BY messages.created_at DESC
                LIMIT 30;
                """
            )
            rows = cur.fetchall()

    return render_template("chat.html", user=user, messages=rows)


@app.route("/container-logs")
def container_logs():
    """Show live stdout and stderr from this app's Compose containers."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    return render_template("container_logs.html", user=user)


@app.route("/container-logs/stream")
def container_logs_stream():
    """Stream Docker log lines to the browser as Server-Sent Events."""
    if not current_user():
        return Response("Log in to view container output.", status=401)

    def generate_events():
        messages = queue.Queue()
        stop_event = threading.Event()
        streams = []

        def read_logs(container):
            service = container.labels.get("com.docker.compose.service", container.name)

            try:
                log_stream = container.logs(
                    stream=True,
                    follow=True,
                    tail=80,
                    timestamps=True,
                )
                streams.append(log_stream)

                for line in log_stream:
                    if stop_event.is_set():
                        break
                    messages.put(
                        {
                            "service": service,
                            "message": line.decode("utf-8", errors="replace").rstrip(),
                        }
                    )
            except Exception as error:
                messages.put(
                    {
                        "service": service,
                        "message": f"Unable to read logs: {error}",
                    }
                )

        try:
            containers = compose_containers()

            yield "retry: 3000\n\n"
            yield f"event: ready\ndata: {json.dumps({'containers': len(containers)})}\n\n"

            for container in containers:
                thread = threading.Thread(target=read_logs, args=(container,), daemon=True)
                thread.start()

            while True:
                try:
                    message = messages.get(timeout=15)
                    yield f"data: {json.dumps(message)}\n\n"
                except queue.Empty:
                    yield ": keep-alive\n\n"
        except Exception as error:
            payload = {"service": "viewer", "message": f"Unable to connect to Docker: {error}"}
            yield f"event: viewer-error\ndata: {json.dumps(payload)}\n\n"
        finally:
            stop_event.set()
            for log_stream in streams:
                close = getattr(log_stream, "close", None)
                if close:
                    close()

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
    # Classroom reset only: this clears practice chat messages between demos.
    # PSEUDO-CODE:
    # 1. Make sure a fake classroom user is logged in.
    # 2. Delete all rows from messages.
    # 3. Leave student names, colors, usernames, and passwords alone.
    if not current_user():
        return redirect(url_for("login"))

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM messages;")

    init_db()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    # localhost:5000 means "visit port 5000 on this computer."
    # Docker maps that local port to the Flask app inside the web container.
    wait_for_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
