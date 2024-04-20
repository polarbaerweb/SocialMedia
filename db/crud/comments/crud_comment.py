"""
This module provides only basic crud operations and if you need to extend it 
is functionality you will need to inherit from class as entry point
"""

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from db import models, schemas
from db.crud.post import crud_post


class CommentCRUDOperations:
    """Basic comment CRUD operations"""

    def __init__(self, db: Session, post_id: UUID | None = None, author_id: UUID | None = None):
        self._db = db
        self.__post_id = post_id
        self.__author_id = author_id

    def get_all_comments_by_post_id(self) -> List[models.Comment]:
        """Get all comments related to the post"""
        comment_db = crud_post.PostCRUDOperations(
            db=self._db, post_id=self.__post_id)
        post: models.Post = comment_db.get_post_by_id()

        if post:
            return post.comments

    def create_comment(self, comment: schemas.CommentCreate) -> models.Comment | bool:
        """leave comment to the post"""
        comment_db = models.Comment(
            comment_text=comment.comment_text,
            post_id=comment.post_id,
            author_id=self.__author_id
        )

        self._db.add(comment_db)
        self._db.commit()
        self._db.refresh(comment_db)

        return comment_db

    def delete_comment_by_id(self, comment_id: UUID) -> bool:
        """delete comment"""
        deleted = self._db.query(models.Comment).filter(
            models.Comment.id == comment_id).delete()

        self._db.commit()

        return deleted == 1
