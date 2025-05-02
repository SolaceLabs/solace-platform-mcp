#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import sys
import json
import logging
import logging.handlers
import requests
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict

class LoggingConfig:
    """Encapsulates logging configuration properties."""
    def __init__(self):
        load_dotenv()  # Load variables from .env file
        # Logging configuration
        self.log_level = os.environ.get("MCP_LOG_LEVEL", "INFO").upper()
        self.log_file = os.environ.get("MCP_LOG_FILE", "")
        self.log_disable = os.environ.get("MCP_LOG_DISABLE", "").lower() == "true"

        # Validate log level
        if self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            print(f"Warning: Invalid log level {self.log_level}. Using INFO instead.", file=sys.stderr)
            self.log_level = "INFO"

    def get_level_num(self) -> int:
        """Convert log level string to numeric value."""
        return getattr(logging, self.log_level, logging.INFO)

    def is_logging_enabled(self) -> bool:
        """Check if logging is enabled."""
        return not self.log_disable and (self.log_file != "")

    def __str__(self) -> str:
        """Return string representation for debugging."""
        return f"LoggingConfig(level={self.log_level}, file={self.log_file}, disabled={self.log_disable})"

# Configure logging
def setup_logging():
    """Configure logging with file handler based on LoggingConfig."""
    config = LoggingConfig()
    logger = logging.getLogger("solace-sempv2-mcp")

    # Set log level
    log_level_num = config.get_level_num()
    logger.setLevel(log_level_num)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Check if logging is disabled
    if config.log_disable:
        logger.disabled = True
        return logger

    # Add file handler if specified
    if config.log_file:
        try:
            file_handler = logging.FileHandler(config.log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
        except Exception as e:
            # Can't log this error since logger setup failed
            print(f"ERROR: Failed to create log file {config.log_file}: {e}", file=sys.stderr)
            # Continue without logging
    else:
        # Disable logging if no file is specified
        logger.disabled = True

    return logger

# Initialize logger
logger = setup_logging()

# MCP Protocol Constants
MCP_VERSION = "2024-11-05"

# MCP Message Types
REQUEST = "request"
RESPONSE = "response"
ERROR = "error"

# MCP Error Codes
ERROR_PARSE = -32700
ERROR_INVALID_REQUEST = -32600
ERROR_METHOD_NOT_FOUND = -32601
ERROR_INVALID_PARAMS = -32602
ERROR_INTERNAL = -32603

class ServerConfig:
    """Encapsulates configuration properties with default values."""
    def __init__(self):
        # OpenAPI spec configuration
        self.openapi_spec_path = os.environ.get("OPENAPI_SPEC", "semp-v2-swagger-monitor.json")

        # Solace SEMP API configuration
        self.base_url = os.environ.get("SOLACE_SEMPV2_BASE_URL", "http://localhost:8080")
        self.username = os.environ.get("SOLACE_SEMPV2_USERNAME")
        self.password = os.environ.get("SOLACE_SEMPV2_PASSWORD")

        # Authentication configuration
        self.auth_method = os.environ.get("SOLACE_SEMPV2_AUTH_METHOD", "basic").lower()
        self.bearer_token = os.environ.get("SOLACE_SEMPV2_BEARER_TOKEN", "")

        # API filtering options - by default, include all APIs
        self.include_methods = self._parse_list(os.environ.get("MCP_API_INCLUDE_METHODS", ""))
        self.exclude_methods = self._parse_list(os.environ.get("MCP_API_EXCLUDE_METHODS", ""))
        self.include_tags = self._parse_list(os.environ.get("MCP_API_INCLUDE_TAGS", ""))
        self.exclude_tags = self._parse_list(os.environ.get("MCP_API_EXCLUDE_TAGS", ""))
        self.include_paths = self._parse_list(os.environ.get("MCP_API_INCLUDE_PATHS", ""))
        self.exclude_paths = self._parse_list(os.environ.get("MCP_API_EXCLUDE_PATHS", ""))
        self.include_tools = self._parse_list(os.environ.get("MCP_API_INCLUDE_TOOLS", ""))
        self.exclude_tools = self._parse_list(os.environ.get("MCP_API_EXCLUDE_TOOLS", ""))
        self.validate()

        # Log configuration (masking sensitive data)
        self._log_configuration()

    def _log_configuration(self):
        """Log all configuration properties with sensitive data masked."""
        # Create a dictionary of configuration properties
        config_dict = {
            "OpenAPI Configuration": {
                "openapi_spec_path": self.openapi_spec_path
            },
            "Solace SEMP API Configuration": {
                "base_url": self.base_url,
                "username": self.username if self.username else "<not set>",
                "password": "********" if self.password else "<not set>",
                "auth_method": self.auth_method,
                "bearer_token": "********" if self.bearer_token else "<not set>"
            },
            "API Filtering Configuration": {
                "include_methods": self.include_methods or "<not set>",
                "exclude_methods": self.exclude_methods or "<not set>",
                "include_tags": self.include_tags or "<not set>",
                "exclude_tags": self.exclude_tags or "<not set>",
                "include_paths": self.include_paths or "<not set>",
                "exclude_paths": self.exclude_paths or "<not set>"
            }
        }

        # Log the configuration
        logger.info("Server configuration:")
        for section, values in config_dict.items():
            logger.info(f"  {section}:")
            for key, value in values.items():
                logger.info(f"    {key}: {value}")

    @staticmethod
    def _parse_list(value: str) -> List[str]:
        """Parse comma-separated string into list of strings."""
        if not value:
            return []
        return [item.strip() for item in value.split(',') if item.strip()]

    def validate(self):
        """Validate the configuration and raise errors for critical missing properties."""
        if not self.base_url:
            raise ValueError("SOLACE_SEMPV2_BASE_URL must be specified")

        if self.auth_method == "basic":
            if self.username and not self.password:
                logger.warning("Username specified but password is missing")
            if not self.username and self.password:
                logger.warning("Password specified but username is missing")
        elif self.auth_method == "bearer":
            if not self.bearer_token:
                logger.warning("Bearer auth selected but token is missing")

@dataclass
class McpMessage:
    """Base class for MCP messages"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None

@dataclass
class McpRequest(McpMessage):
    """MCP request message"""
    method: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class McpResponse(McpMessage):
    """MCP response message"""
    result: Dict[str, Any] = field(default_factory=dict)

@dataclass
class McpError(McpMessage):
    """MCP error message"""
    error: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Tool:
    """Represents an MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    path: str
    method: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)

class SolaceSempv2McpServer:
    """MCP Server for the Solace SEMPv2 API"""

    def __init__(self, config: ServerConfig):
        """Initialize the server with the OpenAPI spec"""
        self.config = config
        self.tools: Dict[str, Tool] = {}
        self.openapi_path = config.openapi_spec_path
        self.base_url = config.base_url
        self.username = config.username
        self.password = config.password
        self.openapi_spec = self._load_openapi_spec(self.openapi_path)

        self._register_tools()

    def _load_openapi_spec(self, path: str) -> Dict[str, Any]:
        """Load and parse the OpenAPI specification"""
        try:
            with open(path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Failed to load OpenAPI spec: {e}")
            sys.exit(1)

    def _should_register(self, method: str, tags: List[str], path: str, tool_name: str) -> bool:
        """Determine if a given API operation should be registered as a tool based on filtering rules"""
        method = method.upper()

        # Filter by HTTP method
        if self.config.include_methods and method not in self.config.include_methods:
            logger.debug(f"Filtering out {method} {path}: method not in include list")
            return False
        if self.config.exclude_methods and method in self.config.exclude_methods:
            logger.debug(f"Filtering out {method} {path}: method in exclude list")
            return False

        # Filter by tools
        if self.config.include_tools and tool_name not in self.config.include_tools:
            logger.debug(f"Filtering out {method} {tool_name}: tool not in include list")
            return False
        if self.config.exclude_tools and tool_name in self.config.exclude_tools:
            logger.debug(f"Filtering out {method} {tool_name}: tools in exclude list")
            return False

        # Filter by tags
        if self.config.include_tags:
            # Only apply tag inclusion filter if tags are specified
            if not any(tag in self.config.include_tags for tag in tags):
                logger.debug(f"Filtering out {method} {path}: no matching tags in include list")
                return False

        if self.config.exclude_tags and any(tag in self.config.exclude_tags for tag in tags):
            logger.debug(f"Filtering out {method} {path}: tag in exclude list")
            return False

        # Filter by path
        if self.config.include_paths:
            # Only apply path inclusion filter if paths are specified
            if not any(pattern in path for pattern in self.config.include_paths):
                logger.debug(f"Filtering out {method} {path}: path not matching any pattern in include list")
                return False

        if self.config.exclude_paths and any(pattern in path for pattern in self.config.exclude_paths):
            logger.debug(f"Filtering out {method} {path}: path matching pattern in exclude list")
            return False

        return True

    def _register_tools(self) -> None:
        """Dynamically register tools based on the OpenAPI spec"""
        paths = self.openapi_spec.get('paths', {})
        base_path = self.openapi_spec.get('basePath', '')

        registered_count = 0
        filtered_count = 0

        for path, methods in paths.items():
            for method, details in methods.items():
                if 'operationId' not in details:
                    continue

                tool_name = details['operationId']

                # Extract tags
                tags = details.get('tags', [])

                # Apply filtering rules
                if not self._should_register(method, tags, path, tool_name):
                    logger.debug(f"Filtering out API: {method} {path} with tags {tags}")
                    filtered_count += 1
                    continue

                description = details.get('summary', '')
                # Truncate description at "Attribute|" if present
                if details.get('description'):
                    desc_text = details['description']
                    attr_index = desc_text.find('Attribute|')
                    if attr_index != -1:
                        desc_text = desc_text[:attr_index]
                    description += f"\n{desc_text}"

                # Extract parameters, resolving any references
                parameters = []
                for param in details.get('parameters', []):
                    if '$ref' in param:
                        # Resolve parameter reference
                        resolved_param = self._resolve_parameter_reference(param['$ref'])
                        if resolved_param:
                            parameters.append(resolved_param)
                    else:
                        parameters.append(param)

                # Extract request body if present (can be in parameters or as requestBody)
                request_body = None
                for param in parameters:
                    if param.get('in') == 'body':
                        request_body = param
                        break

                # Check for OpenAPI 3.0 style requestBody if not found in parameters
                if not request_body and 'requestBody' in details:
                    # Convert OpenAPI 3.0 requestBody to a parameter-like structure for compatibility
                    request_body = {
                        'name': 'body',
                        'in': 'body',
                        'required': details.get('requestBody', {}).get('required', False),
                        'schema': details.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
                    }

                # Build input schema
                input_schema = self._build_input_schema(parameters, request_body)

                # Create and register the tool
                tool = Tool(
                    name=tool_name,
                    description=description,
                    input_schema=input_schema,
                    path=base_path + path,
                    method=method.upper(),
                    parameters=parameters,
                    request_body=request_body,
                    tags=tags
                )

                self.tools[tool_name] = tool
                registered_count += 1
                logger.info(f"Registered tool: {tool_name}")

        logger.info(f"Registered {registered_count} tools, filtered out {filtered_count} APIs")

    def _resolve_parameter_reference(self, ref_path: str) -> Dict[str, Any]:
        """Resolve a parameter reference in the OpenAPI spec"""
        if not ref_path.startswith('#/'):
            logger.warning(f"External references not supported: {ref_path}")
            return {}

        path_parts = ref_path[2:].split('/')
        current = self.openapi_spec

        for part in path_parts:
            if part not in current:
                logger.warning(f"Parameter reference not found: {ref_path}")
                return {}
            current = current[part]

        return current

    def _build_input_schema(self, parameters: List[Dict[str, Any]], request_body: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build JSON Schema for tool input based on OpenAPI parameters"""
        properties = {}
        required = []

        # Process path parameters
        for param in parameters:
            # Check if this is a reference parameter and resolve it
            if '$ref' in param:
                param = self._resolve_parameter_reference(param['$ref'])

            if param.get('in') in ['path', 'query']:
                param_name = param.get('name', '')
                param_type = param.get('type', 'string')
                param_description = param.get('description', '')
                param_required = param.get('required', False)
                if param_name == 'count':
                    param_type = 'string'
                properties[param_name] = {
                    "type": param_type,
                    "description": param_description
                }

                if param_required:
                    required.append(param_name)

        # Process request body if present
        if request_body:
            body_schema = request_body.get('schema', {})
            body_required = request_body.get('required', False)

            properties['body'] = body_schema

            if body_required:
                required.append('body')

        # Create the final schema
        schema = {
            "type": "object",
            "properties": properties
        }

        if required:
            schema["required"] = required

        return schema

    def handle_message(self, message_str: str) -> str:
        """Handle an incoming MCP message"""
        try:
            message = json.loads(message_str)

            # Validate message format
            if not isinstance(message, dict) or 'jsonrpc' not in message or message['jsonrpc'] != '2.0':
                return self._create_error_response(None, ERROR_INVALID_REQUEST, "Invalid request format")

            msg_id = message.get('id')
            method = message.get('method')

            if not method:
                return self._create_error_response(msg_id, ERROR_INVALID_REQUEST, "Method not specified")

            # Handle different MCP methods
            if method == "initialize":
                return self._handle_initialize(msg_id, message.get('params', {}))
            elif method == "mcp.list_tools" or method == "tools/list":
                return self._handle_list_tools(msg_id)
            elif method == "mcp.call_tool" or method == "tools/call":
                return self._handle_call_tool(msg_id, message.get('params', {}))
            else:
                return self._create_error_response(msg_id, ERROR_METHOD_NOT_FOUND, f"Method not found: {method}")

        except json.JSONDecodeError:
            return self._create_error_response(None, ERROR_PARSE, "Parse error")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return self._create_error_response(None, ERROR_INTERNAL, f"Internal error: {str(e)}")

    def _handle_initialize(self, msg_id: str, params: Dict[str, Any]) -> str:
        """Handle initialize request"""
        # Return server capabilities
        response = McpResponse(
            id=msg_id,
            result={
                "protocolVersion": MCP_VERSION,
                "capabilities": {
                    "tools": {
                        "enabled": True
                    },
                    "resources": {
                        "enabled": False
                    },
                    "resourceTemplates": {
                        "enabled": False
                    }
                },
                "serverInfo": {
                    "name": "solace-sempv2-mcp",
                    "version": MCP_VERSION
                }
            }
        )

        return json.dumps(asdict(response))

    def _handle_list_tools(self, msg_id: str) -> str:
        """Handle mcp.list_tools request"""
        tools_list = []

        for name, tool in self.tools.items():
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
                "tags": tool.tags
            })

        response = McpResponse(
            id=msg_id,
            result={"tools": tools_list}
        )

        return json.dumps(asdict(response))

    def _handle_call_tool(self, msg_id: str, params: Dict[str, Any]) -> str:
        """Handle mcp.call_tool request"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        if not tool_name:
            return self._create_error_response(msg_id, ERROR_INVALID_PARAMS, "Tool name not specified")

        tool = self.tools.get(tool_name)
        if not tool:
            return self._create_error_response(msg_id, ERROR_METHOD_NOT_FOUND, f"Tool not found: {tool_name}")

        try:
            # Dynamically invoke the tool
            result = self._invoke_tool(tool, arguments)

            response = McpResponse(
                id=msg_id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            )

            return json.dumps(asdict(response))

        except Exception as er:
            logger.error(f"Error invoking tool {tool_name}: {er}")
            return self._create_error_response(msg_id, ERROR_INTERNAL, f"Error invoking tool: {str(er)}")

    def _invoke_tool(self, tool: Tool, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically invoke a tool by making the appropriate API request"""
        # Prepare the URL with path parameters
        url = self._prepare_url(tool.path, arguments)

        # Prepare query parameters
        query_params = self._prepare_query_params(tool.parameters, arguments)

        # Prepare headers
        headers = {"Content-Type": "application/json"}

        # Prepare request body if needed
        body = None
        if 'body' in arguments and tool.request_body:
            body = arguments['body']

        # Prepare auth based on configured authentication method
        auth = None
        if self.config.auth_method == "basic" and self.config.username and self.config.password:
            auth = (self.config.username, self.config.password)
        elif self.config.auth_method == "bearer" and self.config.bearer_token:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"

        # Make the request
        try:
            response = self._make_request(tool.method, url, params=query_params, headers=headers, json=body, auth=auth)
            return response
        except Exception as e:
            logger.error(f"API request failed: {e}")
            # Re-raising with a message that includes "API request failed" for test compatibility
            raise Exception(f"API request failed: {str(e)}")

    def _prepare_url(self, path_template: str, arguments: Dict[str, Any]) -> str:
        """Prepare the URL by replacing path parameters with values from arguments"""
        url = self.base_url + path_template

        # Replace path parameters
        for arg_name, arg_value in arguments.items():
            placeholder = f"{{{arg_name}}}"
            if placeholder in url:
                url = url.replace(placeholder, str(arg_value))

        return url

    def _prepare_query_params(self, parameters: List[Dict[str, Any]], arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Extract query parameters from arguments based on parameter definitions"""
        query_params = {}

        for param in parameters:
            if param.get('in') == 'query':
                param_name = param.get('name')
                if param_name in arguments:
                    query_params[param_name] = arguments[param_name]

        return query_params

    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the API"""
        logger.info(f"Making {method} request to {url}")

        # Debug information - log all parameters
        logger.debug(f"Request details for {method} {url}:")

        # Log each parameter with special handling for sensitive data
        for param_name, param_value in kwargs.items():
            if param_name == 'auth':
                continue
            elif param_name == 'headers' and param_value:
                # Mask sensitive headers like Authorization
                headers_debug = param_value.copy()
                if 'Authorization' in headers_debug:
                    auth_parts = headers_debug['Authorization'].split(' ')
                    if len(auth_parts) > 1:
                        headers_debug['Authorization'] = f"{auth_parts[0]} ***"
                    else:
                        headers_debug['Authorization'] = "***"
                logger.debug(f"  headers: {headers_debug}")
            elif param_name == 'json' and param_value:
                # Print JSON structure but potentially mask sensitive values
                logger.debug(f"  json: {json.dumps(param_value, indent=2)}")
            else:
                logger.debug(f"  {param_name}: {param_value}")

        # Execute the request
        response = requests.request(method, url, **kwargs)

        # Log response details
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")

        # Raise exception for error status codes
        response.raise_for_status()

        # Try to parse as JSON
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"text": response.text}

    def _create_error_response(self, msg_id: Optional[str], code: int, message: str) -> str:
        """Create an MCP error response"""
        error = McpError(
            id=msg_id,
            error={
                "code": code,
                "message": message
            }
        )

        return json.dumps(asdict(error))

    def run(self) -> None:
        """Run the MCP server, reading from stdin and writing to stdout"""
        logger.info("Starting Solace SEMPv2 MCP Server")
        logger.info(f"Loaded {len(self.tools)} tools from OpenAPI spec")

        # Print server info
        server_info = {
            "name": "solace-sempv2-mcp",
            "version": MCP_VERSION,
            "tools": list(self.tools.keys())
        }
        logger.info(f"Server info: {json.dumps(server_info)}")

        try:
            # Process messages from stdin
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                response = self.handle_message(line)
                sys.stdout.write(response + "\n")
                sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("Server shutting down")
            sys.exit(0)

if __name__ == "__main__":
    try:
        # Create configuration object
        config = ServerConfig()

        # Create and run the server
        server = SolaceSempv2McpServer(config)
        server.run()
    except Exception as e:
        logger.critical(f"Server startup failed: {e}")
        sys.exit(1)
