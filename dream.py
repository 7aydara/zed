import os
import json
import logging
import threading
import time
import requests
import datetime
from pathlib import Path
import config
import rag

log = logging.getLogger("dream")

def _parse_frontmatter(content: str):
    """Simple parser to extract YAML frontmatter and the rest of the markdown."""
    if not content.startswith("---\n"):
        return "", content
    parts = content.split("---\n", 2)
    if len(parts) >= 3:
        return "---\n" + parts[1] + "---\n", parts[2]
    return "", content

def consolidate_node(filepath: Path):
    """Consolidates a single Markdown file using the LLM to rewrite it cleanly."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        
        # Heuristic: If it doesn't have multiple '## Context Update' and is short, maybe it's fine.
        if content.count("## Context Update") <= 1 and len(content) < 500:
            return False # No need to consolidate
            
        log.info("💭 Dreaming about: %s", filepath.name)
        
        frontmatter, markdown_body = _parse_frontmatter(content)
        
        prompt = (
            f"Existing Memory Node: {filepath.stem}\n\n"
            f"Content:\n{markdown_body}\n\n"
            "Task: You are performing a 'dream' — a reflective pass over your memory files. "
            "Synthesize the content above into a durable, well-organized memory. "
            "1. Remove all '## Context Update (Date)' headers.\n"
            "2. Merge duplicate facts and resolve any contradictions.\n"
            "3. Format the output cleanly using standard markdown headings and bullet points where appropriate.\n"
            "4. Convert relative dates ('yesterday') into absolute context if possible.\n"
            "Return ONLY the rewritten markdown body. Do not return the YAML frontmatter. Do not wrap in ```markdown blocks."
        )

        payload = {
            "model": config.OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.2} # low temp for factual rewrite
        }
        
        res = requests.post(config.OLLAMA_URL, json=payload, timeout=90.0)
        res.raise_for_status()
        
        merged_body = res.json().get("message", {}).get("content", "").strip()
        
        if merged_body:
            # Strip markdown code blocks if the LLM hallucinated them
            if merged_body.startswith("```markdown"):
                merged_body = merged_body[11:].strip()
                if merged_body.endswith("```"):
                    merged_body = merged_body[:-3].strip()
            
            # Update 'last_modified' in frontmatter if possible
            if frontmatter:
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                lines = frontmatter.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("last_modified:"):
                        lines[i] = f"last_modified: {today}"
                frontmatter = "\n".join(lines)
                
            new_content = frontmatter + "\n" + merged_body + "\n"
            filepath.write_text(new_content, encoding="utf-8")
            log.info("💭 Successfully consolidated: %s", filepath.name)
            return True
            
    except Exception as e:
        log.error("Failed to consolidate %s: %s", filepath.name, e)
    
    return False

def dream_cycle():
    """Runs a full pass over the Vault to consolidate memory."""
    vault_path = config.VAULT_PATH
    if not vault_path.exists():
        return
        
    consolidated_count = 0
    categories = ["00_Core", "10_People", "20_Projects", "30_Concepts"]
    
    for cat in categories:
        cat_dir = vault_path / cat
        if not cat_dir.exists():
            continue
            
        for md_file in cat_dir.glob("*.md"):
            if consolidate_node(md_file):
                consolidated_count += 1
                time.sleep(5.0)  # Yield Ollama queue to core chat thread
                
    if consolidated_count > 0:
        log.info("💤 Dream cycle completed. Consolidated %d memories. Triggering RAG sync.", consolidated_count)
        rag.sync_embeddings()
    else:
        log.debug("💤 Dream cycle completed. Memories already tight.")

def _dream_loop(interval: int):
    log.info("💤 Background autoDream thread started (wakes every %d seconds)...", interval)
    while True:
        try:
            dream_cycle()
        except Exception as e:
            log.error("Error in autoDream sequence: %s", e)
        time.sleep(interval)

def start_background_dream(interval: int = 3600):
    """Start the permanent background memory consolidation thread (default 1 hour)."""
    t = threading.Thread(target=_dream_loop, args=(interval,), daemon=True)
    t.start()

if __name__ == "__main__":
    # For standalone testing
    logging.basicConfig(level=logging.INFO)
    dream_cycle()
