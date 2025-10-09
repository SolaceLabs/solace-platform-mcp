import httpx
import json
import logging
from fastmcp import FastMCP
from fastmcp.server.openapi import (
    RouteMap,
    MCPType,
    HTTPRoute,
    OpenAPITool,
    OpenAPIResource,
    OpenAPIResourceTemplate
)
from fastmcp.client.auth import BearerAuth
import os
import sys

logger = logging.getLogger(__name__)

# We need to customize the description of each component. We want to remove all information after the "Token Permissions" link.
def customize_components(
    route: HTTPRoute, 
    component: OpenAPITool | OpenAPIResource | OpenAPIResourceTemplate,
) -> None:
    if isinstance(component, OpenAPITool):
        # Remove the "Token Permissions" link from the description
        component.description = component.description.split("<br><br><a href=\"https://api.solace.dev/cloud/reference/authentication\">Token Permissions</a>")[0]
        # Disable any kind of output validation, we will return whatever is returned by the API
        component.output_schema = None
        toDelete = []
        for key, value in component.parameters["properties"].items():
            if "readOnly" in value and value["readOnly"]:
                # If the key is readOnly, we don't want to include it in the parameters
                toDelete.append(key)
                continue

            if "description" in value:
                # If the key isn't required, add Optional
                if key != "required" and ("required" not in component.parameters or key not in component.parameters["required"]):
                    value["description"] = "(Optional) "  + value["description"]
                # Add a range if present
                if "minimum" in value and "maximum" in value:
                    value["description"] += f" (Range: {round(value['minimum'])} - {round(value['maximum'])})"
            if "format" in value:
                del value["format"]
        for key in toDelete:
            del component.parameters["properties"][key]


def main():
    from solace_event_portal_designer_mcp import __version__

    logger.info(f"Starting Solace Event Portal Designer MCP Server v{__version__}")

    # Create an HTTP client for your API
    base_url = os.getenv("SOLACE_API_BASE_URL", default="https://api.solace.cloud")
    token = os.getenv("SOLACE_API_TOKEN")
    headers_for_tracability={
        "User-Agent": f"solace/event-portal-designer-mcp/{__version__}",
        "x-issuer": f"solace/event-portal-designer-mcp/{__version__}"
    }

    logger.info(f"Connecting to Solace API at {base_url}")

    if not token:
        logger.error("SOLACE_API_TOKEN environment variable is not set")
        raise ValueError("SOLACE_API_TOKEN environment variable is not set.")

    client = httpx.AsyncClient(
        base_url=base_url,
        auth=BearerAuth(token=token)
    )
    client.headers.update(headers_for_tracability)
    logger.debug("HTTP client configured with authentication and custom headers")


    # Load your OpenAPI spec
    spec_path = os.path.join(os.path.dirname(__file__), "data", "ep-designer.json")
    logger.debug(f"Loading OpenAPI specification from {spec_path}")
    try:
        with open(spec_path) as f:
            openapi_spec = json.load(f)
        logger.debug("OpenAPI specification loaded successfully")
    except FileNotFoundError:
        logger.error(f"OpenAPI spec file not found at {spec_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in OpenAPI spec: {e}")
        sys.exit(1)

    # There are some cyclical references in the OpenAPI spec that need to be resolved before passing it to FastMCP
    # Manual patch for circular references:
    # The "InvalidStateReference" schema has properties "inboundInvalidStateReferences" and "outboundInvalidStateReferences"
    # which reference arrays of "InvalidStateReference" objects, creating a circular reference in the OpenAPI spec.
    # This causes issues with tools like FastMCP that cannot process such cycles.
    # To break the cycle, we replace the "items" schema for these properties with a generic object.
    # This loses schema detail for these properties, but is necessary for compatibility.
    logger.info("Patching circular references in OpenAPI specification")
    openapi_spec["components"]["schemas"]["InvalidStateReference"]["properties"]["inboundInvalidStateReferences"]["items"] = {"type": "object"}
    openapi_spec["components"]["schemas"]["InvalidStateReference"]["properties"]["outboundInvalidStateReferences"]["items"] = {"type": "object"}

    # Create the MCP server
    logger.info("Creating MCP server from OpenAPI specification")
    mcp = FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=client,
        name="EP Designer API",
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

    try:
        logger.info("Starting MCP server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error running MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()