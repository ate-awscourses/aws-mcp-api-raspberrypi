from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import strawberry
from strawberry.fastapi import GraphQLRouter
import requests
import time

# Replace this with your exact API Gateway Invoke URL followed by /sync
AWS_API_GATEWAY_URL = "https://f615d8utbk.execute-api.us-west-1.amazonaws.com/prod"

app = FastAPI(title="Edge Telemetry API")

# --- 1. DATA MODELS ---
class Telemetry(BaseModel):
    device_id: str
    cpu_temp: float
    memory_usage: float

# --- 2. REST API ROUTES ---
@app.post("/api/v1/telemetry")
async def post_telemetry(data: Telemetry):
    """Receives local edge data and syncs to AWS only if a threshold is breached."""
    aws_status = "skipped_normal_temp"
    
    # Event-Driven Architecture: Only alert the cloud if the CPU exceeds 80 degrees
    if data.cpu_temp > 44.0:
        try:
            # Format the payload exactly as the Lambda function expects it
            cloud_payload = {
                "device_id": data.device_id, 
                "cpu_temp": data.cpu_temp
            }
            
            # Push to AWS Cloud (with a 3-second timeout to prevent locking the edge device)
            resp = requests.post(AWS_API_GATEWAY_URL, json=cloud_payload, timeout=3)
            
            if resp.status_code == 200:
                aws_status = f"synced_to_dynamodb"
            else:
                aws_status = f"sync_failed_http_{resp.status_code}"
                
        except Exception as e:
            aws_status = f"sync_error: {str(e)}"

    return {
        "status": "success", 
        "recorded": data.dict(), 
        "aws_sync": aws_status
    }

@app.get("/api/v1/health")
async def health_check(simulate_error: int = Query(None, description="Inject an HTTP status code")):
    """A diagnostic endpoint for the MCP tool to hit, featuring intentional fault injection."""
    if simulate_error == 400:
        raise HTTPException(status_code=400, detail="Simulated Bad Request: Missing device_id")
    elif simulate_error == 429:
        return JSONResponse(status_code=429, content={"detail": "Too Many Requests"}, headers={"Retry-After": "60"})
    elif simulate_error == 500:
        # Force an internal server crash for diagnostic testing
        1 / 0
        
    return {"status": "healthy", "timestamp": time.time(), "cpu_temp": 45.2, "protocol": "REST"}

# --- 3. GRAPHQL ROUTE ---
@strawberry.type
class SystemMetrics:
    cpu_temp: float
    uptime: int
    status: str

@strawberry.type
class Query:
    @strawberry.field
    def metrics(self) -> SystemMetrics:
        # In a real environment, this would read actual sensor data. We are mocking it for the lab.
        return SystemMetrics(cpu_temp=45.2, uptime=3600, status="healthy")

# Mount the GraphQL application onto the FastAPI server
schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
