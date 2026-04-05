---
name: mcp_transaction
description: MCP Tool. Execute multiple SQL statements within a transaction. CRITICAL: You must pass a STRICTLY FORMATTED VALID JSON STRING containing your arguments. Avoid unescaped quotes! Schema reference: {'type': 'object', 'properties': {'statements': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Array of SQL statements to execute in transaction'}}, 'required': ['statements'], 'additionalProperties': False, '$schema': 'http://json-schema.org/draft-07/schema#'}
arguments: payload
---
!`"C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\HP\Desktop\Zeus - Projets AI\zed\invoke_mcp.py" "C:\Program Files\nodejs\npx.CMD" "-y mcp-server-sqlite --db temp.db" "transaction" "${payload}"`
