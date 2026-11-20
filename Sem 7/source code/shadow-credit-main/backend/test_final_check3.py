#!/usr/bin/env python3
"""CHECK 3 — End-to-end session (requires backend running on port 8000)"""

import httpx
import json
import sys

print("=" * 60)
print("CHECK 3 — END-TO-END SESSION")
print("=" * 60)
print()

print("NOTE: This test requires the backend to be running.")
print("Start it with: uvicorn main:app --reload --port 8000")
print()

try:
    # Test health endpoint first
    print("Testing health endpoint...")
    r = httpx.get('http://localhost:8000/api/v1/health', timeout=5.0)
    health = r.json()
    print(f"✅ Health: {health['status']}")
    print()
    
    # Create a test session
    print("Creating test session...")
    r2 = httpx.post('http://localhost:8000/api/v1/sessions', json={
        'owner_name': 'Suresh Kirana Store',
        'location_district': 'Pune, Maharashtra',
        'consent_given': True,
        'demo_mode': False
    }, timeout=10.0)
    
    data = r2.json()
    session_id = data['data']['session_id']
    print(f"✅ Session created: {session_id[:8]}...")
    print()
    
    print("=" * 60)
    print("✅ BACKEND READY FOR DEMO")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Upload test documents via /api/v1/ingest")
    print("2. Watch agents run in real-time")
    print("3. View results on RM dashboard")
    
except httpx.ConnectError:
    print("❌ Backend not running on port 8000")
    print()
    print("Start the backend first:")
    print("  cd shadow-credit/backend")
    print("  uvicorn main:app --reload --port 8000")
    print()
    print("Then run this test again.")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
