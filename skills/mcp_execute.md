---
name: mcp_execute
description: MCP Tool. Execute a SQL statement that modifies data (INSERT, UPDATE, DELETE, CREATE, DROP). CRITICAL: You must pass a STRICTLY FORMATTED VALID JSON STRING containing your arguments. Avoid unescaped quotes! Schema reference: {'type': 'object', 'properties': {'sql': {'type': 'string', 'description': 'SQL statement to execute'}}, 'required': ['sql'], 'additionalProperties': False, '$schema': 'http://json-schema.org/draft-07/schema#'}
arguments: payload
---
!`"C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\HP\Desktop\Zeus - Projets AI\zed\invoke_mcp.py" "C:\Program Files\nodejs\npx.CMD" "-y mcp-server-sqlite --db temp.db" "execute" "${payload}"`
