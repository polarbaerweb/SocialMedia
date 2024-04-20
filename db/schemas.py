from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from db import models


class PostBase(BaseModel):
    title: str
    description: Optional[str] = None
    image_link: Optional[str] = None


class CommentBase(BaseModel):
    comment_text: str


class CommentCreate(CommentBase):
    post_id: UUID


class Comment(CommentBase):
    id: UUID
    post_id: UUID
    author_id: UUID

    class Config:
        orm_mode = True


class Post(PostBase):
    post_id: UUID
    author_id: UUID
    comments: List[Comment] = []

    class Config:
        orm_mode = True


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    pass


class UserBase(BaseModel):
    username: str
    email: str
    is_active: Optional[bool] = True
    role: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: UUID
    liked_posts: List[Post] = []
    posts: List[Post] = []

    class Config:
        orm_mode = True


class LikePost(BaseModel):
    post_id: UUID
    operation: str


class UserLogIn(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserUpdatePassword(BaseModel):
    old_password: str
    password: str


class WatchListBase(BaseModel):
    pass


class WatchListCreate(WatchListBase):
    pass


class WatchList(WatchListBase):
    id: UUID
    user_id: UUID
    saved_posts: List[Post] = []

    class Config:
        orm_mode = True
