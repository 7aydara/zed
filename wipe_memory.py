import shutil
from pathlib import Path

vault_path = Path.home() / "Documents" / "ZedVault"

# 1. Delete index
index_path = vault_path / ".zed_embeddings.json"
if index_path.exists():
    index_path.unlink()
    print("Deleted .zed_embeddings.json")

# 2. Delete all generated nodes in Nodes folder
nodes_path = vault_path / "Nodes"
if nodes_path.exists() and nodes_path.is_dir():
    count = 0
    for file in nodes_path.glob("*.md"):
        file.unlink()
        count += 1
    print(f"Deleted {count} generated memory nodes in Nodes/")
    
print("Vault memory reset successfully!")
