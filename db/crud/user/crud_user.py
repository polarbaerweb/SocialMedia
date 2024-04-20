"""
    This module provides only basic crud operations and if you need to extend it
    is functionality you will need to inherit from class as entry point
    """

from typing import List
from uuid import UUID

from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session

from db import models, schemas
from utils.password_handlers.password_hash_verify import (get_password_hash,
                                                          verify_password)


class UserCRUDOperations:
    """Making Basic CRUD operations with user"""

    def __init__(self, db: Session):
        self._db = db

    def get_user_by_id(self, user_id: UUID) -> models.User | str:
        user = self._db.query(models.User).filter(
            models.User.id == user_id).first()

        return user

    def get_user_by_email(self, email: str) -> models.User | None:
        user = self._db.query(models.User).filter(
            models.User.email == email).first()

        return user

    def get_all_users(self) -> List[models.User]:
        users = self._db.query(models.User).all()
        return users

    def user_create(self, user: schemas.UserCreate) -> models.User:
        hashed_password = get_password_hash(user.password)

        try:
            db_user = models.User(
                username=user.username,
                email=user.email,
                role=user.role,
                password=hashed_password,
            )

            self._db.add(db_user)
            self._db.commit()
            self._db.refresh(db_user)
        except StatementError:
            return {"message": "role must be in range of custom, manager and admin"}
        else:
            return db_user

    def update_password(self, password_data: schemas.UserUpdatePassword, user_id: UUID) -> models.User | bool:
        db_user: models.User = self.get_user_by_id(user_id)

        if not db_user:
            return False

        if not verify_password(password_data.old_password, db_user.password):
            return False

        db_user.password = get_password_hash(password_data.password)

        self._db.commit()

        return db_user

    def remove_user(self, user_id: UUID) -> bool:
        user = self._db.query(models.User).filter(
            models.User.id == user_id).delete()

        self._db.commit()

        return user == 1
