# Classroom Full-Stack Demo

This is a small classroom demo for Python students. It shows the path:

```text
Browser -> Flask -> Flask-SQLAlchemy -> PostgreSQL -> generated HTML -> browser
```

It is intentionally simple. The login uses fake classroom accounts only, and the passwords are stored in plain text so students can read the code easily. Real apps should never expose secrets in files like this and should never store plain-text passwords.

## Run With Docker

```bash
docker compose up --build
```

Then visit:

```text
http://localhost:5000
```

Demo accounts:

```text
user1 / sunnydesk
user2 / bluepencil
user3 / greenmarker
user4 / purplepaper
user5 / redcanvas
user6 / goldfolder
user7 / mintwindow
user8 / silverchair
user9 / coralnotebook
user10 / indigobrush
user11 / tealposter
user12 / amberpixel
user13 / rosekeyboard
user14 / limeproject
user15 / navysketch
user16 / peachscreen
user17 / violetgrid
user18 / aquaheader
user19 / olivebutton
user20 / rubyborder
user21 / cyanlayout
user22 / plumshadow
user23 / orangecard
user24 / forestfont
user25 / skyimage
user26 / pinkstyle
user27 / slatewire
user28 / yellowspace
user29 / magentalink
user30 / brownshape
```

After students log in, they can enter their first name and choose a favorite
color. Flask-SQLAlchemy updates their `User` model and refreshes the dashboard.

The app also includes a simple chat page:

```text
GET /chat  -> SQLAlchemy loads Message models and Flask renders chat.html
POST /chat -> Flask creates a Message model and SQLAlchemy saves it
```

This is meant to make browser requests, backend routes, database rows, and generated HTML visible in one classroom-friendly flow.

## Database Abstraction

The Python code uses **Flask-SQLAlchemy** instead of handwritten SQL. The
`User` and `Message` classes describe the data, while package methods such as
`db.select()`, `db.session.add()`, and `db.session.commit()` handle PostgreSQL.

## Python Modules

- `app.py` contains the routes and starts the server.
- `classroom_app/application.py` configures Flask and connects extensions.
- `classroom_app/models.py` contains the `User` and `Message` database models.
- `classroom_app/database.py` creates tables, seeds users, and waits for PostgreSQL.
- `classroom_app/activity.py` records activity and registers automatic page-visit logging.
- `classroom_app/extensions.py` provides the shared Flask-SQLAlchemy object.
- `classroom_app/teaching.py` supplies the visible URL-to-function teaching banner.

## Live Python Activity

After logging in, open **Python activity** in the navigation. The page streams
messages created by `classroom_app/activity.py`, such as `Jordan logged in` and
`Jordan visited the chat page`. This gives students a simple view of Python code
reacting to browser requests.

## Useful Docker Commands

```bash
docker compose ps
docker compose logs web
docker compose logs db
docker compose down
docker compose down -v
```

`docker compose down -v` removes the PostgreSQL volume, so the saved chat messages disappear too.

## What The Containers Do

The `web` container runs Flask. Flask receives browser requests, talks to the database, and renders Jinja HTML templates.

The `db` container runs PostgreSQL. It stores the fake users and chat messages.

The Docker network lets the `web` container talk to the `db` container using the hostname `db`.

Port `5000` lets your browser reach the Flask app. Docker maps `localhost:5000` on your computer to port `5000` inside the web container.

## Classroom Reset

After logging in, use the reset button on the dashboard to clear all chat messages. Student names, colors, usernames, and passwords stay in place. This is only for quickly resetting the demo between classes.

## Cloudflare Tunnel Note

You do not need Cloudflare to run this app. For a classroom demo, a local app running at:

```text
http://localhost:5000
```

can be exposed with Cloudflare Tunnel by pointing `cloudflared` at that local address. No Cloudflare configuration is included here because the app should run locally with Docker first.
