# Task Manager — Portfolio Project

This is a portfolio project implemented as a simple asynchronous task manager. It demonstrates building a small service with FastAPI, Redis for state, RabbitMQ for background task queuing, and minimal auth for protected endpoints. The project is intended for job prospection and to showcase backend architecture, async integration, and testing.

## Python Version
3.14

## Tools
- FastApi
- Redis
- RabbitMQ
- Docker

## Badges (version / modules)
- ![python](https://img.shields.io/badge/python-3.14-blue) 
- ![fastapi](https://img.shields.io/badge/FastAPI-%5E0.121.2-lightgrey)
- ![redis](https://img.shields.io/badge/Redis-%3E%3D7.1.0-orange)
- ![rabbitmq](https://img.shields.io/badge/RabbitMQ-%3E%3D3.0-yellowgreen)
- ![pytest](https://img.shields.io/badge/pytest-%3E%3D9.0.1-brightgreen)

## Stack
- FastAPI — web framework and API surface
- Redis — lightweight datastore for task status/results
- RabbitMQ — message broker for background task processing
- SQLModel / SQLite — simple user storage and auth examples
- Tests: pytest and fastapi.TestClient
- Other libs: pika, python-dotenv, pwdlib, pyjwt

## Modules / dependencies
See pyproject.toml for exact dependency pins. Key modules used:
- fastapi, redis, pika, requests, pytest, sqlmodel, pwdlib, pyjwt, python-dotenv

## Quick start (development)
1. Bring up Redis and RabbitMQ (docker-compose is provided):
   ```bash
   docker compose up -d
   ```
2. Run the API in development mode:
   ```bash
   uv fastapi dev app/api.py
   ```
3. Run the consumer:
  ```bash
  uv run python app/consumer.py
  ```
4. Run tests:
   ```bash
   uv run pytest
   ```

## API — short overview
- **GET** `/health`
  - Simple health check returning `{"status": "ok"}`.

- **POST** `/user/register`
  - Register a new user (username, password, email, full_name).
  - Returns 201 on success.

- **POST** `/user/login`
  - OAuth2 password grant to obtain a Bearer token.
  - Form fields: username, password.
  - Returns access_token.

- **POST** `/submit-task`
  - Protected endpoint (Bearer token required).
  - Body: `{ "operation": "reverse"|"count_words"|"count_letters"|"uppercase"|"lowercase", "data": "<string>" }`
  - Returns 201 with `{"task_id": "<id>", "status": "Queued"}`.

- **GET** `/task/{task_id}`
  - Get task status/result.
  - If no task found returns 204 No Content.
  - Otherwise returns `{"status": "<Queued|Processing|Finished>", "result": "<result or empty>"}`.

## Notes on testing and consumer
- Unit tests cover the task operations and the process_message logic (consumer) without requiring a live RabbitMQ broker.
- The actual consumer connects to RabbitMQ and processes messages by reading task payloads, computing results and updating Redis.

## Contributing / extension ideas
- Add more operations or allow custom worker pools.
- Replace sqlite with a full DB for user management and migrations.
- Add integration tests using ephemeral Docker containers for Redis/RabbitMQ.

## License
- Add your preferred license if publishing.
