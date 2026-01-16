import json
import logging
from mangum import Mangum
from solace_event_portal_designer_mcp.server import create_mcp_http_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handler(event, context):
    """Lambda handler that calls the EP MCP module."""
    logger.info(f"Request: {event.get('rawPath')}")

    try:
        app = create_mcp_http_app()
        asgi_handler = Mangum(app, lifespan="on")
        return asgi_handler(event, context)
    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            })
        }
