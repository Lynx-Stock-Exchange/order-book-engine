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



The exchange fee rate is configurable through environment variables and is applied on every executed trade.

---

## OrderSubmissionService

`order_submission_service.py` handles incoming order validation before orders enter the execution pipeline.

Responsibilities:

* validating incoming orders
* market-open validation
* structured rejection handling
* persisting accepted orders into PostgreSQL

The service raises standardized `OrderRejected` exceptions for invalid or rejected orders.

Example rejection codes include:

* `MARKET_CLOSED`
* `INVALID_QUANTITY`
* `INVALID_LIMIT_PRICE`
* `INVALID_ORDER_TYPE`

---

# Kafka Integration

The Order Book Engine integrates with Apache Kafka for asynchronous market data ingestion and event publishing.

---

## Kafka Consumer

The engine consumes live market price updates from:


For every incoming tick:

1. open orders are loaded from PostgreSQL
2. an in-memory order book is reconstructed
3. the matching engine executes eligible orders
4. trades are persisted
5. order statuses are updated
6. execution events are published

---

## Kafka Producer

The engine publishes events to multiple Kafka topics.

### trade_executed

Published whenever a trade is successfully executed.

Example:

```json
{
  "type": "TRADE_EXECUTED",
  "payload": {
    "trade_id": "...",
    "order_id": "...",
    "instrument_id": "AAPL",
    "side": "BUY",
    "quantity": "10",
    "price": "210.50",
    "exchange_fee": "2.10"
  }
}
```

---

### order_updates

Published whenever an order state changes after execution.

Example:

```json
{
  "type": "ORDER_UPDATE",
  "payload": {
    "order_id": "...",
    "status": "PARTIALLY_FILLED",
    "filled_quantity": "5",
    "average_fill_price": "210.50",
    "exchange_fee": "1.05"
  }
}
```




### Create Order

```http
POST /orders
```

Example request:

```json
{
  "platform_user_id": "user1",
  "instrument_type": "STOCK",
  "instrument_id": "AAPL",
  "order_type": "LIMIT",
  "side": "BUY",
  "quantity": 10,
  "limit_price": 200
}
```

---

### Get Order

```http
GET /orders/{order_id}
```

Returns full order execution state.

---

### Cancel Order

```http
DELETE /orders/{order_id}
```

Cancels a pending or partially filled order.


### Open Market

```http
POST /admin/market/open
```

---

### Close Market

```http
POST /admin/market/close
```

Behaviour:

* LIMIT orders → EXPIRED
* MARKET orders → REJECTED

---

### Market Status

```http
GET /admin/market/status
```

---

# Database Migrations

Run migrations manually:

```bash
python -m app.migrations.run_migration
```

This creates:

* `orders`
* `trades`

tables and indexes.

---

# Running the Engine

## Start PostgreSQL + Kafka

```bash
docker compose up -d
```

---

## Start FastAPI

```bash
uvicorn app.main:app --reload
```

---

## Start Kafka Consumer

```bash
python -m run_consumer
```

---

# Error Handling

The engine uses structured rejection responses.

Example:

```json
{
  "error": {
    "code": "INVALID_LIMIT_PRICE",
    "message": "LIMIT orders require positive limit_price.",
    "details": {}
  }
}
```

---

# Exchange Rules Implemented

The engine currently supports:

* MARKET orders
* LIMIT orders
* BUY and SELL sides
* partial fills
* weighted average fill pricing
* configurable liquidity per tick
* configurable exchange fees
* market open / close handling
* order cancellation
* order expiration
* Kafka-based event publishing

  

## Market Statistics

Retrieve aggregated exchange statistics calculated from persisted trade data.

### Endpoint

```http
GET /market/stats
```

### Example Response

```json
{
  "total_revenue": "8.0000",
  "total_trades": 4,
  "total_volume": "40.0000"
}
```

Returns:

* total exchange revenue
* total executed trades
* total traded volume

---

## Market Tick Simulation (Admin)

Publish simulated stock price ticks into Kafka for testing and execution triggering.

### Endpoint

```http
POST /admin/market/tick
```

### Example Request

```json
{
  "ticker": "AAPL",
  "price": 190
}
```

### Example Response

```json
{
  "status": "PUBLISHED",
  "payload": {
    "ticker": "AAPL",
    "price": 190
  }
}
```

This endpoint is mainly intended for:

* local development
* execution testing
* Kafka event simulation
* demo scenarios


