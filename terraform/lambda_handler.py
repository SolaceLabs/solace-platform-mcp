import httpx
import json
import logging
import os
from fastmcp import FastMCP
from fastmcp.server.openapi import RouteMap, MCPType, OpenAPITool, HTTPRoute, OpenAPIResource, OpenAPIResourceTemplate
from fastmcp.client.auth import BearerAuth
from mangum import Mangum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def customize_components(route: HTTPRoute, component: OpenAPITool | OpenAPIResource | OpenAPIResourceTemplate) -> None:
    if isinstance(component, OpenAPITool):
        component.description = component.description.split("<br><br><a href=\"https://api.solace.dev/cloud/reference/authentication\">Token Permissions</a>")[0]
        component.output_schema = None
        toDelete = []
        for key, value in component.parameters["properties"].items():
            if "readOnly" in value and value["readOnly"]:
                toDelete.append(key)
                continue
            if "description" in value:
                if key != "required" and ("required" not in component.parameters or key not in component.parameters["required"]):
                    value["description"] = "(Optional) " + value["description"]
                if "minimum" in value and "maximum" in value:
                    value["description"] += f" (Range: {round(value['minimum'])} - {round(value['maximum'])})"
            if "format" in value:
                del value["format"]
        for key in toDelete:
            del component.parameters["properties"][key]


def create_mcp_app():
    """Create FastMCP app with stateless HTTP support"""
    base_url = os.getenv("SOLACE_API_BASE_URL", "https://api.solace.cloud")
    token = os.getenv("SOLACE_API_TOKEN")

    if not token:
        logger.error("SOLACE_API_TOKEN not set")
        raise ValueError("SOLACE_API_TOKEN required")

    headers = {
        "User-Agent": "solace/event-portal-designer-mcp/lambda",
        "x-issuer": "solace/event-portal-designer-mcp/lambda"
    }

    client = httpx.AsyncClient(base_url=base_url, auth=BearerAuth(token=token))
    client.headers.update(headers)

    spec_path = os.path.join(os.path.dirname(__file__), "solace_event_portal_designer_mcp/data/ep-designer.json")
    with open(spec_path) as f:
        openapi_spec = json.load(f)

    openapi_spec["components"]["schemas"]["InvalidStateReference"]["properties"]["inboundInvalidStateReferences"]["items"] = {"type": "object"}
    openapi_spec["components"]["schemas"]["InvalidStateReference"]["properties"]["outboundInvalidStateReferences"]["items"] = {"type": "object"}

    mcp = FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=client,
        name="EP Designer API",
        stateless_http=True,
        route_maps=[
            RouteMap(pattern=r"^/api/v2/architecture/applicationDomains(/\{id\})?$", mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/api/v2/architecture/applications(/\{id\})?$", mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/api/v2/architecture/applicationVersions(/\{versionId\})?$", mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/api/v2/architecture/applicationVersions/\{applicationVersionId\}/asyncApi$", mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/api/v2/architecture/events(/\{id\})?$", mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/api/v2/architecture/eventVersions(/\{id\})?$", mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/api/v2/architecture/schemaVersions(/\{id\})?$", mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/api/v2/architecture/schemas(/\{id\})?$", mcp_type=MCPType.TOOL),
            RouteMap(mcp_type=MCPType.EXCLUDE)
        ],
        mcp_component_fn=customize_components,
    )

    return mcp.http_app(path="/mcp")


def handler(event, context):
    """
    Lambda handler function.
    Creates fresh app instance per invocation for stateless operation.
    """
    logger.info(f"Request: {event.get('rawPath')}")

    try:
        # Create fresh app instance per invocation
        app = create_mcp_app()

        # Create Mangum adapter with lifespan support
        asgi_handler = Mangum(app, lifespan="on")

        # Process the event and return response
        response = asgi_handler(event, context)

        return response
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
