# Solace Event Portal Designer MCP Server

> ⚠️ **RELEASE CANDIDATE** - Version: 0.1.0rc1

This project provides a Model Context Protocol (MCP) server for interacting with the Solace Event Portal Designer API. Designer enables you to design and view all of the objects in your event-driven architecture (EDA). You can use Designer to create events, associate payload schemas, specify the events that applications publish and subscribe to, and create event APIs and Event API Products to share events. See the [Event Portal Designer Documentation](https://docs.solace.com/Cloud/Event-Portal/event-portal-designer-tool.htm) for more info about Designer.

## Quick Start

1. **Get your Solace API Token** from the [Solace Cloud Console](https://console.solace.cloud/). Ensure the token has **"Event Portal > Designer > Read"** permissions (or appropriate write permissions if you need to create/modify objects).

2. **Add to your MCP client configuration** (e.g., Claude Desktop, Cline):

```json
{
  "mcpServers": {
    "solace-event-portal-designer": {
      "command": "uvx",
      "args": ["solace-event-portal-designer-mcp"],
      "env": {
        "SOLACE_API_TOKEN": "<your-api-token>"
      }
    }
  }
}
```

3. **Restart your MCP client** and start asking questions about your Event Portal!

**Example prompts:**
- "List all application domains in my Event Portal"
- "Show me events in the OrderManagement domain"

## Installation

### Recommended: No installation needed

If you use `uvx` in your MCP client configuration (as shown above), the package will be automatically downloaded when your client starts.

### Alternative: Pre-install with pip

```bash
# Install from PyPI
pip install solace-event-portal-designer-mcp

# Or install from Git
pip install git+https://github.com/SolaceLabs/solace-platform-mcp.git#subdirectory=solace-event-portal-designer-mcp
```

Use this if your MCP client doesn't support `uvx` or you prefer pre-installing. Then use `"command": "solace-ep-designer-mcp"` in your configuration instead of `uvx`.

## Configuration

See [examples/](examples/) for more configuration examples.

### Multi-Region Support

By default, the server connects to the US region. If your Solace Cloud account is in a different region, set the `SOLACE_API_BASE_URL` environment variable in your MCP client configuration:

| Region | Base URL |
|--------|----------|
| United States (default) | `https://api.solace.cloud` |
| Australia | `https://api.solacecloud.au` |
| Europe | `https://api.solacecloud.eu` |
| Singapore | `https://api.solacecloud.sg` |

**Example configuration for Australia:**
```json
{
  "mcpServers": {
    "solace-event-portal-designer": {
      "command": "uvx",
      "args": ["solace-event-portal-designer-mcp"],
      "env": {
        "SOLACE_API_TOKEN": "<your-token>",
        "SOLACE_API_BASE_URL": "https://api.solacecloud.au"
      }
    }
  }
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SOLACE_API_TOKEN` | Yes | - | Your Solace API token |
| `SOLACE_API_BASE_URL` | No | `https://api.solace.cloud` | Base URL for Solace Cloud API |

See [Managing your API Tokens](https://docs.solace.com/Cloud/ght_api_tokens.htm) for details on creating a token. Ensure the API Token has at least "Event Portal > Designer > Read" permissions.

## Available Tools

This server provides **35 tools** for full CRUD operations on Solace Event Portal Designer objects:

- **Application Domains** - Create, read, update, delete, and list domains
- **Applications** - Manage applications and their versions
- **Events** - Manage events and their versions
- **Schemas** - Manage schemas and their versions
- **AsyncAPI Export** - Generate AsyncAPI specifications from application versions

### Example Usage

Use your AI assistant to:
- "List all events in my application domain"
- "Create a new schema for order events"
- "Export an AsyncAPI spec for application version X"
- "Show me all applications that publish the OrderCreated event"

## Troubleshooting

### Verify your setup is working

After configuring your MCP client, verify the connection:

1. **Restart your MCP client** (e.g., Claude Desktop, Cline)
2. **Ask a simple question** like: "List my application domains"
3. If it works, you'll see results from Event Portal

### Common Issues

**"API token not found" or authentication errors:**
- Ensure `SOLACE_API_TOKEN` is set correctly in your MCP client configuration
- Verify your token hasn't expired in the [Solace Cloud Console](https://console.solace.cloud/)
- Check the token has "Event Portal > Designer > Read" permissions

**"Connection refused" or timeout errors:**
- Check if you're using the correct region via `SOLACE_API_BASE_URL` (see [Multi-Region Support](#multi-region-support))
- Verify your network allows connections to `api.solace.cloud` (or your region's URL)

**"Command not found" errors:**
- If using `uvx`, ensure you have Python 3.10+ and `uv` installed
- If using pip install, run `which solace-ep-designer-mcp` to verify installation

## Development

This project uses [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management.

```bash
# Clone repo
git clone https://github.com/SolaceLabs/solace-platform-mcp.git
cd solace-platform-mcp/solace-event-portal-designer-mcp

# Install dependencies
uv sync

# Install in editable mode
uv pip install -e .

# Make changes, test immediately (no rebuild needed)
```

### Running Tests

```bash
# Install development dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=solace_event_portal_designer_mcp --cov-report=term-missing
```

### Manual Testing

```bash
# Verify installation
which solace-ep-designer-mcp

# Test server starts (will wait for MCP protocol input on stdin)
export SOLACE_API_TOKEN="your-token"
solace-ep-designer-mcp
# Press Ctrl+C to exit
```
