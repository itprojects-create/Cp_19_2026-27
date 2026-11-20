#!/usr/bin/env python3
"""CHECK 2 — Backend starts clean"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("CHECK 2 — BACKEND STARTUP")
print("=" * 60)
print()

print("Testing backend imports...")
try:
    from main import app
    print("✅ FastAPI app imports successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

print()
print("Testing database connection...")
try:
    from db.database import get_db
    import asyncio
    
    async def test_db():
        async with get_db() as db:
            result = await db.execute("SELECT 1")
            return result
    
    asyncio.run(test_db())
    print("✅ Database connection OK")
except Exception as e:
    print(f"❌ Database failed: {e}")
    sys.exit(1)

print()
print("Testing agent initialization...")
try:
    from agents.supervisor import SupervisorAgent
    supervisor = SupervisorAgent()
    print("✅ Supervisor agent initializes successfully")
    print(f"   Agents loaded: {list(supervisor.agents.keys())}")
except Exception as e:
    print(f"❌ Agent initialization failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✅ BACKEND READY")
print("=" * 60)
print()
print("To start the server, run:")
print("  uvicorn main:app --reload --port 8000")
print()
print("Then test health endpoint:")
print("  curl http://localhost:8000/api/v1/health")
