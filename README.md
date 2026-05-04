# order-book-engine
The heart of the Stock Exchange system. The Order Book Engine is a critical, Python-based service responsible for trade matching algorithms. It processes the incoming order flow from the Broker Platforms, maintains the central order book, and ensures the efficient and accurate execution of BUY and SELL matches. 
**Made by Team 3.**

# Order Book Engine – Project Skeleton

## Description

This repository contains the initial project setup, including:

* Python 3.12 environment
* PostgreSQL connection pool
* Environment-based configuration using `.env`

---

## Requirements

* Python 3.12
* Docker (optional, for local PostgreSQL)

---

## Project Structure

```
order-book-engine/
│── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   └── test_connection.py
│
│── .env.example
│── requirements.txt
│── docker-compose.yml
│── README.md
```

---

## Setup (Local)

### 1. Create virtual environment

```bash
python -m venv venv
```

### 2. Activate environment

**Git Bash / Linux / Mac:**

```bash
source venv/Scripts/activate
```

**Windows CMD:**

```bash
venv\Scripts\activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Example configuration:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=exchange
DB_USER=postgres
DB_PASSWORD=postgres
```

---

## Running PostgreSQL (Docker)

```bash
docker-compose up -d
```

---

## Test Database Connection

```bash
python -m app.test_connection
```

---

## Expected Output

```
Connection OK: (1,)
```

---


