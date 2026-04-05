import json
import logging
import requests
import numpy as np
import threading
import time
from pathlib import Path

import config

log = logging.getLogger("rag")

vault_path = config.VAULT_PATH

# ─── Global State for Fast RAG ────────────────────────────────────────────────
_index_lock = threading.Lock()
_cached_index = {}
_embeddings_matrix = None
_filepaths_list = []

def get_embedding(text: str) -> np.ndarray:
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": "nomic-embed-text",
                "prompt": text
            },
            timeout=10
        )
        response.raise_for_status()
        emb = response.json().get("embedding")
        return np.array(emb, dtype=np.float32)
    except Exception as e:
        log.error("Failed to generate embedding: %s", e)
        return np.array([], dtype=np.float32)

def load_index():
    index_file = vault_path / ".zed_embeddings.json"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_index(index):
    index_file = vault_path / ".zed_embeddings.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f)

def sync_embeddings():
    global _cached_index, _embeddings_matrix, _filepaths_list
    
    if not _cached_index:
        _cached_index = load_index()
        
    if not vault_path.exists():
        return

    updated = False
    current_paths = set()
    
    # 1. Update/Add New Files
    for md_file in vault_path.rglob("*.md"):
        if ".obsidian" in md_file.parts or ".trash" in md_file.parts:
            continue
            
        mtime = md_file.stat().st_mtime
        str_path = str(md_file.relative_to(vault_path))
        current_paths.add(str_path)
        
        if str_path not in _cached_index or _cached_index[str_path]["mtime"] < mtime:
            text = md_file.read_text(encoding="utf-8", errors="replace")
            emb = get_embedding(f"{md_file.stem}\n\n{text}")
            if emb.size > 0:
                _cached_index[str_path] = {
                    "mtime": mtime,
                    "emb": emb.tolist()
                }
                updated = True
                log.info("🧠 Embedded Node: %s", md_file.name)
            
    # 2. Clean Up Deleted Files
    for cached_path in list(_cached_index.keys()):
        if cached_path not in current_paths:
            del _cached_index[cached_path]
            updated = True
            log.debug("🗑️ Removed cached embedding: %s", cached_path)
            
    if updated:
        save_index(_cached_index)
        
    # 3. Rebuild Numpy Matrix for Lightning Fast Querying
    with _index_lock:
        if not _cached_index:
            _embeddings_matrix = None
            _filepaths_list = []
            return
            
        _filepaths_list = list(_cached_index.keys())
        matrix = np.array([_cached_index[p]["emb"] for p in _filepaths_list], dtype=np.float32)
        
        # Pre-normalize the matrix (L2 norm) so dot product is exact cosine sim
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1 # Avoid division by zero
        _embeddings_matrix = matrix / norms

def _background_sync_loop(interval: int):
    log.info("🔄 Background RAG thread started (sync every %ds)...", interval)
    while True:
        try:
            sync_embeddings()
        except Exception as e:
            log.error("Error in background RAG sync: %s", e)
        time.sleep(interval)

def start_background_sync(interval: int = 60):
    """Start the permanent background synchronization thread."""
    t = threading.Thread(target=_background_sync_loop, args=(interval,), daemon=True)
    t.start()

def get_relevant_notes(query: str, top_k: int = 5) -> str:
    """Instantly returns the top_k relevant notes using matrix multiplication in RAM."""
    with _index_lock:
        local_matrix = _embeddings_matrix
        local_paths = _filepaths_list
        
    if local_matrix is None or len(local_paths) == 0:
        return ""
        
    query_emb = get_embedding(query)
    if query_emb.size == 0:
        return "(Embedding service failed, no RAG context)"
        
    # Normalize query embedding
    q_norm = np.linalg.norm(query_emb)
    if q_norm == 0:
        return ""
    q_emb_norm = query_emb / q_norm
    
    # 🚀 Instant Vector Similarity Math
    scores = np.dot(local_matrix, q_emb_norm)
    
    # Top K indices
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    parts = []
    top_score = 0
    for i, idx in enumerate(top_indices):
        filepath = local_paths[idx]
        score = scores[idx]
        if i == 0: top_score = score
        
        full_path = vault_path / filepath
        if full_path.exists():
            content = full_path.read_text(encoding="utf-8", errors="replace")
            parts.append(f"--- {filepath} ---\n{content}")
            
    context = "\n\n".join(parts)
    if parts:
        log.info("⚡ RAG instantly loaded %d notes (max score %.2f)", len(parts), top_score)
    return context
