from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from classroom_app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    first_name: Mapped[str] = mapped_column(default="")
    favorite_color: Mapped[str]
    messages: Mapped[list["Message"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Message(db.Model):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    message: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    user: Mapped[User] = relationship(back_populates="messages")

    @property
    def username(self):
        return self.user.username

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def favorite_color(self):
        return self.user.favorite_color
