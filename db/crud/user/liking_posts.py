from typing import List

from db import models
from db.crud.post.crud_post import PostCRUDOperations
from db.crud.user.crud_user import UserCRUDOperations


class UserPostsLiking(PostCRUDOperations, UserCRUDOperations):
    """Managing posts liking, inherited from UserCRUDOperations and PostCRUDOperations, 
                so you need to pass post_id: UUID and user_id: UUID"""

    def _like_post(self) -> bool:
        """User liked post"""
        user: models.User = self.get_user_by_id(user_id=self._user_id)
        post: models.Post = self.get_post_by_id()

        if not user or not post:
            return False

        if user and post:
            user.liked_posts.append(post)
            self._db.commit()
            return True

    def get_liked_posts(self) -> List[models.Post] | None:
        """Get all posts user liked"""
        user: models.User = self.get_user_by_id(self._user_id)

        if user:
            return user.liked_posts

    def _dislike_post(self) -> bool:
        """User disliked post"""
        user: models.User = self.get_user_by_id(user_id=self._user_id)
        post: models.Post = self.get_post_by_id()

        if not user or not post:
            return False

        if user and post:
            user.liked_posts.remove(post)
            self._db.commit()
            return True

    def handle_likes(self, operation: str) -> bool:
        """Choose one of the two options liking or dislike, 
                                if user or post does not exist return False otherwise True"""
        operations = {
            "liking": self._like_post,
            "dislike": self._dislike_post
        }

        if operation in operations:
            return operations[operation]()
