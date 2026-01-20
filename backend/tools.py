import json
from typing import Any, Dict, List

from db import get_schema, list_tables, run_sql

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List available tables in the database.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "Get column metadata for specific tables.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Table names to inspect.",
                    }
                },
                "required": ["tables"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Execute a read-only SQL SELECT query against the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL SELECT to execute."},
                    "limit": {
                        "type": "integer",
                        "description": "Maximum rows to return (default 50).",
                        "minimum": 1,
                        "maximum": 200,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def call_tool(name: str, arguments: Dict[str, Any]) -> str:
    try:
        if name == "list_tables":
            data = list_tables()
        elif name == "get_schema":
            tables = arguments.get("tables", [])
            data = get_schema(tables)
        elif name == "run_sql":
            query = arguments.get("query")
            limit = int(arguments.get("limit", 50)) if arguments.get("limit") else 50
            data = run_sql(query, limit)
        else:
            return json.dumps({"error": f"Unknown tool {name}"})
        return json.dumps(data, default=str)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)})
