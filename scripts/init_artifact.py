import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, cwd=None, env=None):
    if env is None:
        env = os.environ.copy()
    env["CI"] = "true"
    print(f"[*] Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, cwd=cwd, env=env, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[!] Error: {e.stderr}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Initialize a new React project for Zed artifacts.")
    parser.add_argument("project_name", help="Name of the project directory")
    args = parser.parse_args()

    project_path = Path(args.project_name)
    if project_path.exists():
        print(f"[!] Error: Path '{args.project_name}' already exists.")
        sys.exit(1)

    print(f"[*] Initializing artifact project: {args.project_name} ...")

    # 1. Create Vite project (React + TS)
    # Using --template react-ts and non-interactive mode
    run_command(f"npx -y create-vite@latest {args.project_name} --template react-ts")

    # 2. Install dependencies
    print("[*] Installing core dependencies...")
    run_command("npm install", cwd=project_path)

    # 3. Install Tailwind CSS and related tools
    print("[*] Installing Tailwind CSS and dependencies...")
    run_command("npm install -D tailwindcss postcss autoprefixer", cwd=project_path)
    run_command("npx tailwindcss init -p", cwd=project_path)

    # 4. Configure Tailwind
    print("[*] Configuring Tailwind CSS...")
    tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
    with open(project_path / "tailwind.config.js", "w", encoding="utf-8") as f:
        f.write(tailwind_config)

    # 5. Set up CSS
    print("[*] Setting up styles...")
    css_content = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
    # Create src directory if it doesn't exist (vite creates it)
    with open(project_path / "src" / "index.css", "w", encoding="utf-8") as f:
        f.write(css_content)

    # 6. Basic App.tsx cleanup
    print("[*] Cleaning up App.tsx...")
    app_content = """import React from 'react'

function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">Zed Artifact</h1>
      <p className="text-lg text-gray-600">Start building your React artifact here!</p>
    </div>
  )
}

export default App
"""
    with open(project_path / "src" / "App.tsx", "w", encoding="utf-8") as f:
        f.write(app_content)

    print(f"\n[+] Successfully initialized artifact project in '{args.project_name}'!")
    print(f"[+] You can now edit files and run 'python scripts/bundle_artifact.py {args.project_name}' to build.")

if __name__ == "__main__":
    main()
