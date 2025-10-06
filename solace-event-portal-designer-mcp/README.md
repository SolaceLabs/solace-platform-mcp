# Solace Event Portal Designer MCP Server

> ⚠️ **RELEASE CANDIDATE** - Version: 0.1.0-rc1

This project provides a Model Context Protocol (MCP) server for interacting with the Solace Event Portal Designer API. Designer enables you to design and view all of the objects in your event-driven architecture (EDA). You can use Designer to create events, associate payload schemas, specify the events that applications publish and subscribe to, and create event APIs and Event API Products to share events. See the [Event Portal Designer Documentation](https://docs.solace.com/Cloud/Event-Portal/event-portal-designer-tool.htm) for more info about Designer.

## Installation

### From PyPI (when published)
```bash
pip install solace-event-portal-designer-mcp==0.1.0-rc1
```

### From Source (Development)
```bash
cd solace-event-portal-designer-mcp
uv pip install -e .
```

### From Wheel File
```bash
pip install solace_event_portal_designer_mcp-0.1.0rc1-py3-none-any.whl
```

### From Git
```bash
pip install git+https://github.com/SolaceLabs/solace-platform-mcp.git#subdirectory=solace-event-portal-designer-mcp
```

## Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "solace-event-portal-designer": {
      "command": "solace-ep-designer-mcp",
      "env": {
        "SOLACE_API_TOKEN": "<your-solace-api-token>"
      }
    }
  }
}
```

See [examples/](examples/) for more configuration examples.

### Multi-Region Support

If your Solace home cloud is in a different region, set the `SOLACE_API_BASE_URL` environment variable:

**Australia:**
```json
{
  "command": "solace-ep-designer-mcp",
  "env": {
    "SOLACE_API_TOKEN": "<your-token>",
    "SOLACE_API_BASE_URL": "https://api.solacecloud.au"
  }
}
```

**Europe:**
```json
"SOLACE_API_BASE_URL": "https://api.solacecloud.eu"
```

**Singapore:**
```json
"SOLACE_API_BASE_URL": "https://api.solacecloud.sg"
```

**United States (Default):**
```json
"SOLACE_API_BASE_URL": "https://api.solace.cloud"
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SOLACE_API_TOKEN` | Yes | - | Your Solace API token |
| `SOLACE_API_BASE_URL` | No | `https://api.solace.cloud` | Base URL for Solace Cloud API |

See [Managing your API Tokens](https://docs.solace.com/Cloud/ght_api_tokens.htm) for details on creating a token. Ensure the API Token has at least "Event Portal > Designer > Read" permissions.

## Available Endpoints

This MCP server exposes 8 Event Portal Designer API endpoints:

- Application Domains (`/api/v2/architecture/applicationDomains`)
- Applications (`/api/v2/architecture/applications`)
- Application Versions (`/api/v2/architecture/applicationVersions`)
- Events (`/api/v2/architecture/events`)
- Event Versions (`/api/v2/architecture/eventVersions`)
- Schemas (`/api/v2/architecture/schemas`)
- Schema Versions (`/api/v2/architecture/schemaVersions`)
- AsyncAPI export

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

### Testing

```bash
# Verify installation
which solace-ep-designer-mcp

# Test server starts (will wait for MCP protocol input on stdin)
export SOLACE_API_TOKEN="your-token"
solace-ep-designer-mcp
# Press Ctrl+C to exit
```
