import re
import uuid

from sqlalchemy import (UUID, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Table, UniqueConstraint)
from sqlalchemy.orm import relationship, validates

from db.custom_types.roles_choice import RolesChoice
from db.database import Base

post_liked = Table(
    "liked_posts",
    Base.metadata,
    Column("user_id", ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("post_id", ForeignKey("post.post_id",
           ondelete="CASCADE"), primary_key=True),
)

watch_list = Table(
    "watch_list_middle",
    Base.metadata,
    Column("post_id", ForeignKey("post.post_id",
           ondelete="CASCADE"), primary_key=True),
    Column("watch_list_id", ForeignKey(
        "watch_list.id", ondelete="CASCADE"), primary_key=True),
)

USER_ROLES = [
    "custom",
    "manager",
    "admin",
]


class User(Base):
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String(length=255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(RolesChoice(USER_ROLES), nullable=False)

    liked_posts = relationship(
        "Post", secondary=post_liked, back_populates="user_liked")
    posts = relationship("Post", back_populates="author",
                         cascade="all, delete")
    comments = relationship("Comment", back_populates="comment_author")
    added_to_watchlist = relationship(
        "WatchList", back_populates="user_watchlist", uselist=False, cascade="all, delete")

    @validates("email")
    def validate_email(self, key, value):
        assert "@" in value, "Your email address must contain @"
        return value

    @validates("password")
    def validate_password(self, key, value):
        pattern = "^(?=.*[a-z].*[a-z])(?=.*[A-Z].*[A-Z])(?=.*[!@#$%^&*()_+={}[\]:;<>,.?~]).{8,}$"
        assert len(value) >= 8, "Password length must be more or equal to eight"
        assert re.search(pattern, value), "Password must match the pattern"
        return value


class Post(Base):
    __tablename__ = "post"
    post_id = Column(UUID(as_uuid=True), primary_key=True,
                     default=uuid.uuid4, index=True)
    title = Column(String, unique=True)
    description = Column(String)
    image_link = Column(String)

    user_liked = relationship(
        "User", secondary=post_liked, back_populates="liked_posts")
    author = relationship("User", back_populates="posts")
    author_id = Column(UUID(as_uuid=True), ForeignKey(
        "user.id", ondelete="CASCADE"), index=True)
    comments = relationship(
        "Comment", back_populates="commented_post", cascade="all, delete")
    watch_list = relationship(
        "WatchList", secondary=watch_list, back_populates="saved_posts")


class Comment(Base):
    __tablename__ = "comment"
    id = Column(UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, index=True)
    comment_text = Column(String, index=True)

    post_id = Column(UUID(as_uuid=True), ForeignKey(
        "post.post_id", ondelete="CASCADE"), index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey(
        "user.id", ondelete="CASCADE"), index=True)

    commented_post = relationship("Post", back_populates="comments")
    comment_author = relationship(
        "User", back_populates="comments", cascade="all, delete")


class WatchList(Base):
    __tablename__ = "watch_list"
    id = Column(UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, index=True)
    saved_date = Column(DateTime(timezone=True), onupdate=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "user.id",  ondelete="CASCADE"), index=True)

    saved_posts = relationship(
        "Post", secondary=watch_list, back_populates="watch_list", cascade="all, delete")

    user_watchlist = relationship(
        "User", back_populates="added_to_watchlist")
