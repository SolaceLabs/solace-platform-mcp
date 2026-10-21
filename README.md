# Solace Platform MCP Servers

Solace offers several [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers that let AI applications and agents work with Solace products. With an MCP server, you can use natural language in an AI application or agent to work with Solace products.

## Available MCP servers

You can choose the MCP servers based on the Solace products you work with:

- **Solace event brokers** (queues, clients, Message VPNs): You can use the [Solace Broker MCP Server](https://github.com/SolaceProducts/solace-broker-mcp).
- **Event Portal designs in Solace Cloud** (applications, events, schemas): You can use the [Solace Event Portal Designer MCP Server](solace-event-portal-designer-mcp/).

| Server | What it does | Availability | Support |
|---|---|---|---|
| [Solace Broker MCP Server](https://github.com/SolaceProducts/solace-broker-mcp) | Monitors and manages Solace event brokers | Generally available (GA) | Supported by Solace |
| [Solace Event Portal Designer MCP Server](solace-event-portal-designer-mcp/) | Reads, creates, updates and deletes Event Portal Designer objects (application domains, applications, events, schemas) and exports AsyncAPI specifications, from your AI application | Early Access (EA) | The Event Portal team takes feedback and bug reports through [GitHub issues](https://github.com/SolaceLabs/solace-platform-mcp/issues) |

Each MCP server has its own installation and configuration steps that are available in its README file.

### Deprecated servers

The Solace Monitoring MCP Server is deprecated and no longer maintained. Use the [Solace Broker MCP Server](https://github.com/SolaceProducts/solace-broker-mcp) instead. See [solace-monitoring-mcp-server](solace-monitoring-mcp-server/) for details.

## Disclaimer

MCP servers are used by AI applications that run on large language models (LLMs), which are non-deterministic and may change over time. Results can vary between runs and may be incorrect, insecure, incomplete, or unsuitable for your environment. Some MCP servers can create, update, or delete resources. You are responsible for reviewing, testing, and validating all results and actions before use, especially in production environments.

## Contributing

To contribute, see [CONTRIBUTING.md](CONTRIBUTING.md). Thanks to everyone who has [contributed](https://github.com/SolaceLabs/solace-platform-mcp/graphs/contributors) to this project.

## License

This project is licensed under the Apache 2.0 License. See [LICENSE.txt](LICENSE.txt).
