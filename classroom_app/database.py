import time

from sqlalchemy.exc import OperationalError

from classroom_app.extensions import db
from classroom_app.models import User


DEMO_USERS = [
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
    ("admin", "admin1", "#92400e"),
]


def initialize_database():
    """Create model tables and add any missing classroom users."""
    db.create_all()

    existing_usernames = set(db.session.scalars(db.select(User.username)))
    for username, password, favorite_color in DEMO_USERS:
        if username not in existing_usernames:
            db.session.add(
                User(
                    username=username,
                    password=password,
                    favorite_color=favorite_color,
                )
            )

    db.session.commit()


def wait_for_database(app):
    """Retry initialization while the PostgreSQL container starts."""
    with app.app_context():
        for attempt in range(1, 11):
            try:
                initialize_database()
                return
            except OperationalError:
                db.session.rollback()
                if attempt == 10:
                    raise
                time.sleep(1)
