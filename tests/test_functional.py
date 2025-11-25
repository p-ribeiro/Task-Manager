import requests
from fastapi import status

from app.enums.task_operations import TaskOperations


def test_functional():
    url = "http://127.0.0.1:8000"

    task = {"operation": TaskOperations.REVERSE.value, "task": "Reverse this text"}

    ## User tries to send task via api without registering
    ## expects error
    resp = requests.post(f"{url}/submit-task", json=task)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    ## User registers
    user_register_data = {
        "username": "johndoe",
        "password": "mypass",
        "email": "jdoe@example.com",
        "full_name": "John Doe",
    }
    resp = requests.post(f"{url}/user/register", json=user_register_data)
    assert resp.status_code == status.HTTP_201_CREATED

    ## User logs in
    resp = requests.post(f"{url}/user/login", data=user_register_data)
    assert resp.status_code == status.HTTP_200_OK
    resp_json = resp.json()
    assert "access_token" in resp_json
    access_token = resp_json["access_token"]

    ## User sends task via API
    header = {"Authorization": f"Bearer {access_token}"}
    task = {"operation": "reverse", "data": "This should be reversed"}
    resp = requests.post(f"{url}/submit-task", json=task, headers=header)
    assert resp.status_code == status.HTTP_201_CREATED

    ## User waits for task to be completed

    ## Checks if response is expected

    # ## send a task via api
    # resp = requests.post(f"{url}/submit-task", json=task)
    # assert resp.status_code == 201
    # data = resp.json()
    # task_id = data["task_id"]

    # # waits until task is "finished"
    # while True:
    #     print(f"\nChecking status for {task_id}...")

    #     resp = requests.get(f"{url}/task/{task_id}")
    #     assert resp.status_code == 200

    #     data = resp.json()
    #     if data["status"] == TaskStatus.FINISHED:
    #         break

    #     print(f"Task is not finished. Status: {data['status']}")
    #     # sleeping for 2 seconds
    #     time.sleep(2)

    # ## retrives task from redis
    # assert data["result"] == task["data"][::-1]
