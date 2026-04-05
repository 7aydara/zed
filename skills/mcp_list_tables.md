---
name: mcp_list_tables
description: MCP Tool. List all tables in the database. CRITICAL: You must pass a STRICTLY FORMATTED VALID JSON STRING containing your arguments. Avoid unescaped quotes! Schema reference: {'$schema': 'http://json-schema.org/draft-07/schema#', 'type': 'object', 'properties': {}}
arguments: payload
---
!`"C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\HP\Desktop\Zeus - Projets AI\zed\invoke_mcp.py" "C:\Program Files\nodejs\npx.CMD" "-y mcp-server-sqlite --db temp.db" "list-tables" "${payload}"`
