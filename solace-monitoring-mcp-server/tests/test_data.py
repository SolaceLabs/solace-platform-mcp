#!/usr/bin/env python3
"""
Test data for Solace SEMPv2 MCP Server tests.

This module contains test fixtures that are used by the unit tests,
separating them from the test logic for better maintainability.
"""

# Dummy OpenAPI specification for testing
DUMMY_OAS_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "version": "1.0.0"
    },
    "paths": {
        "/items": {
            "get": {
                "operationId": "getItems",
                "summary": "Get all items",
                "tags": ["items", "read"],
                "responses": {"200": {"description": "Success"}}
            },
            "post": {
                "operationId": "createItem",
                "summary": "Create a new item",
                "tags": ["items", "write"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "value": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "responses": {"201": {"description": "Created"}}
            }
        },
        "/items/{itemId}": {
            "get": {
                "operationId": "getItemById",
                "summary": "Get item by ID",
                "tags": ["items", "read"],
                "parameters": [
                    {
                        "name": "itemId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {"200": {"description": "Success"}}
            },
            "delete": {
                "operationId": "deleteItem",
                "summary": "Delete an item",
                "tags": ["items", "write", "deprecated"],
                "parameters": [
                    {
                        "name": "itemId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {"204": {"description": "Deleted"}}
            }
        },
        "/config/broker": {
            "get": {
                "operationId": "getBrokerConfig",
                "summary": "Get broker configuration",
                "tags": ["config", "read"],
                "responses": {"200": {"description": "Success"}}
            }
        },
        "/msgVpns/queues": {
            "get": {
                "operationId": "getMsgVpnQueues",
                "summary": "Get all queues across message VPNs",
                "tags": ["msgVpns", "queues", "read"],
                "responses": {"200": {"description": "Success"}}
            }
        }
    }
}