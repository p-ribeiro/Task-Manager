import json
import time
import requests
from app.enums.task_status import TaskStatus


def test_functional():
    url = "http://127.0.0.1:8000"
    
    ## send a task via api
    task = {
        "operation": "reverse",
        "data": "This should be reversed"
    }
    resp = requests.post(f"{url}/submit-task", json=task)
    assert resp.status_code == 201
    data = resp.json()
    task_id = data["task_id"]
    
    
    ## check task status
    resp = requests.get(f"{url}/task/{task_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in [TaskStatus.QUEUED, TaskStatus.PROCESSING]
    
    # waits until task is "finished"
    while True:
        print(f"\nChecking status for {task_id}...")
        
        resp = requests.get(f"{url}/task/{task_id}")
        assert resp.status_code == 200
        
        data = resp.json() 
        if data["status"] == TaskStatus.FINISHED:
            break
        
        print(f"Task is not finished. Status: {data['status']}")
        # sleeping for 2 seconds
        time.sleep(2)
    
    ## retrives task from redis
    print("Result found")
    print(data["result"])
    