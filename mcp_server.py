from mcp.server.fastmcp import FastMCP
import urllib.request
import urllib.error
import boto3
from boto3.dynamodb.conditions import Key

mcp = FastMCP("Edge Diagnostic Server")

# Initialize AWS DynamoDB using the credentials configured in Phase 4
dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
table = dynamodb.Table('EdgeTelemetry')

@mcp.tool()
def ping_health_endpoint(simulate_error: int = None) -> str:
    """Pings the local REST API health endpoint to check status or trigger simulated errors."""
    url = "http://localhost:8000/api/v1/health"
    if simulate_error:
        url += f"?simulate_error={simulate_error}"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = response.read().decode("utf-8")
            return f"SUCCESS - Status: {response.status}\nBody: {data}"
    except urllib.error.HTTPError as e:
        return f"HTTP ERROR {e.code}\nReason: {e.reason}\nHeaders: {dict(e.headers)}"
    except Exception as e:
        return f"CONNECTION FAILED: {str(e)}"

@mcp.tool()
def check_pi_system_memory() -> str:
    """Reads local system memory directly from the Raspberry Pi OS environment."""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        return "".join(lines[:5])
    except Exception as e:
        return f"Failed to read memory: {str(e)}"

@mcp.tool()
def verify_cloud_backup(device_id: str) -> str:
    """Queries AWS DynamoDB to confirm if a critical telemetry alert was synced to the cloud."""
    try:
        response = table.query(
            KeyConditionExpression=Key('device_id').eq(device_id)
        )
        items = response.get('Items', [])
        if not items:
            return f"No cloud records found in DynamoDB for device: {device_id}."
        return f"Found {len(items)} cloud records. Latest record: {items[-1]}"
    except Exception as e:
        return f"AWS Query Failed: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
