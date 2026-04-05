---
name: mcp_describe_table
description: MCP Tool. Get detailed information about a table structure. CRITICAL: You must pass a STRICTLY FORMATTED VALID JSON STRING containing your arguments. Avoid unescaped quotes! Schema reference: {'type': 'object', 'properties': {'tableName': {'type': 'string', 'description': 'Name of the table to describe'}}, 'required': ['tableName'], 'additionalProperties': False, '$schema': 'http://json-schema.org/draft-07/schema#'}
arguments: payload
---
!`"C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\HP\Desktop\Zeus - Projets AI\zed\invoke_mcp.py" "C:\Program Files\nodejs\npx.CMD" "-y mcp-server-sqlite --db temp.db" "describe-table" "${payload}"`
