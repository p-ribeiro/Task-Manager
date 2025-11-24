from contextlib import asynccontextmanager
import json
from typing import Optional, Annotated
from fastapi import Depends, FastAPI, Response, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from uuid import uuid7
from redis.asyncio import Redis

from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.database import create_db_and_tables, get_session
from app.models import User
from app.producer import produce_task
from app.enums.task_status import TaskStatus
from app.enums.task_operations import TaskOperations

SECRET_KEY = "72df37c496cff8090711a951b7f474d1e00d4c2d5a93db887c00d1c2e5b3d640"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserInDB(User):
    hashed_password: str

class Task(BaseModel):
    operation: TaskOperations
    data: str
    id: Optional[str] = None

class RegisterForm(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None

SessionDep = Annotated[Session, Depends(get_session)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")
password_hash = PasswordHash.recommended()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis(host="localhost", port=6379, decode_responses=True)
    create_db_and_tables()
    yield
    await app.state.redis.aclose()


app = FastAPI(lifespan=lifespan)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

def get_user_by_username(session: Session, username: str) -> User:
    stmt = select(User).where(User.username == username)
    result = session.exec(stmt).first()
    
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return result

def authenticate_user(username: str, password: str, session: SessionDep) -> Optional[User]:
    user = get_user_by_username(session, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(
    session: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username = username)
    
    except InvalidTokenError:
        raise credentials_exception
    
    if not token_data.username:
        raise credentials_exception
    
    user = get_user_by_username(session, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/user/register", status_code=status.HTTP_201_CREATED)
async def register_user(data: RegisterForm, session: SessionDep) -> None:
    hashed_password = get_password_hash(data.password)
    user = User(
        username=data.username,
        password=hashed_password,
        email=data.email,
        full_name=data.full_name
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)


@app.post("/user/login")
async def login_for_access_token(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
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
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user



@app.post("/submit-task", status_code=status.HTTP_201_CREATED)
async def submit_task( 
    task: Task,
    current_user: Annotated[User, Depends(get_current_active_user)], 
    redis: Redis = Depends(get_redis),
    ):
    # generate task-id
    task_uuid = str(uuid7())
    data = {
        "status": TaskStatus.QUEUED,
        "result": ""
    }
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
    task_id: str,
    response: Response,
    # token: Annotated[str, Depends(oauth2_scheme)],
    redis: Redis = Depends(get_redis)
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
