import os
import json
import logging
import requests
import datetime
import shutil
from pathlib import Path
import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("migrate")

vault_path = config.VAULT_PATH
categories = ["00_Core", "10_People", "20_Projects", "30_Concepts", "90_Journal", "_Templates"]

def ensure_folders():
    for cat in categories:
        (vault_path / cat).mkdir(parents=True, exist_ok=True)
    log.info("Ensured all 5 buckets and _Templates exist.")

def migrate_file(filepath: Path):
    if filepath.name.startswith("."):
        return
    
    content = filepath.read_text(encoding="utf-8", errors="replace")
    
    # If it already has YAML frontmatter, we skip (or handle if it's already migrated).
    if content.startswith("---\n"):
        log.info(f"Skipping {filepath.name}, already has frontmatter.")
        # Try to move to 30_Concepts if it's in Nodes
        if "Nodes" in filepath.parts:
            dest = vault_path / "30_Concepts" / filepath.name
            shutil.move(str(filepath), str(dest))
            log.info(f"Moved {filepath.name} to 30_Concepts")
        return

    prompt = (
        f"File Title: {filepath.stem}\n"
        f"Content limit:\n{content[:1500]}\n\n"
        "Task: You are an Obsidian architect. Given the file content above, determine its category, "
        "appropriate tags, and any aliases.\n"
        "Return ONLY a strict JSON object with this exact structure:\n"
        "{\n"
        "  \"category\": \"(must be one of: 00_Core, 10_People, 20_Projects, 30_Concepts, 90_Journal)\",\n"
        "  \"tags\": [\"tag1\", \"tag2\"],\n"
        "  \"aliases\": [\"alias1\", \"alias2\"]\n"
        "}\n"
    )

    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1}
    }
    
    try:
        res = requests.post(config.OLLAMA_URL, json=payload, timeout=30.0)
        res.raise_for_status()
        data = res.json().get("message", {}).get("content", "{}")
        parsed = json.loads(data)
    except Exception as e:
        log.error(f"Failed LLM categorization for {filepath.name}: {e}")
        parsed = {}

    category = parsed.get("category", "30_Concepts")
    if category not in categories:
        category = "30_Concepts"
        
    tags = parsed.get("tags", ["migrated"])
    aliases = parsed.get("aliases", [])
    
    now_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Build YAML Frontmatter
    yaml_lines = [
        "---",
        f"aliases: {json.dumps(aliases)}",
        f"tags: {json.dumps(tags)}",
        f"created: {now_str}",
        f"last_modified: {now_str}",
        "---",
        ""
    ]
    
    new_content = "\n".join(yaml_lines) + "\n" + content
    
    dest_path = vault_path / category / filepath.name
    dest_path.write_text(new_content, encoding="utf-8")
    
    # Delete original
    filepath.unlink()
    log.info(f"Migrated [[{filepath.stem}]] -> {category}")

def main():
    ensure_folders()
    
    # Find all loose files in Nodes/ or Root
    nodes_dir = vault_path / "Nodes"
    if nodes_dir.exists():
        for md_file in nodes_dir.glob("*.md"):
            migrate_file(md_file)
            
    for root_md in vault_path.glob("*.md"):
        migrate_file(root_md)
        
    # Clean up Nodes if empty
    if nodes_dir.exists() and not any(nodes_dir.iterdir()):
        nodes_dir.rmdir()
        log.info("Deleted empty Nodes/ directory.")

if __name__ == "__main__":
    main()
