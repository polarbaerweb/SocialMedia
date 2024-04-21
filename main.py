from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from db import models, schemas
from db.crud.comments import crud_comment
from db.crud.post import crud_post
from db.crud.user import add_to_watchlist, crud_user, liking_posts
from db.database import SESSION_LOCAL, engine
from utils.password_handlers.password_hash_verify import verify_password

models.Base.metadata.create_all(bind=engine)


app = FastAPI()

SECRET_KEY = "e73e8cdd011fda919e486d8f4ba291dd250c9ca0450061203b03731aa8234da3"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60


def get_db() -> Session:
    with SESSION_LOCAL() as db:
        yield db


def authenticate_user(email: str, password: str, db: Session) -> models.User:
    user_db = crud_user.UserCRUDOperations(db=db)
    user_selected = user_db.get_user_by_email(email)

    if not user_selected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user does not exist")

    if not verify_password(password, user_selected.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="password is wrong try again")

    return user_selected


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_access_token_from_header(x_token: str = Header()) -> str:
    if x_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token is missing"
        )
    return x_token


async def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY,
                             algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


@app.post("/user_create/", response_model=schemas.User | None)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.User | None:
    user_db = crud_user.UserCRUDOperations(db=db)
    user_selected = user_db.get_user_by_email(user.email)

    if user_selected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user exists, try again")

    user = user_db.user_create(user)

    if isinstance(user, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=user["message"])

    return user


@app.delete("/delete_user/{user_id}")
async def delete_user(user_id: str, x_token: str = Depends(get_access_token_from_header), db: Session = Depends(get_db)):
    user_db = crud_user.UserCRUDOperations(db=db)
    get_payload = await verify_token(x_token)

    if not get_payload["role"] == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="only admin can delete users")

    if not user_db.remove_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="user does not exist")

    return {"message": "user successfully was deleted"}


@app.post("/token", response_model=schemas.Token)
async def login_user(user: schemas.UserLogIn, db: Session = Depends(get_db)) -> schemas.Token:
    email = user.email
    password = user.password
    user = authenticate_user(email, password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}, expires_delta=access_token_expires
    )

    return schemas.Token(access_token=access_token, token_type="jwt")


@app.get("/all_users", response_model=List[schemas.User])
async def get_all_users(x_token: str = Depends(get_access_token_from_header), db=Depends(get_db)) -> schemas.User:
    get_payload = await verify_token(x_token)
    user_db = crud_user.UserCRUDOperations(db=db)

    if not get_payload["role"] == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="only for admins are allowed")

    return user_db.get_all_users()


@app.post("/create_post", response_model=schemas.Post)
async def create_post(post: schemas.PostCreate, db: Session = Depends(get_db), x_token: str = Depends(get_access_token_from_header)):
    get_payload = await verify_token(x_token)
    post_db = crud_post.PostCRUDOperations(db=db, user_id=get_payload["sub"])

    if not get_payload["role"] in ("custom", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="admin can not create a post")
    else:
        post = post_db.create_post(post)

    if not post:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="post  with such kind of title already exists")

    return post


@app.patch("/update_post/{post_id}", response_model=schemas.PostUpdate)
async def update_post(post_id: str, post: schemas.PostUpdate, db: Session = Depends(get_db), x_token: str = Depends(get_access_token_from_header)):
    get_payload = await verify_token(x_token)
    post_db = crud_post.PostCRUDOperations(
        db=db, post_id=post_id, user_id=get_payload["sub"])

    if not get_payload["role"] in ("custom", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="admin can not update a post")

    return post_db.update_post(post)


@app.delete("/delete_post/{post_id}")
async def delete_post(post_id: str, db: Session = Depends(get_db), x_token: str = Depends(get_access_token_from_header)):
    get_payload = await verify_token(x_token)
    post_db = crud_post.PostCRUDOperations(
        db=db, post_id=post_id, user_id=get_payload["sub"])

    is_deleted = post_db.delete_post()

    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="could not find matched post")

    return {"message": "post successfully deleted"}


@app.get("/all_posts", response_model=List[schemas.Post])
async def get_all_posts(db: Session = Depends(get_db)):
    post_db = crud_post.PostCRUDOperations(db=db)
    return post_db.get_all_posts()


@app.get("/post/{post_id}", response_model=schemas.Post | None)
async def get_post_by_id(post_id: str, db: Session = Depends(get_db)):
    post_db = crud_post.PostCRUDOperations(db=db, post_id=post_id)
    post = post_db.get_post_by_id()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="post was not found")

    return post


@app.post("/add_to_watch_list/{post_id}", response_model=schemas.WatchList)
async def add_to_watch_list(post_id: str, db: Session = Depends(get_db), x_token: str = Depends(get_access_token_from_header)):
    payload = await verify_token(x_token)
    post_db = add_to_watchlist.AddToWatchList(
        post_id=post_id, user_id=payload["sub"], db=db)

    return post_db.add_to_watchlist()


@app.post("/remove_from_watch_list/{post_id}", response_model=schemas.WatchList)
async def remove_from_watch_list(post_id: str, db: Session = Depends(get_db), x_token: str = Depends(get_access_token_from_header)):
    payload = await verify_token(x_token)
    post_db = add_to_watchlist.AddToWatchList(
        post_id=post_id, user_id=payload["sub"], db=db)

    return post_db.remove_post_from_watchlist()


@app.get("/saved_posts", response_model=schemas.WatchList)
async def get_saved_posts(db: Session = Depends(get_db), x_token: str = Depends(get_access_token_from_header)):
    get_payload = await verify_token(x_token)
    post_db = add_to_watchlist.AddToWatchList(
        user_id=get_payload["sub"], db=db)
    return post_db.get_watchlist()


@app.post("/leave_comment", response_model=schemas.Comment)
async def leave_comment(comment: schemas.CommentCreate, x_token: str = Depends(get_access_token_from_header), db: Session = Depends(get_db)):
    get_payload = await verify_token(x_token)
    comment_db = crud_comment.CommentCRUDOperations(
        db=db, author_id=get_payload["sub"])

    return comment_db.create_comment(comment)


@app.get("/post/{post_id}/comments/", response_model=List[schemas.Comment] | None)
async def get_all_comments_by_post_id(post_id: str, x_token: str = Depends(get_access_token_from_header), db: Session = Depends(get_db)):
    comment_db = crud_comment.CommentCRUDOperations(db=db, post_id=post_id)
    return comment_db.get_all_comments_by_post_id()


@app.delete("/comment_delete/{comment_id}")
async def delete_comment(comment_id: str, x_token: str = Depends(get_access_token_from_header), db: Session = Depends(get_db)):
    get_payload = await verify_token(x_token)
    comment_db = crud_comment.CommentCRUDOperations(db=db)

    if not get_payload["role"] == "manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="only managers can delete comments")

    if not comment_db.delete_comment_by_id(comment_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="comment was not found")

    return {"message": "comment successfully was deleted"}


@app.post("/post_like_handler")
async def post_like_handler(like_handler: schemas.LikePost, x_token: str = Depends(get_access_token_from_header), db: Session = Depends(get_db)):
    get_payload = await verify_token(x_token)
    like_db = liking_posts.UserPostsLiking(
        db=db, post_id=like_handler.post_id, user_id=get_payload["sub"])
    is_done = like_db.handle_likes(like_handler.operation)

    if not is_done:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="user or post does not exist, make sure you are passed correct user's token or post id")

    return {"message": "operation done successfully"}


@app.post("/reset_password")
async def reset_password(password: schemas.UserUpdatePassword, x_token: str = Depends(get_access_token_from_header), db: Session = Depends(get_db)):
    get_payload = await verify_token(x_token)
    user_db = crud_user.UserCRUDOperations(db=db)
    user_hashed = user_db.update_password(password, get_payload["sub"])

    if not user_hashed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="password is wrong")

    return {"message": "successfully resettled password"}
