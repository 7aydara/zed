import sys
import json
import asyncio
import shlex
import os
import shutil
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    if len(sys.argv) < 5:
        print("Usage: python invoke_mcp.py <server_cmd> <server_args_str> <tool_name> <payload>")
        sys.exit(1)
        
    server_cmd = shutil.which(sys.argv[1]) or sys.argv[1]
    server_args = shlex.split(sys.argv[2])
    tool_name = sys.argv[3]
    payload_raw = sys.argv[4]
    
    try:
        tool_args = json.loads(payload_raw) if payload_raw.strip() else {}
    except json.JSONDecodeError:
        # Fallback if string isn't JSON. We wrap it in a 'prompt' key as it's common.
        tool_args = {"prompt": payload_raw}

    # Pass environment variables, sometimes needed by MCP servers
    env = os.environ.copy()
    
    server_params = StdioServerParameters(command=server_cmd, args=server_args, env=env)
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=tool_args)
                
                # Render content
                if result.isError:
                    print(f"Error returned from tool '{tool_name}':")
                    
                for c in result.content:
                    if c.type == 'text':
                        print(c.text)
                    else:
                        print(c)
    except Exception as e:
        print(f"MCP Invocation Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
