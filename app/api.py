import json
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated, Optional
from uuid import uuid7

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis

from app.database import create_db_and_tables
from app.enums.task_status import TaskStatus
from app.models import RegisterForm, Task, Token, User
from app.producer import produce_task
from app.utils.authentication import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SessionDep,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis(host="localhost", port=6379, decode_responses=True)
    create_db_and_tables()
    yield
    await app.state.redis.aclose()


app = FastAPI(lifespan=lifespan)


@app.post("/user/register", status_code=status.HTTP_201_CREATED)
async def register_user(data: RegisterForm, session: SessionDep) -> None:
    hashed_password = get_password_hash(data.password)
    user = User(
        username=data.username,
        password=hashed_password,
        email=data.email,
        full_name=data.full_name,
    )

    session.add(user)
    session.commit()
    session.refresh(user)


@app.post("/user/login")
async def login_for_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


def get_redis() -> Redis:
    return app.state.redis


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.post("/submit-task", status_code=status.HTTP_201_CREATED)
async def submit_task(
    task: Task,
    current_user: Annotated[User, Depends(get_current_active_user)],
    redis: Redis = Depends(get_redis),
):
    # generate task-id
    task_uuid = str(uuid7())
    data = {"status": TaskStatus.QUEUED, "result": ""}
    data_json = json.dumps(data)

    # store status in Redis
    await redis.set(f"{task_uuid}", data_json)

    # send data to rabbimq
    task.id = task_uuid
    produce_task(task.model_dump_json())

    return {
        "task_id": task_uuid,
        "status": data["status"],
        # "token": token
    }


@app.get("/task/{task_id}")
async def get_task(
    task_id: str, response: Response, redis: Redis = Depends(get_redis)
) -> Optional[dict]:
    task = await redis.get(task_id)
    if not task:
        response.status_code = status.HTTP_204_NO_CONTENT
        return

    try:
        task_json = json.loads(task)
    except (TypeError, json.JSONDecodeError):
        # stored value is not JSON (e.g. a plain string) — return it as status
        return {"status": task, "result": ""}

    return {
        "status": task_json["status"],
        "result": task_json["result"],
        # "token": token
    }
