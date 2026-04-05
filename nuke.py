import shutil
from pathlib import Path
import config

if config.VAULT_PATH.exists():
    shutil.rmtree(config.VAULT_PATH)
    print(f"Deleted entire vault: {config.VAULT_PATH}")
else:
    print(f"Vault already deleted: {config.VAULT_PATH}")
