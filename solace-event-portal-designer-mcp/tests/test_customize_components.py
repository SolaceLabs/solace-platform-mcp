import pytest
from unittest.mock import Mock
from fastmcp.server.openapi import OpenAPITool, HTTPRoute

from solace_event_portal_designer_mcp.server import customize_components


class TestCustomizeComponents:

    def test_removes_token_permissions_link(self):
        route = Mock(spec=HTTPRoute)
        tool = Mock(spec=OpenAPITool)
        tool.description = (
            "Get application domains<br><br>"
            "<a href=\"https://api.solace.dev/cloud/reference/authentication\">Token Permissions</a>"
            " extra text"
        )
        tool.parameters = {"properties": {}}

        customize_components(route, tool)

        assert "Token Permissions" not in tool.description
        assert tool.description == "Get application domains"

    def test_removes_output_schema(self):
        route = Mock(spec=HTTPRoute)
        tool = Mock(spec=OpenAPITool)
        tool.description = "Some description"
        tool.output_schema = {"type": "object", "properties": {}}
        tool.parameters = {"properties": {}}

        customize_components(route, tool)

        assert tool.output_schema is None

    def test_removes_readonly_fields(self):
        route = Mock(spec=HTTPRoute)
        tool = Mock(spec=OpenAPITool)
        tool.description = "Some description"
        tool.output_schema = None
        tool.parameters = {
            "properties": {
                "id": {"type": "string", "readOnly": True},
                "name": {"type": "string"}
            }
        }

        customize_components(route, tool)

        assert "id" not in tool.parameters["properties"]
        assert "name" in tool.parameters["properties"]

    def test_adds_optional_prefix_to_non_required_fields(self):
        route = Mock(spec=HTTPRoute)
        tool = Mock(spec=OpenAPITool)
        tool.description = "Some description"
        tool.output_schema = None
        tool.parameters = {
            "properties": {
                "name": {"type": "string", "description": "The name"},
                "displayName": {"type": "string", "description": "Display name"}
            },
            "required": ["name"]
        }

        customize_components(route, tool)

        assert tool.parameters["properties"]["name"]["description"] == "The name"
        assert tool.parameters["properties"]["displayName"]["description"] == "(Optional) Display name"

    def test_adds_range_to_numeric_fields(self):
        route = Mock(spec=HTTPRoute)
        tool = Mock(spec=OpenAPITool)
        tool.description = "Some description"
        tool.output_schema = None
        tool.parameters = {
            "properties": {
                "pageSize": {
                    "type": "integer",
                    "description": "Page size",
                    "minimum": 1,
                    "maximum": 100
                }
            }
        }

        customize_components(route, tool)

        assert "(Range: 1 - 100)" in tool.parameters["properties"]["pageSize"]["description"]

    def test_removes_format_field(self):
        route = Mock(spec=HTTPRoute)
        tool = Mock(spec=OpenAPITool)
        tool.description = "Some description"
        tool.output_schema = None
        tool.parameters = {
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Email address"
                }
            }
        }

        customize_components(route, tool)

        assert "format" not in tool.parameters["properties"]["email"]

    def test_does_not_modify_non_tool_components(self):
        route = Mock(spec=HTTPRoute)
        resource = Mock()
        resource.description = "Original description"

        customize_components(route, resource)

        assert resource.description == "Original description"

    def test_handles_optional_field_without_required_list(self):
        route = Mock(spec=HTTPRoute)
        tool = Mock(spec=OpenAPITool)
        tool.description = "Some description"
        tool.output_schema = None
        tool.parameters = {
            "properties": {
                "name": {"type": "string", "description": "The name"}
            }
        }

        customize_components(route, tool)

        assert tool.parameters["properties"]["name"]["description"] == "(Optional) The name"
