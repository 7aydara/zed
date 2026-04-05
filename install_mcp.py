import sys
import os
import asyncio
import shlex
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import argparse
import shutil
import traceback

SKILLS_DIR = Path(__file__).parent / "skills"
PYTHON_BIN = sys.executable
INVOKE_SCRIPT = Path(__file__).parent / "invoke_mcp.py"

async def main():
    parser = argparse.ArgumentParser(description="Extract tools from an MCP server and install them as Zed Skills.")
    parser.add_argument("--cmd", required=True, help="Server command (e.g. npx, node, python)")
    parser.add_argument("--args", required=True, help="Server arguments as a single string")
    
    args = parser.parse_args()
    
    server_cmd = shutil.which(args.cmd) or args.cmd
    # Important: some windows systems might fail if the server command string is complex, but stdio_client handles it best via proper subprocess.
    server_args = shlex.split(args.args)
    
    env = os.environ.copy()
    server_params = StdioServerParameters(command=server_cmd, args=server_args, env=env)
    
    print(f"[*] Booting MCP Server: {server_cmd} {args.args} ...")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("[*] Server connected. Fetching tools...")
                response = await session.list_tools()
                
                tools = response.tools
                if not tools:
                    print("[!] No tools found on this given MCP server.")
                    sys.exit(0)
                    
                SKILLS_DIR.mkdir(parents=True, exist_ok=True)
                
                for t in tools:
                    t_name = t.name
                    # Make it completely valid for Zed naming conventions
                    safe_name = f"mcp_{t_name.replace('-', '_')}"
                    
                    desc = (t.description or "No description provided").replace('\n', ' ')
                    schema_str = str(t.inputSchema) if hasattr(t, 'inputSchema') else "None"
                    
                    md_content = f"""---
name: {safe_name}
description: MCP Tool. {desc}. CRITICAL: You must pass a STRICTLY FORMATTED VALID JSON STRING containing your arguments. Avoid unescaped quotes! Schema reference: {schema_str}
arguments: payload
---
!`"{PYTHON_BIN}" "{INVOKE_SCRIPT}" "{server_cmd}" "{args.args}" "{t_name}" "${{payload}}"`
"""
                    file_path = SKILLS_DIR / f"{safe_name}.md"
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(md_content)
                        
                    print(f"  [+] Extracted tool '{t_name}' -> {safe_name}.md")
                    
        print(f"\n[+] Successfully bridged MCP server into Zed's Hot-Reload skills!")
        
    except Exception as e:
        import traceback
        print(f"[!] Errored during MCP introspection: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
