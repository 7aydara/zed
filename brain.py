"""
Zed Voice Assistant — Brain
Gemini 2.0 Flash LLM with Obsidian vault memory.
"""

from __future__ import annotations

import logging
import re
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterator
import config

import logging

log = logging.getLogger(__name__)

import requests
import json

# Global session and chat history for connection persistence and context
_session = requests.Session()
chat_history: list[dict] = []


# ─── Obsidian Vault ─────────────────────────────────────────────────────────────


# ─── Sentence Splitter ──────────────────────────────────────────────────────────

_SENTENCE_END = re.compile(r'(?<=[.!?])\s+')


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on .!? boundaries."""
    return [s.strip() for s in _SENTENCE_END.split(text) if s.strip()]


import rag

# ─── Think ──────────────────────────────────────────────────────────────────────

def think(user_text: str, interrupt_event: threading.Event = None) -> Iterator[str]:
    """
    Send *user_text* to Gemini with vault context, stream the response
    sentence by sentence.

    Yields
    ------
    str
        One complete sentence at a time.
    """
    # Build context by fetching relevant RAG nodes
    notes_context = rag.get_relevant_notes(user_text)
    
    core_context = ""
    core_dir = config.VAULT_PATH / "00_Core"
    if core_dir.exists():
        for core_file in core_dir.glob("*.md"):
            try:
                core_context += f"--- {core_file.name} ---\n"
                core_context += core_file.read_text(encoding="utf-8") + "\n\n"
            except Exception as e:
                log.warning("Failed to read core file %s: %s", core_file, e)
                
    import skills_engine
    
    system_instruction = (
        f"{config.SYSTEM_PROMPT}\n\n"
        f"{skills_engine.get_skills_prompt()}\n\n"
        f"=== CORE SYSTEM MEMORY ===\n{core_context}\n"
        f"=== USER'S RELEVANT NOTES (RAG) ===\n{notes_context}\n"
        f"=== END NOTES ===\n"
    )

    log.info("🧠 Thinking about: %s", user_text)

    full_response: list[str] = []
    buffer = ""

    global chat_history
    
    messages = [
        {"role": "system", "content": system_instruction}
    ]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_text})

    import subprocess
    max_loops = 3
    loop_count = 0

    try:
        while loop_count < max_loops:
            loop_count += 1
            payload = {
                "model": config.OLLAMA_MODEL,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1024
                }
            }
            res = _session.post(config.OLLAMA_URL, json=payload, stream=True)
            res.raise_for_status()

            buffer = ""
            command_executed = False

            for line in res.iter_lines():
                if interrupt_event and interrupt_event.is_set():
                    log.info("🤔 Interrupted by wake word! Aborting thought.")
                    return

                if line:
                    chunk = json.loads(line)
                    text = chunk.get("message", {}).get("content", "")
                    if text:
                        buffer += text
                        
                        if "<use_skill" in buffer:
                            if "</use_skill>" in buffer:
                                skill_start = buffer.find("<use_skill")
                                skill_end = buffer.find("</use_skill>") + len("</use_skill>")
                                skill_content = buffer[skill_start:skill_end]
                                
                                import re
                                import skills_engine
                                match = re.search(r'<use_skill\s+name=["\'](.*?)["\']>(.*?)</use_skill>', skill_content, re.DOTALL)
                                if match:
                                    skill_name = match.group(1).strip()
                                    skill_arg = match.group(2).strip()
                                    log.info("🪄 Using skill: %s with arg: %s", skill_name, skill_arg)
                                    out_text = skills_engine.execute_skill(skill_name, skill_arg)
                                else:
                                    out_text = "Error: Malformed <use_skill> tag."
                                
                                log.info("🪄 Result preview: %s", out_text[:80].replace("\n", " "))
                                
                                pre_tag = buffer[:skill_start]
                                if pre_tag.strip():
                                    sentences = _split_sentences(pre_tag)
                                    for sentence in sentences:
                                        full_response.append(sentence)
                                        yield sentence
                                        
                                messages.append({"role": "assistant", "content": buffer[:skill_end]})
                                messages.append({"role": "user", "content": f"Skill result:\n<skill_output>\n{out_text}\n</skill_output>\nPlease summarize this briefly (no markdown) for me."})
                                command_executed = True
                                break
                        elif "<run_command>" in buffer:
                            # Found command tag, hold yielding
                            if "</run_command>" in buffer:
                                cmd_start = buffer.find("<run_command>") + len("<run_command>")
                                cmd_end = buffer.find("</run_command>")
                                cmd_str = buffer[cmd_start:cmd_end].strip()
                                
                                log.info("🛠️ Executing command: %s", cmd_str)
                                
                                try:
                                    out = subprocess.run(cmd_str, shell=True, capture_output=True, text=True, timeout=30)
                                    out_text = f"STDOUT:\n{out.stdout}\nSTDERR:\n{out.stderr}"
                                except subprocess.TimeoutExpired:
                                    out_text = "Command timed out after 30 seconds."
                                except Exception as e:
                                    out_text = f"Execution error: {e}"
                                
                                log.info("🛠️ Result preview: %s", out_text[:80].replace("\n", " "))
                                
                                # Yield everything before the command tag
                                pre_tag = buffer[:buffer.find("<run_command>")]
                                if pre_tag.strip():
                                    sentences = _split_sentences(pre_tag)
                                    for sentence in sentences:
                                        full_response.append(sentence)
                                        yield sentence
                                
                                # Setup next loop execution
                                messages.append({"role": "assistant", "content": buffer[:cmd_end + len("</run_command>")]})
                                messages.append({"role": "user", "content": f"Execution result:\n<command_output>\n{out_text}\n</command_output>\nPlease summarize this briefly (no markdown) for me."})
                                command_executed = True
                                break # break iter_lines, restart while LLM response loop
                        else:
                            # Normal streaming
                            sentences = _split_sentences(buffer)
                            if len(sentences) > 1:
                                for sentence in sentences[:-1]:
                                    full_response.append(sentence)
                                    yield sentence
                                buffer = sentences[-1]
                            elif sentences and buffer.rstrip().endswith(('.', '!', '?')):
                                full_response.append(sentences[0])
                                yield sentences[0]
                                buffer = ""

            if command_executed:
                continue

            # Flush remaining buffer at the very end
            if buffer.strip():
                full_response.append(buffer.strip())
                yield buffer.strip()
            break

    except Exception as exc:
        log.error("Ollama error: %s", exc)
        error_msg = "Sorry, I had trouble thinking about that. Please try again."
        full_response.append(error_msg)
        yield error_msg

    # Update chat history
    full_text = " ".join(full_response)
    chat_history.append({"role": "user", "content": user_text})
    chat_history.append({"role": "assistant", "content": full_text})
    
    # Keep history manageable (last 20 messages)
    if len(chat_history) > 20:
        chat_history = chat_history[-20:]

    # Log the exchange
    _log_exchange(user_text, full_text)


# ─── Knowledge Graph Agent ───────────────────────────────────────────────────────

def _log_exchange(user_text: str, response_text: str) -> None:
    """Trigger the asynchronous memory agent to map entities to the Vault."""
    try:
        # Kick off the async memory analysis (don't block the UI!)
        threading.Thread(target=_analyze_memory, args=(user_text, response_text), daemon=True).start()
        log.info("📓 Memory agent analyzing conversation...")
    except Exception as exc:
        log.error("Failed to spawn memory agent: %s", exc)


def _analyze_memory(user_text: str, response_text: str) -> None:
    """Sideband agent that builds an interconnected Obsidian Knowledge Graph."""
    try:
        prompt = (
            f"Conversation:\nUser: {user_text}\nZed: {response_text}\n\n"
            "Task: Act as an Obsidian Knowledge Graph architect. Extract STRICTLY ONLY factual entities, tangible concepts, people, long-term preferences, or real projects. "
            "CRITICAL: DO NOT extract meta-conversational elements (e.g., 'Unclear User Request', 'Misunderstanding', 'Clarification Needed', 'Audio Issue', 'Greeting'). "
            "Provide a structured JSON array under the key 'nodes'. "
            "For each node, provide:\n"
            "  1. 'title' (a short, descriptive phrase)\n"
            "  2. 'content' (a concise summary of what was discussed and any open questions)\n"
            "  3. 'category' (MUST be one of: '00_Core', '10_People', '20_Projects', '30_Concepts', '90_Journal')\n"
            "  4. 'related_topics' (a list of other short string titles that logically connect to this topic)\n"
            "  5. 'tags' (a list of short strings/tags fitting this node, e.g. 'project', 'philosophy')\n"
            "  6. 'aliases' (a list of alternative names for this node)\n\n"
            "If the conversation is just small talk, confusion, or contains no concrete facts, YOU MUST return {{\"nodes\": []}}."
        )

        payload = {
            "model": config.OLLAMA_MODEL,
            "format": "json",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.1}
        }
        
        res = _session.post(config.OLLAMA_URL, json=payload, timeout=60.0)
        res.raise_for_status()
        
        data = res.json()
        reply_str = data.get("message", {}).get("content", "{}")
        
        try:
            parsed = json.loads(reply_str)
            nodes = parsed.get("nodes", [])
        except json.JSONDecodeError:
            nodes = []

        if not nodes:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        for n in nodes:
            title = n.get("title", "").strip()
            content = n.get("content", "").strip()
            related = n.get("related_topics", [])
            category = n.get("category", "30_Concepts").strip()
            tags = n.get("tags", ["auto-generated"])
            aliases = n.get("aliases", [])
            
            valid_categories = ["00_Core", "10_People", "20_Projects", "30_Concepts", "90_Journal", "_Scratchpad"]
            if category not in valid_categories:
                category = "30_Concepts"
            
            if not title or not content:
                continue

            # Strip invalid characters from filename
            safe_title = "".join(x for x in title if x.isalnum() or x in " -_").strip()
            if not safe_title:
                continue

            # Format the related topics as Obsidian wiki links
            links = []
            for r in related:
                clean_r = "".join(x for x in str(r) if x.isalnum() or x in " -_").strip()
                if clean_r:
                    links.append(f"[[{clean_r}]]")
            
            links_str = f"\n**Connections:** {', '.join(links)}" if links else ""

            node_dir = config.VAULT_PATH / category
            node_dir.mkdir(parents=True, exist_ok=True)
            node_file = node_dir / f"{safe_title}.md"

            if not node_file.exists():
                yaml_header = (
                    "---\n"
                    f"aliases: {json.dumps(aliases)}\n"
                    f"tags: {json.dumps(tags)}\n"
                    f"created: {datetime.now().strftime('%Y-%m-%d')}\n"
                    f"last_modified: {datetime.now().strftime('%Y-%m-%d')}\n"
                    "---\n\n"
                )
                header = f"# {title}\n\n"
                entry = f"## Context Update ({timestamp})\n\n{content}\n{links_str}\n\n---\n"
                node_file.write_text(yaml_header + header + entry, encoding="utf-8")
                log.info("🧠 Graph mapped new Node in %s: [[%s]]", category, safe_title)
            else:
                existing_content = node_file.read_text(encoding="utf-8")
                merge_prompt = (
                    f"Existing File Content:\n{existing_content}\n\n"
                    f"New Information:\n{content}\n\n"
                    f"Current Date: {datetime.now().strftime('%Y-%m-%d')}\n\n"
                    "Task: Merge the New Information into the Existing File Content. "
                    "Rewrite the content to be a cohesive, well-structured document that includes all facts. "
                    "CRITICAL: If the Existing File Content has YAML frontmatter (lines between --- at the top), YOU MUST preserve it perfectly at the top of your output. Update 'last_modified' in the YAML to the Current Date. "
                    "Do not just append it. Return ONLY the fully merged markdown text including its YAML frontmatter. Do not include extra conversational text."
                )
                merge_payload = {
                    "model": config.OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": merge_prompt}],
                    "stream": False
                }
                try:
                    merge_res = _session.post(config.OLLAMA_URL, json=merge_payload, timeout=60.0)
                    merge_res.raise_for_status()
                    merged_text = merge_res.json().get("message", {}).get("content", "").strip()
                    if merged_text:
                        # Ensure we don't start with markdown code blocks
                        if merged_text.startswith("```markdown"):
                            merged_text = merged_text[11:].strip()
                            if merged_text.endswith("```"):
                                merged_text = merged_text[:-3].strip()
                        node_file.write_text(merged_text, encoding="utf-8")
                        log.info("🧠 Graph merged info into Node in %s: [[%s]]", category, safe_title)
                    else:
                        raise ValueError("Empty merge result")
                except Exception as e:
                    log.error("Failed to merge node %s, falling back to append: %s", safe_title, e)
                    entry = f"## Context Update ({timestamp})\n\n{content}\n{links_str}\n\n---\n"
                    with node_file.open("a", encoding="utf-8") as f:
                        f.write(entry)

    except Exception as exc:
        log.warning("Knowledge Graph update failed: %s", exc)

