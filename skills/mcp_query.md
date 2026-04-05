---
name: mcp_query
description: MCP Tool. Execute a read-only SQL query and return results. CRITICAL: You must pass a STRICTLY FORMATTED VALID JSON STRING containing your arguments. Avoid unescaped quotes! Schema reference: {'type': 'object', 'properties': {'sql': {'type': 'string', 'description': 'SQL query to execute (SELECT statements only)'}}, 'required': ['sql'], 'additionalProperties': False, '$schema': 'http://json-schema.org/draft-07/schema#'}
arguments: payload
---
!`"C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\HP\Desktop\Zeus - Projets AI\zed\invoke_mcp.py" "C:\Program Files\nodejs\npx.CMD" "-y mcp-server-sqlite --db temp.db" "query" "${payload}"`
