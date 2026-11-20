#!/usr/bin/env python3
"""
Phase 6 Part 1 Verification Script
Tests Groq connection and EasyOCR installation
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

print("=" * 60)
print("PHASE 6 PART 1 VERIFICATION")
print("=" * 60)

# Test 1: Groq connection
print("\n[1/2] Testing Groq API connection...")
try:
    from core.ai_client import groq_complete
    
    result = groq_complete(
        system_prompt="You are a test assistant.",
        user_content="Say the word READY and nothing else.",
        max_tokens=10
    )
    
    assert 'READY' in result.upper(), f"Expected 'READY', got: {result}"
    print("✅ Groq connection: OK")
    print(f"   Response: {result.strip()}")
    
except Exception as e:
    print(f"❌ Groq connection FAILED: {e}")
    print("\nTroubleshooting:")
    print("1. Check GROQ_API_KEY is set in backend/.env")
    print("2. Run: pip install groq")
    print("3. Verify key at console.groq.com")
    exit(1)

# Test 2: EasyOCR installation
print("\n[2/2] Testing EasyOCR installation...")
try:
    import easyocr
    
    reader = easyocr.Reader(['en', 'hi'], gpu=False, verbose=False)
    print("✅ EasyOCR: OK")
    print(f"   Languages: en, hi")
    print(f"   GPU: False")
    
except Exception as e:
    print(f"❌ EasyOCR FAILED: {e}")
    print("\nTroubleshooting:")
    print("1. Run: pip install easyocr")
    print("2. First run downloads models (~100MB) — this is normal")
    exit(1)

print("\n" + "=" * 60)
print("✅ PHASE 6 PART 1 COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Verify backend starts: uvicorn backend.main:app --reload")
print("2. Check health endpoint: http://localhost:8000/api/v1/health")
print("3. Proceed to Phase 6 Part 2 (Agent implementations)")
