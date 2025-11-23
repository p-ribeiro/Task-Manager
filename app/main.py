from contextlib import asynccontextmanager
import json
from typing import Optional
from fastapi import Depends, FastAPI, Response, status
from pydantic import BaseModel
from uuid import uuid7
from redis.asyncio import Redis

from app.producer import produce_task

class Task(BaseModel):
    operation: str
    data: str
    id: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis(host="localhost", port=6379, decode_responses=True)
    yield
    await app.state.redis.aclose()

app = FastAPI(lifespan=lifespan)
redis_client: Redis | None


def get_redis() -> Redis:
    return app.state.redis

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/submit-task", status_code=status.HTTP_201_CREATED)
async def submit_task(task: Task, redis: Redis = Depends(get_redis)):
    # generate task-id
    task_uuid = str(uuid7())
    data = {
        "status": "Queued",
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
        "status": data["status"]
    }


@app.get("/task/{task_id}")
async def get_task(
    task_id: str,
    response: Response,
    redis: Redis = Depends(get_redis)
    ) -> Optional[dict]:
    
    
    task = await redis.get(task_id)
    task_json = json.loads(task)
    
    if not task:
        response.status_code = status.HTTP_204_NO_CONTENT
        return 
    
    return {
        "status": task_json["status"],
        "result": task_json["result"]
    }
    