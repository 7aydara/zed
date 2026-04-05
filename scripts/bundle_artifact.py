import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

def run_command(cmd, cwd=None, env=None):
    print(f"[*] Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd, env=env)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error: {e.stderr}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Bundle a React project into a single HTML artifact.")
    parser.add_argument("project_name", help="Name of the project directory")
    args = parser.parse_args()

    project_path = Path(args.project_name)
    if not project_path.exists():
        print(f"[!] Error: Path '{args.project_name}' does not exist.")
        sys.exit(1)

    print(f"[*] Bundling artifact project: {args.project_name} ...")

    # 1. Install vite-plugin-singlefile
    print("[*] Installing bundling plugin...")
    run_command("npm install -D vite-plugin-singlefile", cwd=project_path)

    # 2. Setup vite.config.ts
    print("[*] Configuring Vite to bundle single file...")
    vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteSingleFile } from 'vite-plugin-singlefile'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), viteSingleFile()],
})
"""
    with open(project_path / "vite.config.ts", "w", encoding="utf-8") as f:
        f.write(vite_config)

    # 3. Build the project
    print("[*] Building the project...")
    run_command("npm run build", cwd=project_path)

    # 4. Extract bundle.html
    dist_html = project_path / "dist" / "index.html"
    if not dist_html.exists():
        print("[!] Error: Build failed to produce index.html in dist/")
        sys.exit(1)

    output_file = project_path / "bundle.html"
    shutil.copy2(dist_html, output_file)

    print(f"\n[+] Successfully bundled artifact into '{output_file}'!")
    print(f"[+] You can now open this file in any browser to view your artifact.")

if __name__ == "__main__":
    main()
