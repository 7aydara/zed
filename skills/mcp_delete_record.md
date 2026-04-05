---
name: mcp_delete_record
description: MCP Tool. Delete records from a table. CRITICAL: You must pass a STRICTLY FORMATTED VALID JSON STRING containing your arguments. Avoid unescaped quotes! Schema reference: {'type': 'object', 'properties': {'table': {'type': 'string', 'description': 'Table name'}, 'where': {'type': 'string', 'description': 'WHERE clause to identify records to delete'}}, 'required': ['table', 'where'], 'additionalProperties': False, '$schema': 'http://json-schema.org/draft-07/schema#'}
arguments: payload
---
!`"C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\HP\Desktop\Zeus - Projets AI\zed\invoke_mcp.py" "C:\Program Files\nodejs\npx.CMD" "-y mcp-server-sqlite --db temp.db" "delete-record" "${payload}"`
