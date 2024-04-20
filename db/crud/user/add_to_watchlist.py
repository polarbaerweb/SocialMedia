from db import models
from db.crud.post.crud_post import PostCRUDOperations
from db.crud.user.crud_user import UserCRUDOperations


class AddToWatchList(PostCRUDOperations, UserCRUDOperations):
    """Managing with watch list"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_to_watchlist(self) -> models.WatchList:
        """if watch list exists add post or create new one and readd"""
        user: models.User = self.get_user_by_id(user_id=self._user_id)
        post: models.Post = self.get_post_by_id()
        watch_list: models.WatchList = user.added_to_watchlist

        if not watch_list:
            watch_list = self.__create_watchlist()

        if user and post:
            watch_list.saved_posts.append(post)
            self._db.commit()

        return watch_list

    def remove_post_from_watchlist(self) -> models.WatchList:
        """remove post from watch list if post there is"""
        user: models.User = self.get_user_by_id(user_id=self._user_id)
        post: models.Post = self.get_post_by_id()
        watch_list: models.WatchList = user.added_to_watchlist

        if user and post and watch_list and (post in watch_list.saved_posts):
            watch_list.saved_posts.remove(post)
            self._db.commit()

        return watch_list

    def __create_watchlist(self) -> models.WatchList:
        """if watch list does not exist create one and return it is instance"""
        watch_list = models.WatchList(
            user_id=self._user_id,
        )

        self._db.add(watch_list)
        self._db.commit()
        self._db.refresh(watch_list)

        return watch_list

    def get_watchlist(self) -> models.WatchList:
        """if user exists return his watchlist"""
        user: models.User = self.get_user_by_id(user_id=self._user_id)

        if user:
            return user.added_to_watchlist
