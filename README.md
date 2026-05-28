# Classroom Full-Stack Demo

This is a small high school HTML/CSS design class demo. It shows the path:

```text
Browser -> Flask container -> PostgreSQL container -> generated HTML -> browser
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

After students log in, they can enter their first name and choose a favorite color. That updates their row in PostgreSQL and refreshes the dashboard.

The app also includes a simple chat page:

```text
GET /chat  -> Flask reads messages from PostgreSQL and renders chat.html
POST /chat -> Flask saves a new message, then redirects back to GET /chat
```

This is meant to make browser requests, backend routes, database rows, and generated HTML visible in one classroom-friendly flow.

## Useful Docker Commands

```bash
docker compose ps
docker compose logs web
docker compose logs db
docker compose down
docker compose down -v
```

`docker compose down -v` removes the PostgreSQL volume, so the saved submissions and chat messages disappear too.

## What The Containers Do

The `web` container runs Flask. Flask receives browser requests, talks to the database, and renders Jinja HTML templates.

The `db` container runs PostgreSQL. It stores the fake users, class form submissions, and chat messages.

The Docker network lets the `web` container talk to the `db` container using the hostname `db`.

Port `5000` lets your browser reach the Flask app. Docker maps `localhost:5000` on your computer to port `5000` inside the web container.

## Classroom Reset

After logging in, use the reset button on the dashboard to clear all submissions and chat messages. Student names, colors, usernames, and passwords stay in place. This is only for quickly resetting the demo between classes.

## Cloudflare Tunnel Note

You do not need Cloudflare to run this app. For a classroom demo, a local app running at:

```text
http://localhost:5000
```

can be exposed with Cloudflare Tunnel by pointing `cloudflared` at that local address. No Cloudflare configuration is included here because the app should run locally with Docker first.
