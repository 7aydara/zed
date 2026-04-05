import shutil
from pathlib import Path

vault_path = Path.home() / "Documents" / "ZedVault"

count_md = 0
count_canvas = 0

for item in vault_path.iterdir():
    if item.name == ".obsidian":
        continue # NE JAMAIS supprimer le dossier de configuration système d'Obsidian
    
    if item.is_file():
        if item.suffix == ".md":
            count_md += 1
            item.unlink()
        elif item.suffix == ".canvas":
            count_canvas += 1
            item.unlink()
        else:
            item.unlink()
            
    elif item.is_dir():
        # Supprime récursivement les dossiers comme Nodes et Nodes_Archive
        shutil.rmtree(item)

# Recreate Nodes folder so Zed doesn't crash
(vault_path / "Nodes").mkdir(exist_ok=True)

print(f"Purge Totale Terminée: Supprimé {count_md} fichiers Markdown et {count_canvas} fichiers Canvas.")
