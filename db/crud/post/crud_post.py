from uuid import UUID

from sqlalchemy import and_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import models, schemas


class PostCRUDOperations:
    """Basic post CRUD operations"""

    def __init__(self, db: Session, post_id: UUID | None = None, user_id: UUID | None = None):
        self._db = db
        self._post_id = post_id
        self._user_id = user_id

    def get_all_posts(self):
        return self._db.query(models.Post).all()

    def get_post_by_id(self) -> models.Post:
        post = self._db.query(models.Post).filter(
            models.Post.post_id == self._post_id).first()

        return post

    def create_post(self, post: schemas.PostCreate) -> models.Post | bool:
        try:
            post_db = models.Post(
                title=post.title,
                description=post.description,
                image_link=post.image_link,
                author_id=self._user_id
            )

            self._db.add(post_db)
            self._db.commit()
            self._db.refresh(post_db)
        except IntegrityError:
            return False
        else:
            return post_db

    def update_post(self, post: schemas.PostUpdate) -> models.Post:
        self._db.execute(update(models.Post).where(
            and_(models.Post.post_id == self._post_id, models.Post.author_id == self._user_id)).values(**post.dict(exclude_unset=True)))

        self._db.commit()

        return self._db.query(models.Post).filter(models.Post.post_id == self._post_id).first()

    def delete_post(self) -> bool:
        deleted = self._db.query(models.Post).filter(and_(
            models.Post.post_id == self._post_id, models.Post.author_id == self._user_id)).delete()

        self._db.commit()

        return deleted == 1
