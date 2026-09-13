#!/usr/bin/env python3
"""
Demonstration of how to use this MCP server with the MCP configuration file.
This script shows how to load the MCP configuration and start the server.
"""

import json
import os
import subprocess
import sys
import time
import signal
from typing import Dict, Any, List, Optional, Tuple


def load_mcp_config(config_path: str) -> Dict[str, Any]:
    """Load the MCP configuration from a file."""
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)


def display_server_config(server_name: str, config: Dict[str, Any]) -> None:
    """Display the server configuration settings."""
    if server_name not in config.get('mcpServers', {}):
        print(f"Server '{server_name}' not found in configuration")
        return

    server_config = config['mcpServers'][server_name]
    env = server_config.get('env', {})

    print("\nServer Configuration:")
    print(f"  Command: {server_config.get('command')} {' '.join(server_config.get('args', []))}")

    # Display core configuration
    print("\n  Core Configuration:")
    print(f"    OpenAPI Spec: {env.get('OPENAPI_SPEC', 'Not set')}")
    print(f"    API Base URL: {env.get('SOLACE_SEMPV2_BASE_URL', 'http://localhost:8080')}")

    # Display authentication configuration
    auth_method = env.get('SOLACE_SEMPV2_AUTH_METHOD', 'basic')
    print("\n  Authentication Configuration:")
    print(f"    Auth Method: {auth_method}")
    if auth_method == 'basic':
        username = env.get('SOLACE_SEMPV2_USERNAME', 'Not set')
        password = '******' if env.get('SOLACE_SEMPV2_PASSWORD') else 'Not set'
        print(f"    Username: {username}")
        print(f"    Password: {password}")
    elif auth_method == 'bearer':
        token = '******' if env.get('SOLACE_SEMPV2_BEARER_TOKEN') else 'Not set'
        print(f"    Bearer Token: {token}")

    # Display logging configuration
    print("\n  Logging Configuration:")
    log_disabled = env.get('MCP_LOG_DISABLE', 'false').lower() == 'true'
    log_file = env.get('MCP_LOG_FILE', 'Not set')
    log_level = env.get('MCP_LOG_LEVEL', 'INFO')

    print(f"    Logging Disabled: {log_disabled}")
    if not log_disabled:
        print(f"    Log File: {log_file}")
        print(f"    Log Level: {log_level}")

    # Display API filtering settings
    print("\n  API Filtering Configuration:")
    print(f"    Include Methods: {env.get('MCP_API_INCLUDE_METHODS', 'None')}")
    print(f"    Exclude Methods: {env.get('MCP_API_EXCLUDE_METHODS', 'None')}")
    print(f"    Include Tags: {env.get('MCP_API_INCLUDE_TAGS', 'None')}")
    print(f"    Exclude Tags: {env.get('MCP_API_EXCLUDE_TAGS', 'None')}")
    print(f"    Include Paths: {env.get('MCP_API_INCLUDE_PATHS', 'None')}")
    print(f"    Exclude Paths: {env.get('MCP_API_EXCLUDE_PATHS', 'None')}")


def start_mcp_server(server_name: str, config: Dict[str, Any]) -> Optional[subprocess.Popen]:
    """Start an MCP server from the configuration."""
    if server_name not in config.get('mcpServers', {}):
        print(f"Server '{server_name}' not found in configuration")
        return None

    server_config = config['mcpServers'][server_name]
    if server_config.get('disabled', False):
        print(f"Server '{server_name}' is disabled in configuration")
        return None

    command = server_config.get('command')
    args = server_config.get('args', [])
    env = os.environ.copy()
    env.update(server_config.get('env', {}))

    cmd = [command] + args
    print(f"Starting MCP server '{server_name}' with command: {' '.join(cmd)}")

    # Start the server process
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,

            bufsize=1  # Line buffered
        )
        # Give the process a moment to start and potentially fail
        time.sleep(0.5)
        retcode = process.poll()
        print(f"Process starting ")
        if retcode is not None:
            # Process already terminated - likely failed to start
            stderr_output = process.stderr.read()
            print(f"Error starting server: exit code {retcode}): {stderr_output}")
            raise RuntimeError(f"Process failed to start (exit code {retcode}): {stderr_output}")
        print(f"Process started successfully with PID: {process.pid}")
    except Exception as e:
        print(f"Error starting server: {e}")
        return None

    # Give the server a moment to initialize
    time.sleep(2)

    return process


def send_mcp_request(server_process, request: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Send a request to the MCP server and get the response.
    Returns a tuple of (response, error_message)
    """
    if not server_process:
        return None, "Server process is not running"

    # Convert request to JSON string
    request_str = json.dumps(request) + "\n"

    try:
        # Send request to server
        server_process.stdin.write(request_str)
        server_process.stdin.flush()

        # Read response from server
        response_str = server_process.stdout.readline().strip()
        if not response_str:
            return None, "No response from server"

        # Parse response
        return json.loads(response_str), None
    except json.JSONDecodeError:
        return None, f"Error parsing response: {response_str}"
    except BrokenPipeError:
        return None, "Connection to server lost"
    except Exception as e:
        return None, f"Error communicating with server: {e}"


def initialize_server(server_process) -> bool:
    """Initialize the MCP server and get its capabilities."""
    print("\nInitializing MCP server...")
    init_request = {
        "jsonrpc": "2.0",
        "id": "init-1",
        "method": "initialize",
        "params": {}
    }

    response, error = send_mcp_request(server_process, init_request)
    if error:
        print(f"Initialization error: {error}")
        return False

    if response and "result" in response:
        result = response["result"]
        print(f"Server initialized with MCP version: {result.get('protocolVersion', 'Unknown')}")
        print(
            f"Server info: {result.get('serverInfo', {}).get('name', 'Unknown')} (v{result.get('serverInfo', {}).get('version', 'Unknown')})")

        capabilities = result.get('capabilities', {})
        print("Capabilities:")
        for capability, details in capabilities.items():
            enabled = details.get('enabled', False)
            print(f"  - {capability}: {'Enabled' if enabled else 'Disabled'}")

        return True
    else:
        print("Error initializing server:", response)
        return False


def list_tools(server_process):
    """List available tools from the MCP server."""
    print("\n1. Listing available tools...")
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": "list-1",
        "method": "mcp.list_tools"
    }

    response, error = send_mcp_request(server_process, list_tools_request)
    if error:
        print(f"Error listing tools: {error}")
        return None

    if response and "result" in response and "tools" in response["result"]:
        return response["result"]["tools"]
    else:
        print("Error getting tools list:", response)
        return None


def display_tools_summary(tools):
    """Display a summary of available tools."""
    if not tools:
        return

    print(f"Found {len(tools)} tools.")

    # Group tools by tag
    tools_by_tag = {}
    for tool in tools:
        for tag in tool.get('tags', []):
            if tag not in tools_by_tag:
                tools_by_tag[tag] = []
            tools_by_tag[tag].append(tool['name'])

    # Print a few example tags and their tools
    print("\nExample tool categories:")
    example_tags = list(tools_by_tag.keys())[:3]  # Take first 3 tags
    for tag in example_tags:
        print(f"\nTag: {tag}")
        for i, tool_name in enumerate(tools_by_tag[tag][:5], 1):  # Show first 5 tools per tag
            print(f"  {i}. {tool_name}")
        if len(tools_by_tag[tag]) > 5:
            print(f"  ... and {len(tools_by_tag[tag]) - 5} more")


def call_simple_tool(server_process, tool_name, arguments=None):
    """Call a tool with the given arguments."""
    if arguments is None:
        arguments = {}

    print(f"\nCalling {tool_name} tool...")
    call_tool_request = {
        "jsonrpc": "2.0",
        "id": f"call-{tool_name}",
        "method": "mcp.call_tool",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    response, error = send_mcp_request(server_process, call_tool_request)
    if error:
        print(f"Error calling tool: {error}")
        return None

    if response and "result" in response and "content" in response["result"]:
        content = response["result"]["content"][0]["text"]
        return json.loads(content)
    elif "error" in response:
        print(f"Error from server: {response['error'].get('message', 'Unknown error')}")
        return None
    else:
        print("Unexpected response:", response)
        return None


def main():
    # Load MCP configuration, you may need to use full path to python interpreter and mcp server script in it
    config_path = "sample_mcp_config.json"
    print(f"Loading MCP configuration from {config_path}")
    config = load_mcp_config(config_path)

    # Display the server configuration
    server_name = "solace-sempv2-config"
    display_server_config(server_name, config)

    # Start the Solace SEMPv2 MCP server
    server_process = start_mcp_server(server_name, config)
    if not server_process:
        print(f"Failed to start server '{server_name}'")
        return

    try:
        # Initialize the server
        if not initialize_server(server_process):
            return

        # List and display tools
        tools = list_tools(server_process)
        if tools:
            display_tools_summary(tools)
        else:
            return

        # Demonstrate using a simple tool - getAboutApi
        print("\n2. Calling getAboutApi tool...")
        about_api_result = call_simple_tool(server_process, "getAboutApi")
        if about_api_result:
            print("API Information:", json.dumps(about_api_result, indent=2))

        # Demonstrate error handling with an invalid tool name
        print("\n4. Error Handling: Calling non-existent tool...")
        invalid_result = call_simple_tool(server_process, "nonExistentTool")
        # The call_simple_tool function will display the error

    finally:
        # Terminate the server
        print("\nShutting down server...")
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Server did not terminate gracefully, forcing...")
            server_process.kill()
        except Exception as e:
            print(f"Error shutting down server: {e}")


if __name__ == "__main__":
    main()
