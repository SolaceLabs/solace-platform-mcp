#!/bin/bash
# Installation script for the Solace SEMPv2 MCP Server

echo "Installing Solace SEMPv2 MCP Server..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
required_version="3.10"

# Fix for version comparison - use proper version comparison
python3 -c "import sys; sys.exit(0 if tuple(map(int, '$python_version'.split('.'))) >= tuple(map(int, '$required_version'.split('.'))) else 1)"
if [ $? -ne 0 ]; then
    echo "Error: Python $required_version or higher is required. You have Python $python_version."
    exit 1
fi

echo "Python version $python_version detected."

# Install required packages from requirements.txt
echo "Installing required Python packages from requirements.txt..."
python3 -m pip install -r requirements.txt

# Make scripts executable
echo "Making scripts executable..."
chmod +x solace_monitoring_mcp_server.py
chmod +x tests/test_mcp_server.py
chmod +x examples/mcp_server_config_example.py

echo "Installation complete!"
echo ""
echo "You can now run the server using:"
echo "  python3 solace_monitoring_mcp_server.py"
echo ""
echo "Or try the example scripts:"
echo "  python3 tests/test_mcp_server.py"
echo "  python3 examples/mcp_server_config_example.py"
echo ""
echo "To use this server with an MCP client, add the configuration from sample_mcp_config.json to your MCP client's configuration."
echo ""
echo "Note: You may need to update the base URL, username, and password in sample_mcp_config.json to match your Solace PubSub+ broker configuration."
