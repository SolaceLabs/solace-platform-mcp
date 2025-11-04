# (Beta) Solace Monitoring MCP Server for Solace Agent Mesh 

This is a Model Context Protocol (MCP) server for Solace event brokers. 
It provides comprehensive monitoring and management capabilities for Solace event brokers. 
The server dynamically registers tools based on the Solace OpenAPI specification.
This server enables seamless integration between Solace Agent Mesh (SAM) and Solace event brokers.


## Features

- **Dynamic Tool Registration**: Automatically registers tools based on a provided OpenAPI specification.
- **Configurable API Filtering**: Allows fine-grained control over which API operations are registered as tools based on HTTP methods, tags, or paths.
- **Multiple Authentication Methods**: Supports Basic Authentication (username/password) and Bearer Token authentication.
- **Configurable OpenAPI Source**: Load the OpenAPI specification from a local file path or a remote URL.
- **File-Based Logging**: Logs server activity to a rotating file, avoiding interference with `stdio` transport used by the MCP SDK. Logging can also be disabled.
- **Multi-Broker Support**: Connect to and manage multiple Solace brokers from a single server instance.

## Requirements

- Python 3.10+
- Required Python packages:
  - `requests` 
  - `python-dotenv`
  **No additional dependencies are required when you are running this server using Solace Agent Mesh Python virtual environment.

## Installation

### Automatic Installation

The easiest way to install is to use the provided installation script:

```bash
./install.sh
```

This script will:
1. Check if Python 3.10+ is installed.
2. Install the required Python packages (`requests` and `mcp`).
3. Make all Python scripts executable.

### Manual Installation

If you prefer to install manually:

```bash
pip install -r requirements.txt 
```

or 

```bash
pip install requests
```

3. Make the scripts executable:

```bash
chmod +x solace_monitoring_mcp_server.py
# Optional: chmod +x test_*.py use_*.py if you plan to run them directly
```

## Configuration

The server is configured entirely through environment variables, typically set within an MCP client's configuration file (like the included `sample_mcp_config.json`).

### Core Configuration

- **`OPENAPI_SPEC`**: Path to the local OpenAPI specification file (e.g., [`semp-v2-swagger-monitor.json`](./semp-v2-swagger-monitor.json)). Used if `OPENAPI_SPEC_URL` is not provided or fails.
- **`OPENAPI_SPEC_URL`**: URL to fetch the OpenAPI specification from. Takes precedence over `OPENAPI_SPEC`.

### Single-Broker Configuration (Default)

If you are connecting to a single broker, you can use the following environment variables. This maintains backward compatibility with previous versions.

- **`SOLACE_SEMPV2_BASE_URL`**: Base URL for the Solace SEMPv2 API (e.g., `http://<host>:<port>`). Default: `http://localhost:8080`.
- **`SOLACE_SEMPV2_AUTH_METHOD`**: Authentication method (`basic`, `bearer`, or `none`).
- **`SOLACE_SEMPV2_USERNAME`**: Username for Basic Authentication.
- **`SOLACE_SEMPV2_PASSWORD`**: Password for Basic Authentication.
- **`SOLACE_SEMPV2_BEARER_TOKEN`**: Bearer token for Bearer Authentication.

### Multi-Broker Configuration

To connect to multiple brokers, you must first define a list of broker aliases.

- **`SOLACE_BROKERS_ALIAS`**: A comma-separated list of unique aliases for each broker (e.g., `broker_a,broker_b`).

For each alias, you must provide a full set of configuration variables by appending the alias name (in uppercase) to the standard variable names.

- **`SOLACE_SEMPV2_BASE_URL_<ALIAS>`**: The base URL for the broker (e.g., `SOLACE_SEMPV2_BASE_URL_BROKER_A`).
- **`SOLACE_SEMPV2_AUTH_METHOD_<ALIAS>`**: The authentication method for the broker.
- **`SOLACE_SEMPV2_USERNAME_<ALIAS>`**: The username for the broker.
- **`SOLACE_SEMPV2_PASSWORD_<ALIAS>`**: The password for the broker.
- **`SOLACE_SEMPV2_BEARER_TOKEN_<ALIAS>`**: The bearer token for the broker.

You can also specify a default broker to be used when no alias is provided in a tool call.

- **`SOLACE_BROKER_DEFAULT`**: The alias of the broker to use as the default (e.g., `broker_a`).

When using a multi-broker configuration, all tools will include a `broker_alias` parameter.
- If a default broker is defined, this parameter is **optional**.
- If no default broker is defined, this parameter is **required**.

**Example Multi-Broker `env` Configuration:**
```json
"env": {
    "SOLACE_BROKERS_ALIAS": "broker_a,broker_b",
    "SOLACE_BROKER_DEFAULT": "broker_a",

    "SOLACE_SEMPV2_BASE_URL_BROKER_A": "http://localhost:8080",
    "SOLACE_SEMPV2_USERNAME_BROKER_A": "admin",
    "SOLACE_SEMPV2_PASSWORD_BROKER_A": "admin",

    "SOLACE_SEMPV2_BASE_URL_BROKER_B": "http://otherhost:8080",
    "SOLACE_SEMPV2_USERNAME_BROKER_B": "user",
    "SOLACE_SEMPV2_PASSWORD_BROKER_B": "password"
}
```

### Authentication Configuration

- **`SOLACE_SEMPV2_AUTH_METHOD`**: Authentication method to use.
    - `basic` (Default): Use HTTP Basic Authentication. Requires `SOLACE_SEMPV2_USERNAME` and `SOLACE_SEMPV2_PASSWORD`.
    - `bearer`: Use Bearer Token Authentication. Requires `SOLACE_SEMPV2_BEARER_TOKEN`.
    - `none` or empty: No authentication.
- **`SOLACE_SEMPV2_USERNAME`**: Username for Basic Authentication.
- **`SOLACE_SEMPV2_PASSWORD`**: Password for Basic Authentication.
- **`SOLACE_SEMPV2_BEARER_TOKEN`**: Bearer token for Bearer Authentication.

### API Filtering Configuration

Control which API endpoints become tools using comma-separated lists:

- **`MCP_API_INCLUDE_METHODS`**: Only register tools matching these HTTP methods (e.g., `GET,POST`).
- **`MCP_API_EXCLUDE_METHODS`**: Do not register tools matching these HTTP methods (e.g., `DELETE,PUT`).
- **`MCP_API_INCLUDE_TAGS`**: Only register tools associated with these OpenAPI tags (e.g., `msgVpn,queue`).
- **`MCP_API_EXCLUDE_TAGS`**: Do not register tools associated with these OpenAPI tags (e.g., `deprecated`).
- **`MCP_API_INCLUDE_PATHS`**: Only register tools whose path contains any of these substrings (e.g., `/msgVpns/,/clients/`). Simple substring match.
- **`MCP_API_EXCLUDE_PATHS`**: Do not register tools whose path contains any of these substrings. Simple substring match.
- **`MCP_API_INCLUDE_TOOLS`**: Only register tools by name, coma separated (e.g., `getMsgVpnQueues,getMsgVpnQueue`). Simple string match.
- **`MCP_API_EXCLUDE_TOOLS`**: Only not register tools, by name coma separated (e.g., `getMsgVpnQueues,getMsgVpnQueue`). Simple string match.

*Note: If conflicting include/exclude rules are set (e.g., including and excluding the same method), exclusion takes precedence.*

### Logging Configuration

- **`MCP_LOG_LEVEL`**: Sets the logging level. Valid values are `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. Default: `INFO`.
- **`MCP_LOG_FILE`**: Path to the log file (e.g., `solace_mcp_server.log`). If set, logs are written here using a rotating file handler (10MB limit, 5 backups). If not set, logs go to `stderr`.
- **`MCP_LOG_DISABLE`**: Set to `true` to disable logging entirely. Default: `false`.



## Integration with Solace Agent Mesh
This MCP server is fully compatible with the Solace Agent Mesh ecosystem and can be used as a backend for the SAM MCP Server plugin, allowing SAM agents to interact with Solace event brokers through a consistent interface.
For installation and configuration details, please refer to the documentation at [Solace Agent Mesh MCP Server Plugin GitHub repository](https://github.com/SolaceLabs/solace-agent-mesh-core-plugins/tree/main/sam-mcp-server)


### Usage

The server is designed to be run by an MCP client such as Solace Agent Mesh MCP Server Plugin using a configuration properties similar to the one below. The client will manage the server's lifecycle and communication over `stdio`.
If you need to run the server using Solace Agent Mesh MCP Server Plugin follow installation instructions from [Solace Agent Mesh MCP Server Plugin GitHub repository](https://github.com/SolaceLabs/solace-agent-mesh-core-plugins/tree/main/sam-mcp-server)

Configuration for the MCP Agent can be performed using environment variables:

```bash 
# Set environment variables for MCP AGENT. Assuming the instance name of your MCP agent being configured is SOLACE_SEMP:   
...
SOLACE_SEMP_MCP_SERVER_COMMAND="python3 /<path to your mcp script location>/solace_monitoring_mcp_server.py"
SOLACE_SEMP_MCP_SERVER_DESCRIPTION="This server provides access to the Solace broker over SEMP v2. Follow instructions. USE 'count' parameter for the pagination, set 'count' to 25. USE default pagination mechanism using 'cursor' parameter only when tried using count and it fails. Each time you determine that more pages are available keep fetching more pages until you fetched all results or requested number of results."
```
> ℹ️ *Info:* We recommend to add system prompt like one above as part of the MCP server description environment variable  

```bash
# Set environment variables for MCP server (examples)
export OPENAPI_SPEC="semp-v2-swagger-monitor.json"
export SOLACE_SEMPV2_BASE_URL="http://localhost:8080"
export SOLACE_SEMPV2_AUTH_METHOD="basic"
export SOLACE_SEMPV2_USERNAME="admin"
export SOLACE_SEMPV2_PASSWORD="admin"
export MCP_LOG_LEVEL="INFO"
export MCP_LOG_FILE="solace_mcp_server.log"
...
```
To optimize both performance and LLM cost efficiency, limit exposed tools to only those essential for your use case such as i.e:
```bash
"MCP_API_INCLUDE_TOOLS": "getMsgVpnQueues,getMsgVpnQueue,getMsgVpnQueueTxFlows,getMsgVpnClients,getMsgVpnClient,getMsgVpnClientConnections,getMsgVpn,getMsgVpns,getMsgVpnClientTxFlows,getMsgVpnClientTxFlow"
```

If you need to run the server directly for testing (outside an MCP client) set environment variables or use `.env` file and run:
```bash
# Run the server command
python3 solace_monitoring_mcp_server.py
```

For testing, you can use also `.env` file located in the current working server execution directory to provide all needed environment variables. 

The server will then listen for MCP JSON-RPC messages on `stdin` and send responses to `stdout`.

## How it Works

1.  **Initialization**: Reads environment variables for configuration. Sets up logging using the LoggingConfig handler.
2.  **Load Spec**: Fetches the OpenAPI spec from the configured URL or file path.
3.  **Tool Registration**: Parses the OpenAPI `paths` section. For each operation (`operationId`), it checks against the filtering rules (methods, tags, paths). If allowed, it builds a JSON schema for the input parameters (path, query, header, body) and prepares a `Tool` object.
5.  **MCP Protocol**: Implements Model Context Protocol version "2024-11-05" for standardized communication with MCP clients.
6.  **Run**: Starts the server, which handles `stdio` communication according to the MCP protocol.
7.  **Tool Call**: When the MCP client sends a `mcp.call_tool` request:
    *   The server validates the request against the registered tool's input schema.
    *   It parses the parameters and prepares the API URL, query parameters, headers (including authentication), and body.
    *   It makes the HTTP request to the Solace SEMPv2 API using the `requests` library.
    *   Handles the API response (success, error, empty content) and formats it for the MCP response.
    *   Returns the result or sends an appropriate error message, which is formatted into a JSON-RPC response.

## Example Scripts

- `tests/test_mcp_server.py`: Unit tests covering configuration, tool registration, API filtering, and MCP message handling.
- `examples/mcp_server_config_example.py`: Script demonstrates how to launch the server via configuration manually.
- `sample_mcp_config.json`: demonstrates a simple MCP client configuration file for MCP client tools like VS Code Copilot Chat, it is also used in the previous script 
