# Solace Platform MCP Servers

This page lists the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) servers for Solace products. MCP servers let AI assistants and agents work with Solace products through natural language.

## Available MCP servers

Pick the server by what you work with:

- **Solace event brokers** (queues, clients, Message VPNs): use the [Solace Broker MCP Server](https://github.com/SolaceProducts/solace-broker-mcp).
- **Event Portal designs in Solace Cloud** (applications, events, schemas): use the [Solace Event Portal Designer MCP Server](solace-event-portal-designer-mcp/).

| Server | What it does | Availability | Support |
|---|---|---|---|
| [Solace Broker MCP Server](https://github.com/SolaceProducts/solace-broker-mcp) | Monitors and manages Solace event brokers | Generally available (GA) | Supported by Solace |
| [Solace Event Portal Designer MCP Server](solace-event-portal-designer-mcp/) | Reads, creates, updates and deletes Event Portal Designer objects (application domains, applications, events, schemas) and exports AsyncAPI specifications, from your AI assistant | Early Access (EA) | The Event Portal team takes feedback and bug reports through [GitHub issues](https://github.com/SolaceLabs/solace-platform-mcp/issues) |

Each server's README has its installation and configuration instructions.

### Retired servers

The Solace Monitoring MCP Server has been retired. Use the [Solace Broker MCP Server](https://github.com/SolaceProducts/solace-broker-mcp) instead. See [solace-monitoring-mcp-server](solace-monitoring-mcp-server/) for details.

## Contributing

To contribute, see [CONTRIBUTING.md](CONTRIBUTING.md). Thanks to everyone who has [contributed](https://github.com/SolaceLabs/solace-platform-mcp/graphs/contributors) to this project.

## License

This project is licensed under the Apache 2.0 License. See [LICENSE.txt](LICENSE.txt).
