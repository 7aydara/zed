---
name: mcp_drop_table
description: MCP Tool. Delete a table from the database. CRITICAL: You must pass a STRICTLY FORMATTED VALID JSON STRING containing your arguments. Avoid unescaped quotes! Schema reference: {'type': 'object', 'properties': {'name': {'type': 'string', 'description': 'Table name to drop'}, 'ifExists': {'type': 'boolean', 'default': True, 'description': 'Add IF EXISTS clause'}}, 'required': ['name'], 'additionalProperties': False, '$schema': 'http://json-schema.org/draft-07/schema#'}
arguments: payload
---
!`"C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\HP\Desktop\Zeus - Projets AI\zed\invoke_mcp.py" "C:\Program Files\nodejs\npx.CMD" "-y mcp-server-sqlite --db temp.db" "drop-table" "${payload}"`
