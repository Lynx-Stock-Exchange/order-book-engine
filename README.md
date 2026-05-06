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


## Order Book & Matching Engine (Issue #2)

### Overview

This component implements an in-memory order book and matching engine per the exchange specification §6.3.

---

### Order Book

An in-memory `OrderBook` is maintained per ticker.

Supported operations:

* `add(order)` – add new order
* `remove(order_id)` – remove order
* `get()` – retrieve current orders
* `top_levels()` – best bid / ask prices
* `pressure()` – buy vs sell imbalance
* `iter_matchable(current_price)` – yields orders eligible for execution

---

### Matching Logic

Matching follows the rules defined in §6.3 of the specification:

* **LIMIT BUY**

  * Executed if `limit_price >= current_price`
  * Execution price = `limit_price`

* **LIMIT SELL**

  * Executed if `limit_price <= current_price`
  * Execution price = `limit_price`

* **MARKET orders**

  * Executed immediately at `current_price`
  * Do not depend on limit conditions

---

###  Partial Fill Behaviour

The engine simulates limited market depth:

* Each tick has a configurable liquidity cap (`max_liquidity_per_tick`)
* Orders may be partially filled if liquidity is insufficient
* Remaining quantity stays active and continues in subsequent ticks

This implements the behaviour described in §6.5 of the specification.

---

### Fill Execution

* Supports **partial fills across multiple ticks**
* Automatically updates:

  * `filled_quantity`
  * `status` (`PENDING → PARTIALLY_FILLED → FILLED`)
* Calculates **weighted average fill price**

---

###  No I/O

* Fully in-memory
* No database or external dependencies
* Deterministic and testable

---

###  Test Coverage

The following scenarios are validated:

* MARKET order execution
* LIMIT BUY trigger / no-trigger
* LIMIT SELL trigger
* Partial fill within one tick
* Multi-tick completion (second partial)
* Competing BUY/SELL orders sharing liquidity
* Weighted average price calculation
* CANCELLED orders ignored


---

---

# Execution Persistence 

## Overview

The matching engine itself remains fully in-memory, while execution results are persisted into PostgreSQL after each market tick.

---

## execution_service.py

`execution_service.py` acts as the orchestration layer of the Order Book Engine.

It coordinates the complete execution lifecycle:

```text
Load open orders from database
        ↓
Build in-memory OrderBook
        ↓
Run matching engine
        ↓
Generate trades
        ↓
Persist trades into database
        ↓
Update order execution state



