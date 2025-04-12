# Django Banking API

A simple and modular banking API built with Django, supporting account management and secure transaction processing.

## Features

- Account creation and balance tracking
- Deposit and withdrawal transactions
- Transaction rollback support
- Dockerized setup for easy deployment
- Admin interface via Django Admin

---

## Prerequisites

- Docker
- Docker Compose

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <project-directory>
```

### 2. Build and Start the Containers

```bash
docker-compose up --build
```

This will:

- Build the Docker image
- Apply database migrations
- Collect static files
- Start the development server on http://localhost:8000

---

## Creating a Superuser and Accessing the Admin Panel

Before using the API, you must create a Django superuser. This user can log in, obtain tokens (if authentication is required), and manage the system through the admin interface.

### 1. Open a shell inside the running container

```bash
docker exec -it <your_container_name> bash
```

Replace `<your_container_name>` with the actual name, e.g., `banking_api_web`.

### 2. Create a superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to enter a username, email, and password.

### 3. Access the Admin Panel

Visit: http://localhost:8000/admin/ and log in with the superuser credentials.

---

## API Access Notes

To access the secured endpoints, you will typically need to:

1. **Create a superuser** (see above).
2. **Authenticate** using login credentials or obtain an authentication token depending on how the API is secured (e.g., using JWT or session-based authentication).
3. **Use the token** in the `Authorization` header for future API requests, for example:

```bash
-H "Authorization: Token your_token_here"
```

---

## API Endpoints

### Accounts

- `POST   /api/accounts/` — Create a new account
- `GET    /api/accounts/{id}/` — Retrieve account details
- `GET    /api/accounts/{id}/balance/` — Get account balance
- `GET    /api/accounts/{id}/transactions/` — List all transactions for an account

### Transactions

- `POST   /api/transactions/` — Create a transaction (deposit or withdrawal)
- `GET    /api/transactions/` — List all transactions
- `POST   /api/transactions/{id}/rollback/` — Roll back a transaction

---

## Example Requests

### Create an Account

```bash
curl -X POST http://localhost:8000/api/accounts/ \
  -H "Content-Type: application/json" \
  -d '{"public_key": "abc123", "private_key": "secret"}'
```

### Make a Deposit

```bash
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Content-Type: application/json" \
  -d '{"account": 1, "amount": "10.00", "transaction_type": "deposit"}'
```

### Check Account Balance

```bash
curl http://localhost:8000/api/accounts/1/balance/
```

---

## Development Notes

- Volume mounts allow live code changes during development (no rebuild needed).
- For production deployment:
  - Disable volume mounts
  - Use a production WSGI server like Gunicorn
  - Configure proper Django security settings (e.g., `ALLOWED_HOSTS`, `DEBUG=False`, secure secret key)

---

## Stopping the Application

```bash
docker-compose down
```
