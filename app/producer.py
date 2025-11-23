from app.rabbimq import Rabbitmq

def produce_task(task: str):
    rabbitmq_instance = Rabbitmq()
    channel = rabbitmq_instance.get_channel()
    
    if channel:
        channel.queue_declare(queue="tasks", durable=True)
        channel.basic_publish(exchange="", routing_key="tasks", body=task)