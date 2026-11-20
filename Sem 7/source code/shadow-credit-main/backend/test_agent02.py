#!/usr/bin/env python3
"""
Agent 02 (WhatsApp) Verification Test
Tests Groq-powered Hinglish classification
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

import asyncio
from agents.agent_02_whatsapp import WhatsAppBatchParser

print("=" * 60)
print("AGENT 02 (WhatsApp) VERIFICATION")
print("=" * 60)

test_messages = """[27/03/2026, 9:15 AM] Ramesh Patil: bhai 500 rupes kal dena
[27/03/2026, 9:18 AM] Suresh Kirana: haan pakka bhai
[27/03/2026, 10:30 AM] Sharma Traders: Sir 2kg aata 1kg daal 180 rupaye
[27/03/2026, 10:31 AM] Suresh Kirana: payment aa gaya shukriya
[27/03/2026, 11:00 AM] Unknown: Good morning! 🌅
[27/03/2026, 2:15 PM] Ramesh Patil: bhai 5 hazaar ka maal chahiye"""

print("\nTest data: 6 messages (1 greeting, 5 financial)")
print("Expected: Greeting filtered out, 5 financial events extracted\n")

parser = WhatsAppBatchParser()

result = asyncio.run(parser.execute('test-session-p6', {
    'raw_text': test_messages,
    'session_id': 'test-session-p6'
}))

print(f"✅ Agent executed successfully")
print(f"   Success: {result.success}")
print(f"   Total messages parsed: {result.data['total_messages_parsed']}")
print(f"   Messages filtered: {result.data['messages_filtered']}")
print(f"   Financial events: {len(result.data['financial_events'])}")
print(f"   Confidence: {result.confidence_score}")

# Assertions
assert result.success, "Agent execution failed"
assert result.data['total_messages_parsed'] == 6, f"Expected 6 messages, got {result.data['total_messages_parsed']}"
assert result.data['messages_filtered'] > 0, "Expected some messages filtered (Good Morning)"
assert len(result.data['financial_events']) > 0, "Expected at least one financial event"

print("\n" + "=" * 60)
print("Sample financial event:")
print("=" * 60)
if result.data['financial_events']:
    event = result.data['financial_events'][0]
    print(f"Type: {event['event_type']}")
    print(f"Direction: {event['direction']}")
    print(f"Amount: ₹{event['amount']}")
    print(f"Counterparty: {event['counterparty']}")
    print(f"Confidence: {event['confidence']}")
    print(f"Reasoning: {event['reasoning']}")

print("\n" + "=" * 60)
print("✅ AGENT 02 VERIFICATION COMPLETE")
print("=" * 60)
