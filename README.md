# Actual Budget HTTP Wrapper

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org) ![Maintenance](https://img.shields.io/maintenance/yes/2025)

A simple FastAPI-based wrapper that allows you to interact with [Actual Budget](https://actualbudget.org/) via a minimal HTTP API, forked from [actual-api-rest](https://github.com/tmllull/actual-api-rest). Uses the [actualpy](https://github.com/bvanelli/actualpy) module under the hood.

## Fork changes

- Can now get budget and accounts info
- Requests instance password and filename instead of storing them in environment variables
- Removed useless API key verification
- More under the hood changes

## Setup

Create a `.env` file with the following variable:

```env
ACTUAL_HOST="https://your-actual-budget-host.com"
```

## Usage

### Using Docker

```bash
docker compose up --build --detach
```

### Local install
> [!NOTE]  
> Untested by me but it should probably work.
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## API Reference

**Headers:**

```
Content-Type: application/json
x-actual-password: your_actual_password
x-actual-encryption-password: encryption_password_if_present
x-actual-file: file_name_or_id
```

### `POST /transaction/add`

Adds a new transaction.

**Body:**

```json
{
  "amount": 12.99,
  "payee": "Spotify",
  "account": "Bank",
  "category": "Subscriptions",
  "notes": "Monthly plan",
  "payment": true,
  "cleared": true
}
```

### `GET /budget/{year}/{month}`

Gets the specified month's budget in JSON format.

### `GET /budget/current`

Gets the current month's budget in JSON format.

### `GET /accounts/balances`

Gets the current account balances in JSON format.

## License

This project is licensed under the [MIT License](LICENSE).
