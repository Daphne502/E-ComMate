#!/bin/bash
set -e

cd /app
export PYTHONPATH=/app

echo "Checking ChromaDB..."
python - <<'PY'
import os
from core.rag import initialize_rag

db_dir = os.path.join("data", "chroma_db")
if not os.path.exists(db_dir) or not os.listdir(db_dir):
    print("ChromaDB missing, building from styles.csv (may take 1-2 min)...")
    initialize_rag()
    print("ChromaDB ready.")
else:
    print("ChromaDB already present.")
PY

exec supervisord -c supervisord.conf