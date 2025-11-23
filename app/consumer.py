import json
import time
from app.rabbimq import Rabbitmq
from redis import Redis


def process_message(ch, method, properties, body):
    
    print("Starting to consumer message")
    message = body.decode() if isinstance(body, (bytes, bytearray)) else body
    
    redis = Redis(host="localhost", port=6379, decode_responses=True)
    data = {
        "status": "Processing",
        "result": ""
    }
    
    task = json.loads(message)
    task_id = task["id"]
    redis.set(f"{task_id}", json.dumps(data))
    
    operation = task["operation"]
    
    time.sleep(10)
    result = ""
    if operation == "reverse":
        result = task["data"][::-1]
    
    data["status"] = "Finished"
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