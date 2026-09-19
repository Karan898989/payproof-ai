#!/bin/sh
set -e

echo "=== Initializing PayProof AI Database & Baseline Seeds ==="
python -c "
import sys
sys.path.insert(0, 'src')
from payproof.repositories.db import init_db
from payproof.repositories.case_repo import case_repo
init_db()
cases = case_repo.list_cases()
if not cases:
    print('[*] Seeding benchmark demo cases...')
    import asyncio
    from scripts.seed_data import seed_all
    asyncio.run(seed_all())
    print('[+] Benchmark data seeded successfully.')
else:
    print(f'[+] Existing database found with {len(cases)} cases.')
"

echo "=== Starting PayProof AI Uvicorn Server on Port ${PORT:-8000} ==="
exec uvicorn payproof.main:app --host 0.0.0.0 --port "${PORT:-8000}"
