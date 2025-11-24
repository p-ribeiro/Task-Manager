import json
import time
from app.rabbimq import Rabbitmq
from redis import Redis

from app.enums.task_status import TaskStatus
from app.enums.task_operations import TaskOperations

def do_op(operation: str, data: str) -> str:
    op = operation.lower() if isinstance(operation, str) else ""
    
    match op:
        case TaskOperations.REVERSE.value:
            return data[::-1]
        case TaskOperations.COUNT_WORDS.value:
            return str(len(data.split()))
        case TaskOperations.COUNT_LETTERS.value:
            words = data.split()
            letters = 0
            for word in words:
                letters += len(word)
            return str(letters)
        case TaskOperations.UPPERCASE.value:
            return data.upper()
        case TaskOperations.LOWERCASE.value:
            return data.lower()
        case _:
            return ""    


def process_message(ch, method, properties, body):
    
    message = body.decode() if isinstance(body, (bytes, bytearray)) else body
    
    redis = Redis(host="localhost", port=6379, decode_responses=True)
    data = {
        "status": TaskStatus.PROCESSING,
        "result": ""
    }
    
    task = json.loads(message)
    task_id = task["id"]
    redis.set(f"{task_id}", json.dumps(data))
    
    operation = task["operation"]
    result = do_op(operation, task["data"])

    data["status"] = TaskStatus.FINISHED
    data["result"] = result
    redis.set(f"{task_id}", json.dumps(data))
    
    if method:
        ch.basic_ack(delivery_tag=method.delivery_tag)    
    

def consumer():
    rabbimq = Rabbitmq()
    channel = rabbimq.get_channel()
    
    if channel:
        channel.queue_declare(queue="tasks", durable=True)
        channel.basic_consume(queue="tasks", on_message_callback=process_message)
        channel.start_consuming()

if __name__ == "__main__":
    consumer()