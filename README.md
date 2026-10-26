# Edge-to-Cloud API & MCP Telemetry Gateway

An event-driven hybrid REST and GraphQL API gateway built on a Raspberry Pi 5. This edge device processes local hardware telemetry and conditionally syncs critical threshold alerts to an AWS Serverless backend (API Gateway, Lambda, DynamoDB). It features a local Model Context Protocol (MCP) server designed to allow LLMs to natively troubleshoot API health and cloud synchronization.

graph LR
        subgraph Mac ["Local Mac"]
            Claude["Claude Desktop"]
        end

        subgraph Edge ["Raspberry Pi 5 (Edge)"]
            MCP["FastMCP Server"]
            REST["FastAPI (REST)"]
            GQL["Strawberry (GraphQL)"]
        end

        subgraph AWS ["AWS Cloud (Serverless)"]
            APIGW["API Gateway"]
            Lambda["AWS Lambda"]
            DDB[(DynamoDB)]
        end

        %% Data Flow & Diagnostics
        Claude <-->|SSH / stdio| MCP
        MCP -->|Health Ping| REST
        MCP -.->|Verify Cloud Record| DDB
        REST -->|High Temp Alert| APIGW
        GQL --- REST
        APIGW --> Lambda
        Lambda --> DDB

## 🛠 Tech Stack
* **Edge Hardware:** Raspberry Pi 5, Raspberry Pi OS (ARM64)
* **API Frameworks:** Python 3, FastAPI (REST), Strawberry (GraphQL), Uvicorn
* **Cloud Infrastructure:** AWS API Gateway, AWS Lambda (boto3), Amazon DynamoDB
* **Observability & Testing:** FastMCP (Anthropic Claude Desktop Integration), Postman, Git

## 🚀 Core Features
1. **Hybrid API Routing:** Mounts both a REST endpoint (`/api/v1/telemetry`) and a GraphQL schema (`/graphql`) on a single ASGI server instance.
2. **Event-Driven Cloud Syncing:** Edge data is processed locally; AWS API Gateway is only invoked if CPU/Memory metrics breach critical thresholds, optimizing cloud costs.
3. **Intentional Fault Injection:** Includes a `/health` endpoint designed to simulate HTTP 400, 429 (Rate Limiting), and 500 error states for testing support runbooks and client retry logic.
4. **AI-Driven Diagnostics (MCP):** Exposes a secure `stdio` pipeline allowing an AI client (Claude) to:
   * Ping local API endpoints and evaluate HTTP headers.
   * Read raw hardware memory limits from the Pi OS (`/proc/meminfo`).
   * Query AWS DynamoDB remotely to verify if edge alerts successfully reached the cloud.

## 📂 Repository Structure
* `main.py` - The FastAPI and Strawberry GraphQL application.
* `mcp_server.py` - The diagnostic server exposing edge and AWS tools to the LLM.
* `tests/Edge_API_Tests.json` - Automated Postman test suite validating HTTP status codes, headers, and JSON/GraphQL payloads.
* `requirements.txt` - Python dependencies.

## ⚙️ Local Setup & Execution

**1. Clone and Configure Environment**
```bash
git clone [https://github.com/andrewte1995/aws-mcp-api-raspberrypi.git](https://github.com/andrewte1995/aws-mcp-api-raspberrypi.git)
cd aws-mcp-api-raspberrypi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
