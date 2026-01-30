# Multiple Web Protocols

[![CI (lint + test)](https://github.com/blitznihar/multiple-web-protocols/actions/workflows/pylint.yml/badge.svg)](https://github.com/blitznihar/multiple-web-protocols/actions/workflows/pylint.yml)
[![codecov](https://codecov.io/github/blitznihar/multiple-web-protocols/graph/badge.svg?token=WQj9qZBFhi)](https://codecov.io/github/blitznihar/multiple-web-protocols)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Last Commit](https://img.shields.io/github/last-commit/blitznihar/multiple-web-protocols)
![License](https://img.shields.io/github/license/blitznihar/multiple-web-protocols?cacheSeconds=0)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

This repository is a learning/demo project that implements a simple **Customer** service backed by **MongoDB**, exposed over multiple web protocols.

The goal is to show how the same domain and persistence layer (a small customer database) can be accessed through different integration styles:

- A fully implemented **gRPC** service
- A fully implemented **REST** API (FastAPI)
- A fully implemented **SOAP** service (using Spyne)
- A fully implemented **WebSocket** service for real-time event broadcasting
- A fully implemented **Webhook** service for event-driven HTTP callbacks
- A fully implemented **Webhook Receiver** service for receiving and logging webhooks
- Planned/placeholder entry points for **GraphQL**, **MCP** (Model Context Protocol), **AMQP**, **MQTT**, and **SSE**

All variants share the same MongoDB-backed `CustomerDB` abstraction for CRUD operations.

## Architecture

- **Domain model**
	- `db/customer.py` defines a `Customer` Pydantic model (with an optional `Address`).
	- `db/address.py` holds the address model used by `Customer`.

- **Persistence layer**
	- `db/customer_db.py` wraps a `pymongo.MongoClient` and exposes:
		- `create_customer(customer: dict) -> str`
		- `get_customer_by_id(customerid: str) -> dict | None`
		- `list_customers() -> list[dict]`
		- `update_customer(customerid: str, updates: dict) -> bool`
		- `delete_customer(customerid: str) -> bool`

- **Protocols**
	- **gRPC** (implemented)
		- Service definition in `grpc_service/proto/customer.proto`.
		- Generated code in `grpc_service/customerpb/`.
		- Server implementation in `grpc_service/server.py` wrapping `CustomerDB`.
		- Exposes CRUD RPCs: `CreateCustomer`, `GetCustomerById`, `UpdateCustomer`, `DeleteCustomer`.
	- **REST API** (implemented)
		- FastAPI application in `rest/app.py` exposing JSON endpoints over HTTP.
		- Uses the same `CustomerDB` to back CRUD operations.
		- Endpoints:
			- `GET /health` – basic app + MongoDB health-check.
			- `GET /customers` – list all customers.
			- `GET /customers/{customerid}` – fetch a single customer.
			- `POST /customers` – create a new customer (409 on duplicate `customerid`).
			- `PUT /customers/{customerid}` – update basic fields and nested address.
			- `DELETE /customers/{customerid}` – delete a customer.
	- **SOAP** (implemented)
		- Spyne-based SOAP service in `soap/customer_service.py` exposing WSDL and SOAP operations.
		- Uses the same `CustomerDB` for CRUD operations.
		- Operations:
			- `create_customer` – create a new customer.
			- `get_customer` – fetch a customer by ID.
			- `update_customer_email` – update a customer's email.
			- `delete_customer` – delete a customer by ID.
- **WebSocket** (implemented)
	- WebSocket service in `websocket/service.py` providing real-time event broadcasting via Kafka.
	- Consumes events from Kafka topic `player-events` and broadcasts to connected WebSocket clients.
	- Endpoint: `ws://localhost:8068/ws`
- **Webhook** (implemented)
	- Webhook dispatcher service in `webhook/main.py` for event-driven HTTP callbacks.
	- Manages webhook subscriptions and dispatches events to registered URLs based on event types.
	- Uses MongoDB for subscription storage and Kafka for event consumption.
	- Endpoints: `/health`, `/webhooks` (GET, POST, DELETE)
- **Webhook Receiver** (implemented)
	- Simple webhook receiver service in `webhook_receiver/service.py` for receiving and logging incoming webhooks.
	- Logs headers and body of received webhook payloads.
	- Endpoint: `POST /hook`
- **GraphQL** (implemented)
	- GraphQL API implemented using FastAPI and Strawberry GraphQL, exposing the same `Customer` domain.
	- Schema includes queries: `getCustomer(customerid: String!)` and `listCustomers`.
	- Endpoint: `/graphql` (GraphQL playground available).
	- Uses the same `CustomerDB` for persistence.
	- **MCP** (implemented)
	- Model Context Protocol server implemented using FastMCP, exposing customer CRUD operations and event publishing.
	- Tools: `customer_init_indexes`, `customer_create`, `customer_get`, `customer_update`, `customer_delete`, `customer_list`, `player_publish_score_updated`, `player_publish_event`.
	- Runs over HTTP transport.
	- Uses async MongoDB client and Kafka producer for events.
	- **AMQP** (placeholder)
		- `amqp/__main__.py` is a placeholder for AMQP-based messaging.
	- **MQTT** (placeholder)
		- `mqtt/__main__.py` is a placeholder for MQTT-based messaging.
	- **SSE** (implemented)
		- Server-Sent Events service implemented using FastMCP with SSE transport, providing the same MCP tools over Server-Sent Events.

- **Top-level demo**
	- `__main__.py` demonstrates the raw usage of `CustomerDB` (create, read, list, update, delete) when you run the project directly.

- **Infrastructure**
	- `docker-compose.yml` starts a local **MongoDB 7** instance with:
		- Database: `customerdb`
		- Initial data loaded from `data/customer.json` via `data/script/mongo-init.js`.

## Requirements

- Python ≥ 3.11 (project targets modern Python and uses type hints and Pydantic v2).
- A running MongoDB instance (or the included Docker Compose setup).

Recommended tooling (already configured in the project):

- [uv](https://github.com/astral-sh/uv) for dependency and environment management.
- `ruff`, `pylint`, and `pytest` for linting and testing.

## Getting Started

### 1. Start MongoDB with Docker

From the project root:

```bash
docker compose up -d
```

This will:

- Start `mongodb` on `localhost:27017`.
- Create the `customerdb` database.
- Seed it with sample data from `data/customer.json`.

### 2. Start Kafka (for WebSocket and Webhook services)

For the WebSocket and Webhook services, which consume events from Kafka:

```bash
docker compose -f docker-compose.kafka.yml up -d
```

This will:

- Start Kafka on `localhost:9092`.
- Start Kafka UI on `http://localhost:8080` for monitoring topics and messages.

### 3. Create / Activate the Virtual Environment (optional if you already use uv)

Using `uv` (recommended):

```bash
uv sync
```

This installs the dependencies declared in `pyproject.toml` and prepares a virtual environment.

To run commands inside that environment:

```bash
uv run <command>
```

Example:

```bash
uv run .
```

will run the package's `__main__.py` and execute the simple `CustomerDB` CRUD demo.

## Running the REST API

From the project root:

```bash
uv run rest
```

This starts a FastAPI/Uvicorn server, by default on `http://0.0.0.0:8060`, via `rest.__main__.py`.

Example requests (using `curl`):

```bash
curl http://localhost:8060/health
curl http://localhost:8060/customers
curl -X POST http://localhost:8060/customers \
	-H "Content-Type: application/json" \
	-d '{
				"customerid": "C1",
				"firstname": "Alice",
				"lastname": "Smith",
				"email": "alice@example.com",
				"phone": "+1-555-0000"
			}'
```

## Running the gRPC Service

### 1. Generate gRPC Stubs (if needed)

The generated files already live in `grpc_service/customerpb/`. If you change `grpc_service/proto/customer.proto`, you can regenerate them with:

```bash
cd grpc_service
./generate.sh
cd -
```

### 2. Start the gRPC Server

From the project root:

```bash
uv run python -m grpc_service.server
```

The server will listen on `localhost:50051` and log:

```text
✅ gRPC server running on :50051
```

### 3. Call the gRPC API

You can either:

- Use `grpcurl` from the command line, or
- Use the example client in `grpc_service/client.py` once implemented.

At a high level, the service supports:

- `CreateCustomer` – create a new customer with optional address.
- `GetCustomerById` – fetch a customer document by `customerid`.
- `UpdateCustomer` – partial updates on basic fields and nested address fields.
- `DeleteCustomer` – delete a customer by `customerid`.

## Running the SOAP Service

From the project root:

```bash
uv run soap
```

This starts a Spyne SOAP server, by default on `http://0.0.0.0:8067`, via `soap.__main__.py`.

The WSDL is available at: `http://localhost:8067/?wsdl`

Example operations (using a SOAP client or tools like SoapUI):

- `create_customer` – create a new customer.
- `get_customer` – fetch a customer by ID.
- `update_customer_email` – update a customer's email.
- `delete_customer` – delete a customer by ID.

## Running the Webhook Service

From the project root:

```bash
uv run webhook
```

This starts a FastAPI webhook dispatcher service, by default on `http://0.0.0.0:8069`, via `webhook.__main__.py`.

The service consumes events from the `player-events` Kafka topic and dispatches HTTP POST requests to registered webhook URLs based on event types.

Endpoints:

- `GET /health` – health check.
- `GET /webhooks` – list all webhook subscriptions.
- `POST /webhooks` – create a new webhook subscription (requires `url`, `event_types`, `secret`, optional `player_id`).
- `DELETE /webhooks/{subscription_id}` – disable a webhook subscription.

## Running the WebSocket Service

From the project root:

```bash
uv run websocket
```

This starts a FastAPI WebSocket service, by default on `http://0.0.0.0:8068`, via `websocket.__main__.py`.

The service provides a WebSocket endpoint at `/ws` and broadcasts events consumed from the `player-events` Kafka topic to all connected clients.

Endpoints:

- `GET /health` – health check.
- `WS /ws` – WebSocket connection for receiving real-time events.

## Running the Webhook Receiver

From the project root:

```bash
uv run webhook_receiver
```

This starts a simple FastAPI webhook receiver service, by default on `http://0.0.0.0:8072`, via `webhook_receiver.__main__.py`.

The service logs incoming webhook payloads (headers and body) to the console.

Endpoint:

- `POST /hook` – receive and log webhook data.

## Running the GraphQL Service

From the project root:

```bash
uv run graphql
```

This starts a FastAPI/Strawberry GraphQL server, by default on `http://0.0.0.0:8061`, via `graphql_service/__main__.py`.

The GraphQL playground is available at: `http://localhost:8061/graphql`

Example queries:

```graphql
query GetCustomer($customerid: String!) {
  getCustomer(customerid: $customerid) {
    customerid
    firstname
    lastname
    email
    phone
    address {
      street
      city
      state
      zip
      country
    }
  }
}

query ListCustomers {
  listCustomers {
    customerid
    firstname
    lastname
    email
  }
}
```

## Running the MCP Service

From the project root:

```bash
uv run mcp
```

This starts a FastMCP server over HTTP, by default on `http://0.0.0.0:8062`, via `mcp_service/__main__.py`.

The MCP server exposes tools for customer CRUD operations and event publishing.

Available tools:

- `customer_init_indexes` – Create MongoDB indexes for customers.
- `customer_create` – Create a new customer.
- `customer_get` – Get customer by ID.
- `customer_update` – Update customer fields.
- `customer_delete` – Delete customer by ID.
- `customer_list` – List customers.
- `player_publish_score_updated` – Publish score update event to Kafka.
- `player_publish_event` – Publish custom player event to Kafka.

## Running the SSE Service

From the project root:

```bash
uv run sse
```

This starts a FastMCP server over Server-Sent Events, by default on `http://0.0.0.0:8063`, via `sse/__main__.py`.

Provides the same MCP tools as above, but over SSE transport for real-time streaming.

## Running Other Protocol Entry Points

Some modules are fully implemented, while others are placeholders that just print a greeting. The project wiring is in place via `pyproject.toml` script entries:

```bash
uv run grpc       # mapped to grpc_service:main (implemented)
uv run rest       # mapped to rest:main (implemented)
uv run soap       # mapped to soap:main (implemented)
uv run websocket  # mapped to websocket:main (implemented)
uv run webhook    # mapped to webhook:main (implemented)
uv run webhook_receiver  # mapped to webhook_receiver:main (implemented)
uv run graphql    # mapped to graphql_service:main (implemented)
uv run mcp        # mapped to mcp_service:main (implemented)
uv run amqp       # mapped to amqp:main (placeholder)
uv run mqtt       # mapped to mqtt:main (placeholder)
uv run sse        # mapped to sse:main (implemented)
```

You can use these as starting points to flesh out full implementations for the remaining placeholder protocols while reusing the shared `CustomerDB` persistence layer.

## Development

Install development dependencies:

```bash
uv sync --group dev
```

Run linters and tests:

```bash
uv run ruff check .
uv run pylint multiple-web-protocols  # or the relevant package path
uv run pytest
```

### Test Coverage

The test suite currently includes:

- gRPC service and helper tests in `tests/test_grpc_server.py` (service logic and status codes).
- MongoDB persistence tests in `tests/test_customer_db.py` using an in-memory fake `MongoClient`.
- REST API tests in `tests/test_rest_app.py` using FastAPI's `TestClient` and a fake `CustomerDB`.
- SOAP service tests in `tests/test_customer_service.py` using mocked `CustomerDB`.
- Environment configuration tests in `tests/test_envconfig.py` for `config/envconfig.py` properties.

All tests can be run together with:

```bash
uv run pytest
```

The repository is configured with a GitHub Actions workflow for linting and testing, and Codecov for coverage reporting.

## Testing Event-Driven Services

The WebSocket and Webhook services rely on Kafka for event consumption. To test them:

1. Ensure MongoDB and Kafka are running (see Getting Started).

2. Start the desired service(s), e.g., `uv run webhook` and/or `uv run websocket`.

3. Publish test events to Kafka using the provided script:

   ```bash
   uv run python data/script/publish_event.py
   ```

   This publishes 100 sample `player.score.updated` events to the `player-events` topic.

4. For Webhook testing:
   - Register a webhook subscription by POSTing to `http://localhost:8069/webhooks` with JSON payload like:
     ```json
     {
       "url": "http://localhost:8072/hook",
       "event_types": ["player.score.updated"],
       "secret": "test-secret"
     }
     ```
   - Start the webhook receiver: `uv run webhook_receiver`.
   - Publish events; the receiver should log incoming webhooks.

5. For WebSocket testing:
   - Connect to `ws://localhost:8068/ws` using a WebSocket client (e.g., browser console or tools like `websocat`).
   - Publish events; connected clients should receive the events in real-time.

6. Monitor Kafka topics via Kafka UI at `http://localhost:8080`.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.