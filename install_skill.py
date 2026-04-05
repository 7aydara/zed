import os
import sys
import argparse
import urllib.request
import urllib.error
import re
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"

def install_skill(url_or_path: str):
    print(f"[*] Fetching skill from: {url_or_path}")
    
    content = ""
    # Check if Local or URL
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        try:
            req = urllib.request.Request(url_or_path, headers={'User-Agent': 'Zed-Skill-Installer/1.0'})
            with urllib.request.urlopen(req) as resp:
                content = resp.read().decode('utf-8')
        except urllib.error.URLError as e:
            print(f"[!] Failed to download skill from URL: {e}")
            sys.exit(1)
    else:
        try:
            with open(url_or_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            print(f"[!] Failed to read local file: {e}")
            sys.exit(1)

    # Basic Validation
    if not content.startswith("---"):
        print("[!] Invalid format: A valid Claude Code skill must start with YAML frontmatter (---).")
        sys.exit(1)
        
    lines = content.split('\n')
    frontmatter_end = -1
    for i in range(1, len(lines)):
        if lines[i].startswith("---"):
            frontmatter_end = i
            break
            
    if frontmatter_end == -1:
        print("[!] Invalid format: Could not find the end of the YAML frontmatter (---).")
        sys.exit(1)
        
    # Extract Name for file renaming
    skill_name = None
    for line in lines[1:frontmatter_end]:
        match = re.match(r'^name:\s*(.+)$', line.strip())
        if match:
            skill_name = match.group(1).strip()
            break
            
    if not skill_name:
        print("[!] Invalid format: The YAML frontmatter must contain a 'name: <name>' field.")
        sys.exit(1)
        
    # Security Prompting
    print("\n--- SKILL CONTENT PREVIEW ---")
    print("\n".join(lines[:frontmatter_end + 1]))
    print("...")
    commands = [line for line in lines[frontmatter_end+1:] if line.strip().startswith("!")]
    if commands:
        print("\n[WARNING] This skill executes the following local bash commands:")
        for c in commands:
            print(f"  {c}")
            
    print("-" * 30)
    conf = input(f"Are you sure you want to install '{skill_name}'? [Y/n] ")
    if conf.lower() not in ['', 'y', 'yes']:
        print("[*] Installation aborted.")
        sys.exit(0)
        
    # Save the skill
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    
    safe_name = "".join([c for c in skill_name if c.isalnum() or c in "_-"])
    file_path = SKILLS_DIR / f"{safe_name}.md"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"\n[+] Successfully installed skill '{safe_name}' to {file_path}")
    print("[+] Zed will automatically hot-reload this skill on your next request!")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install a Claude Code formatted skill for Zed")
    parser.add_argument("source", help="URL or local path to the .md skill file")
    args = parser.parse_args()
    
    install_skill(args.source)
