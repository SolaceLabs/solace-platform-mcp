#!/usr/bin/env python3
"""
Unit tests for the Solace SEMPv2 MCP Server.

These tests verify the functionality of the SolaceSempv2McpServer class, including:
- Configuration handling
- OpenAPI spec loading
- Tool registration with various filtering options
- API invocation with different parameter types
- Error handling
"""

import unittest
import os
import json
import requests
from unittest.mock import patch, MagicMock

from solace_sempv2_mcp_server import (
    SolaceSempv2McpServer, ServerConfig, LoggingConfig, 
    Tool, McpResponse, McpError, setup_logging
)

# --- Test Fixtures ---

# Test OpenAPI specification for all tests
from test_data import DUMMY_OAS_SPEC


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and helper methods."""
    
    def setUp(self):
        """Set up for test methods."""
        # Create a dummy spec file for tests that load from file
        self.test_spec_file = "test_spec.json"
        with open(self.test_spec_file, 'w') as f:
            json.dump(DUMMY_OAS_SPEC, f)

        # Reset environment variables to defaults before each test
        self.reset_env_vars()
        
    def reset_env_vars(self):
        """Reset environment variables to default values."""
        os.environ["OPENAPI_SPEC"] = self.test_spec_file
        os.environ["SOLACE_SEMPV2_BASE_URL"] = "http://sample-solace:8080"
        os.environ["SOLACE_SEMPV2_USERNAME"] = "test_user"
        os.environ["SOLACE_SEMPV2_PASSWORD"] = "test_pass"
        os.environ["SOLACE_SEMPV2_AUTH_METHOD"] = "basic"
        os.environ["SOLACE_SEMPV2_BEARER_TOKEN"] = ""
        os.environ["MCP_API_INCLUDE_METHODS"] = ""
        os.environ["MCP_API_EXCLUDE_METHODS"] = ""
        os.environ["MCP_API_INCLUDE_TAGS"] = ""
        os.environ["MCP_API_EXCLUDE_TAGS"] = ""
        os.environ["MCP_API_INCLUDE_PATHS"] = ""
        os.environ["MCP_API_EXCLUDE_PATHS"] = ""
        os.environ["MCP_LOG_DISABLE"] = "true"  # Disable logging during tests
        os.environ["MCP_LOG_FILE"] = ""
        os.environ["MCP_LOG_LEVEL"] = "INFO"
        
    def tearDown(self):
        """Tear down after test methods."""
        # Clean up dummy spec file
        if os.path.exists(self.test_spec_file):
            os.remove(self.test_spec_file)
            
    def verify_request_basics(self, mock_request, method, url):
        """Verify basic request parameters."""
        self.assertEqual(mock_request.call_count, 1)
        call_args = mock_request.call_args[0]
        call_kwargs = mock_request.call_args[1]
        
        self.assertEqual(call_args[0], method)
        self.assertEqual(call_args[1], url)
        return call_kwargs
        
    def mock_server_setup(self, mock_load_spec=None):
        """Setup a server with mocked OpenAPI spec loading."""
        config = ServerConfig()
        if mock_load_spec:
            with patch.object(SolaceSempv2McpServer, '_load_openapi_spec', return_value=DUMMY_OAS_SPEC):
                server = SolaceSempv2McpServer(config)
        else:
            server = SolaceSempv2McpServer(config)
        return server


class TestConfigClasses(BaseTestCase):
    """Tests for configuration classes."""
    
    def test_logging_config_defaults(self):
        """Test LoggingConfig with default values."""
        logging_config = LoggingConfig()
        
        self.assertEqual(logging_config.log_level, "INFO")
        self.assertEqual(logging_config.log_file, "")
        self.assertTrue(logging_config.log_disable)
        self.assertFalse(logging_config.is_logging_enabled())
        self.assertEqual(logging_config.get_level_num(), 20)  # INFO level
        
    def test_logging_config_custom_values(self):
        """Test LoggingConfig with custom values."""
        os.environ["MCP_LOG_LEVEL"] = "DEBUG"
        os.environ["MCP_LOG_FILE"] = "test.log"
        os.environ["MCP_LOG_DISABLE"] = "false"
        
        logging_config = LoggingConfig()
        
        self.assertEqual(logging_config.log_level, "DEBUG")
        self.assertEqual(logging_config.log_file, "test.log")
        self.assertFalse(logging_config.log_disable)
        self.assertTrue(logging_config.is_logging_enabled())
        self.assertEqual(logging_config.get_level_num(), 10)  # DEBUG level
        
    def test_logging_config_invalid_level(self):
        """Test LoggingConfig with invalid log level."""
        os.environ["MCP_LOG_LEVEL"] = "INVALID_LEVEL"
        
        # Redirect stderr to capture warning message
        import sys
        from io import StringIO
        original_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logging_config = LoggingConfig()
            self.assertEqual(logging_config.log_level, "INFO")  # Should default to INFO
            self.assertIn("Invalid log level", sys.stderr.getvalue())
        finally:
            sys.stderr = original_stderr
    
    def test_server_config_defaults(self):
        """Test ServerConfig with default values."""
        config = ServerConfig()
        
        self.assertEqual(config.openapi_spec_path, self.test_spec_file)
        self.assertEqual(config.base_url, "http://sample-solace:8080")
        self.assertEqual(config.username, "test_user")
        self.assertEqual(config.password, "test_pass")
        self.assertEqual(config.auth_method, "basic")
        self.assertEqual(config.bearer_token, "")
        self.assertEqual(config.include_methods, [])
        self.assertEqual(config.exclude_methods, [])
        self.assertEqual(config.include_tags, [])
        self.assertEqual(config.exclude_tags, [])
        self.assertEqual(config.include_paths, [])
        self.assertEqual(config.exclude_paths, [])
    
    def test_server_config_custom_values(self):
        """Test ServerConfig with custom values."""
        os.environ["SOLACE_SEMPV2_BASE_URL"] = "https://custom-solace:9000"
        os.environ["SOLACE_SEMPV2_AUTH_METHOD"] = "bearer"
        os.environ["SOLACE_SEMPV2_BEARER_TOKEN"] = "test-token"
        os.environ["MCP_API_INCLUDE_METHODS"] = "GET,POST"
        os.environ["MCP_API_EXCLUDE_TAGS"] = "deprecated"
        
        config = ServerConfig()
        
        self.assertEqual(config.base_url, "https://custom-solace:9000")
        self.assertEqual(config.auth_method, "bearer")
        self.assertEqual(config.bearer_token, "test-token")
        self.assertEqual(config.include_methods, ["GET", "POST"])
        self.assertEqual(config.exclude_tags, ["deprecated"])
    
    def test_server_config_parse_list(self):
        """Test the _parse_list method in ServerConfig."""
        config = ServerConfig()
        
        self.assertEqual(config._parse_list(""), [])
        self.assertEqual(config._parse_list("item1,item2"), ["item1", "item2"])
        self.assertEqual(config._parse_list(" item1 , item2 "), ["item1", "item2"])
        self.assertEqual(config._parse_list("item1,,item2"), ["item1", "item2"])


class TestToolRegistration(BaseTestCase):
    """Tests for tool registration and filtering."""
    
    def test_no_filtering(self):
        """Test tool registration with no filters applied."""
        server = self.mock_server_setup(mock_load_spec=True)
        
        # Expect all 6 operations to be registered
        self.assertEqual(len(server.tools), 6)
        self.assertIn("getItems", server.tools)
        self.assertIn("createItem", server.tools)
        self.assertIn("getItemById", server.tools)
        self.assertIn("deleteItem", server.tools)
        self.assertIn("getBrokerConfig", server.tools)
        self.assertIn("getMsgVpnQueues", server.tools)

    def test_filter_include_methods(self):
        """Test filtering by including only GET methods."""
        os.environ["MCP_API_INCLUDE_METHODS"] = "GET"
        server = self.mock_server_setup(mock_load_spec=True)
        
        self.assertEqual(len(server.tools), 4)
        self.assertIn("getItems", server.tools)
        self.assertNotIn("createItem", server.tools)
        self.assertIn("getItemById", server.tools)
        self.assertNotIn("deleteItem", server.tools)
        self.assertIn("getBrokerConfig", server.tools)
        self.assertIn("getMsgVpnQueues", server.tools)

    def test_filter_exclude_methods(self):
        """Test filtering by excluding DELETE methods."""
        os.environ["MCP_API_EXCLUDE_METHODS"] = "DELETE"
        server = self.mock_server_setup(mock_load_spec=True)
        
        self.assertEqual(len(server.tools), 5)
        self.assertIn("getItems", server.tools)
        self.assertIn("createItem", server.tools)
        self.assertIn("getItemById", server.tools)
        self.assertNotIn("deleteItem", server.tools)
        self.assertIn("getBrokerConfig", server.tools)
        self.assertIn("getMsgVpnQueues", server.tools)

    def test_filter_include_tags(self):
        """Test filtering by including only 'items' tag."""
        os.environ["MCP_API_INCLUDE_TAGS"] = "items"
        server = self.mock_server_setup(mock_load_spec=True)
        
        self.assertEqual(len(server.tools), 4)
        self.assertIn("getItems", server.tools)
        self.assertIn("createItem", server.tools)
        self.assertIn("getItemById", server.tools)
        self.assertIn("deleteItem", server.tools)
        self.assertNotIn("getBrokerConfig", server.tools)
        self.assertNotIn("getMsgVpnQueues", server.tools)

    def test_filter_exclude_tags(self):
        """Test filtering by excluding 'write' tag."""
        os.environ["MCP_API_EXCLUDE_TAGS"] = "write"
        server = self.mock_server_setup(mock_load_spec=True)
        
        self.assertEqual(len(server.tools), 4)
        self.assertIn("getItems", server.tools)
        self.assertNotIn("createItem", server.tools)
        self.assertIn("getItemById", server.tools)
        self.assertNotIn("deleteItem", server.tools)
        self.assertIn("getBrokerConfig", server.tools)
        self.assertIn("getMsgVpnQueues", server.tools)
    
    def test_filter_include_paths(self):
        """Test filtering by including paths containing '/items'."""
        os.environ["MCP_API_INCLUDE_PATHS"] = "/items"
        server = self.mock_server_setup(mock_load_spec=True)
        
        self.assertEqual(len(server.tools), 4)
        self.assertIn("getItems", server.tools)
        self.assertIn("createItem", server.tools)
        self.assertIn("getItemById", server.tools)
        self.assertIn("deleteItem", server.tools)
        self.assertNotIn("getBrokerConfig", server.tools)
        self.assertNotIn("getMsgVpnQueues", server.tools)

    def test_filter_exclude_paths(self):
        """Test filtering by excluding paths containing '/config'."""
        os.environ["MCP_API_EXCLUDE_PATHS"] = "/config"
        server = self.mock_server_setup(mock_load_spec=True)
        
        self.assertEqual(len(server.tools), 5)
        self.assertIn("getItems", server.tools)
        self.assertIn("createItem", server.tools)
        self.assertIn("getItemById", server.tools)
        self.assertIn("deleteItem", server.tools)
        self.assertNotIn("getBrokerConfig", server.tools)
        self.assertIn("getMsgVpnQueues", server.tools)

    def test_combined_filters(self):
        """Test combining multiple filter types."""
        os.environ["MCP_API_INCLUDE_METHODS"] = "GET"
        os.environ["MCP_API_EXCLUDE_TAGS"] = "deprecated"
        server = self.mock_server_setup(mock_load_spec=True)
        
        self.assertEqual(len(server.tools), 4)
        self.assertIn("getItems", server.tools)
        self.assertNotIn("createItem", server.tools)  # Not GET
        self.assertIn("getItemById", server.tools)
        self.assertNotIn("deleteItem", server.tools)  # Not GET and also deprecated
        self.assertIn("getBrokerConfig", server.tools)
        self.assertIn("getMsgVpnQueues", server.tools)


class TestApiInvocation(BaseTestCase):
    """Tests for API invocation functionality."""
    
    @patch('requests.request')
    def test_invoke_get_no_params(self, mock_request):
        """Test invoking a simple GET tool with no parameters."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"name": "broker"}}
        mock_request.return_value = mock_response
        
        # Create server with mock spec
        server = self.mock_server_setup(mock_load_spec=True)
        
        # Get tool and invoke
        tool = server.tools["getBrokerConfig"]
        result = server._invoke_tool(tool, {})
        
        # Verify request was made correctly
        call_kwargs = self.verify_request_basics(
            mock_request, "GET", "http://sample-solace:8080/config/broker")
        
        self.assertEqual(result, {"data": {"name": "broker"}})
    
    @patch('requests.request')
    def test_invoke_get_with_path_param(self, mock_request):
        """Test invoking a GET tool with a path parameter."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "item123"}}
        mock_request.return_value = mock_response
        
        # Create server with mock spec
        server = self.mock_server_setup(mock_load_spec=True)
        
        # Get tool and invoke
        tool = server.tools["getItemById"]
        result = server._invoke_tool(tool, {"itemId": "item123"})
        
        # Verify request was made correctly
        call_kwargs = self.verify_request_basics(
            mock_request, "GET", "http://sample-solace:8080/items/item123")
        
        self.assertEqual(result, {"data": {"id": "item123"}})
    
    @patch('requests.request')
    def test_invoke_post_with_body(self, mock_request):
        """Test invoking a POST tool with a request body."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"data": {"id": "newItem"}}
        mock_request.return_value = mock_response
        
        # Create server with mock spec
        server = self.mock_server_setup(mock_load_spec=True)
        
        # Create a Tool object with a request_body attribute
        body = {"name": "New Item", "value": 42}
        tool = server.tools["createItem"]
        
        # Explicitly check that the tool has a valid request_body
        self.assertIsNotNone(tool.request_body, "Tool 'createItem' should have a request_body")
        
        # Invoke the tool with the body argument
        result = server._invoke_tool(tool, {"body": body})
        
        # Verify request was made correctly
        call_kwargs = self.verify_request_basics(
            mock_request, "POST", "http://sample-solace:8080/items")
        
        # Check that the json parameter was correctly set
        self.assertEqual(call_kwargs.get("json"), body)
        
        self.assertEqual(result, {"data": {"id": "newItem"}})
    
    @patch('requests.request')
    def test_invoke_with_bearer_auth(self, mock_request):
        """Test invoking a tool with bearer token authentication."""
        # Setup for bearer auth
        os.environ["SOLACE_SEMPV2_AUTH_METHOD"] = "bearer"
        os.environ["SOLACE_SEMPV2_BEARER_TOKEN"] = "my-token"
        
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"name": "broker"}}
        mock_request.return_value = mock_response
        
        # Create server with mock spec
        server = self.mock_server_setup(mock_load_spec=True)
        
        # Get tool and invoke
        tool = server.tools["getBrokerConfig"]
        result = server._invoke_tool(tool, {})
        
        # Verify request was made correctly
        call_kwargs = self.verify_request_basics(
            mock_request, "GET", "http://sample-solace:8080/config/broker")
        self.assertEqual(call_kwargs["headers"]["Authorization"], "Bearer my-token")
        
        self.assertEqual(result, {"data": {"name": "broker"}})
    
    @patch('requests.request')
    def test_invoke_api_error(self, mock_request):
        """Test handling HTTP errors when invoking a tool."""
        # Setup for HTTP error
        mock_request.side_effect = requests.exceptions.HTTPError("API error")
        
        # Create server with mock spec
        server = self.mock_server_setup(mock_load_spec=True)
        
        # Get tool and try to invoke
        tool = server.tools["getBrokerConfig"]
        
        # Verify error is caught and logged
        with self.assertRaises(Exception) as context:
            server._invoke_tool(tool, {})
        
        self.assertIn("API request failed", str(context.exception))


class TestMcpHandlers(BaseTestCase):
    """Tests for MCP message handlers."""
    
    def test_handle_initialize(self):
        """Test handling an initialize request."""
        server = self.mock_server_setup(mock_load_spec=True)
        
        msg_id = "test-id"
        response_str = server._handle_initialize(msg_id, {})
        response = json.loads(response_str)
        
        self.assertEqual(response["id"], msg_id)
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertTrue("result" in response)
        self.assertEqual(response["result"]["protocolVersion"], "2024-11-05")
    
    def test_handle_list_tools(self):
        """Test handling a list_tools request."""
        server = self.mock_server_setup(mock_load_spec=True)
        
        msg_id = "test-id"
        response_str = server._handle_list_tools(msg_id)
        response = json.loads(response_str)
        
        self.assertEqual(response["id"], msg_id)
        self.assertTrue("result" in response)
        self.assertTrue("tools" in response["result"])
        self.assertEqual(len(response["result"]["tools"]), 6)  # Should match number of tools registered
    
    @patch('requests.request')
    def test_handle_call_tool(self, mock_request):
        """Test handling a call_tool request."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"name": "broker"}}
        mock_request.return_value = mock_response
        
        # Create server with mock spec
        server = self.mock_server_setup(mock_load_spec=True)
        
        msg_id = "test-id"
        params = {
            "name": "getBrokerConfig",
            "arguments": {}
        }
        
        response_str = server._handle_call_tool(msg_id, params)
        response = json.loads(response_str)
        
        self.assertEqual(response["id"], msg_id)
        self.assertTrue("result" in response)
        self.assertTrue("content" in response["result"])
        content_text = response["result"]["content"][0]["text"]
        self.assertIn("data", content_text)
    
    def test_handle_call_tool_missing_name(self):
        """Test handling a call_tool request with missing tool name."""
        server = self.mock_server_setup(mock_load_spec=True)
        
        msg_id = "test-id"
        params = {"arguments": {}}  # Missing 'name'
        
        response_str = server._handle_call_tool(msg_id, params)
        response = json.loads(response_str)
        
        self.assertEqual(response["id"], msg_id)
        self.assertTrue("error" in response)
        self.assertEqual(response["error"]["code"], -32602)  # ERROR_INVALID_PARAMS
    
    def test_handle_call_tool_invalid_tool(self):
        """Test handling a call_tool request with invalid tool name."""
        server = self.mock_server_setup(mock_load_spec=True)
        
        msg_id = "test-id"
        params = {
            "name": "nonExistentTool",
            "arguments": {}
        }
        
        response_str = server._handle_call_tool(msg_id, params)
        response = json.loads(response_str)
        
        self.assertEqual(response["id"], msg_id)
        self.assertTrue("error" in response)
        self.assertEqual(response["error"]["code"], -32601)  # ERROR_METHOD_NOT_FOUND


class TestParameterReferences(BaseTestCase):
    """Tests for handling OpenAPI parameter references."""
    
    def test_resolve_parameter_reference(self):
        """Test resolving parameter references in the OpenAPI spec."""
        server = self.mock_server_setup(mock_load_spec=True)
        
        # Test with a valid reference
        server.openapi_spec = {
            "parameters": {
                "testParam": {
                    "name": "testParam",
                    "in": "query",
                    "type": "string",
                    "description": "A test parameter"
                }
            }
        }
        
        result = server._resolve_parameter_reference("#/parameters/testParam")
        self.assertEqual(result, {
            "name": "testParam",
            "in": "query",
            "type": "string",
            "description": "A test parameter"
        })
        
        # Test with an invalid reference path
        result = server._resolve_parameter_reference("#/invalid/path")
        self.assertEqual(result, {})
        
        # Test with an external reference (not supported)
        result = server._resolve_parameter_reference("https://example.com/api#/parameters/testParam")
        self.assertEqual(result, {})
    
    def test_build_input_schema_with_path_parameters(self):
        """Test building input schema with path parameters."""
        server = self.mock_server_setup(mock_load_spec=True)
        
        parameters = [
            {
                "name": "itemId",
                "in": "path",
                "type": "string",
                "description": "ID of the item",
                "required": True
            },
            {
                "name": "filter",
                "in": "query",
                "type": "string",
                "description": "Filter expression"
            }
        ]
        
        schema = server._build_input_schema(parameters, None)
        
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["properties"]["itemId"]["type"], "string")
        self.assertEqual(schema["properties"]["filter"]["type"], "string")
        self.assertEqual(schema["required"], ["itemId"])
    
    def test_build_input_schema_with_request_body(self):
        """Test building input schema with a request body."""
        server = self.mock_server_setup(mock_load_spec=True)
        
        parameters = [
            {
                "name": "itemId",
                "in": "path",
                "type": "string",
                "required": True
            }
        ]
        
        request_body = {
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "integer"}
                }
            }
        }
        
        schema = server._build_input_schema(parameters, request_body)
        
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["properties"]["itemId"]["type"], "string")
        self.assertEqual(schema["properties"]["body"]["type"], "object")
        self.assertIn("itemId", schema["required"])
        self.assertIn("body", schema["required"])
    
    def test_build_input_schema_with_resolved_references(self):
        """Test building input schema with resolved reference parameters."""
        server = self.mock_server_setup(mock_load_spec=True)
        
        # Mock the _resolve_parameter_reference method
        original_resolve = server._resolve_parameter_reference
        
        def mock_resolve(ref_path):
            if ref_path == "#/parameters/testParam":
                return {
                    "name": "testParam",
                    "in": "query",
                    "type": "string",
                    "description": "A test parameter from reference",
                    "required": True
                }
            return {}
        
        server._resolve_parameter_reference = mock_resolve
        
        parameters = [
            {"$ref": "#/parameters/testParam"},
            {
                "name": "directParam",
                "in": "path",
                "type": "string"
            }
        ]
        
        schema = server._build_input_schema(parameters, None)
        
        # Restore original method
        server._resolve_parameter_reference = original_resolve
        
        self.assertEqual(schema["type"], "object")
        self.assertTrue("testParam" in schema["properties"])
        self.assertTrue("directParam" in schema["properties"])
        self.assertEqual(schema["properties"]["testParam"]["description"], 
                         "A test parameter from reference")
        self.assertEqual(schema["required"], ["testParam"])


if __name__ == "__main__":
    unittest.main()