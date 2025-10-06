import httpx
import json
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
    # Create an HTTP client for your API
    base_url = os.getenv("SOLACE_API_BASE_URL", default="https://api.solace.cloud")
    token = os.getenv("SOLACE_API_TOKEN")
    if not token:
        raise ValueError("SOLACE_API_TOKEN environment variable is not set.")

    client = httpx.AsyncClient(
        base_url=base_url,
        auth=BearerAuth(token=token)
    )

    # Load your OpenAPI spec
    spec_path = os.path.join(os.path.dirname(__file__), "data", "ep-designer.json")
    with open(spec_path) as f:
        openapi_spec = json.load(f)

    # There are some cyclical references in the OpenAPI spec that need to be resolved before passing it to FastMCP
    openapi_spec["components"]["schemas"]["InvalidStateReference"]["properties"]["inboundInvalidStateReferences"]["items"] = {"type": "object"}
    openapi_spec["components"]["schemas"]["InvalidStateReference"]["properties"]["outboundInvalidStateReferences"]["items"] = {"type": "object"}

    # Create the MCP server
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

    mcp.run()

if __name__ == "__main__":
    main()