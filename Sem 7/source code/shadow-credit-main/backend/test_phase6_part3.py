#!/usr/bin/env python3
"""
Phase 6 Part 3 Verification Test
Tests Agent 05 (Forensic), Agent 07 (Narrative), and Supervisor Groq integration
"""

import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("PHASE 6 PART 3 VERIFICATION")
print("=" * 60)
print()

# Test Agent 05 Forensic Analysis
print("Testing Agent 05 (Forensic Analysis)...")
print("-" * 60)

from agents.agent_05_reconciliation import run_forensic_analysis

mock_recon = {
    'whatsapp_total': 50000,
    'upi_total': 32000,
    'sms_total': 34500,
    'gap_amount': 18000,
    'gap_pct': 0.36,
    'business_type': 'Kirana Store',
    'location': 'Pune, Maharashtra',
    'avg_transaction': 1200,
    'transaction_count': 42,
    'data_completeness': 0.78
}

try:
    result = run_forensic_analysis(mock_recon)
    
    assert 'hypotheses' in result, "Missing 'hypotheses' field"
    assert 'forensic_narrative' in result, "Missing 'forensic_narrative' field"
    assert len(result['forensic_narrative']) > 50, f"Narrative too short: {len(result['forensic_narrative'])} chars"
    assert len(result['hypotheses']) >= 1, "No hypotheses generated"
    
    print(f"✅ Agent 05 OK")
    print(f"   Hypotheses: {len(result['hypotheses'])}")
    print(f"   Gap Classification: {result.get('gap_classification', 'N/A')}")
    print(f"   Recommended Action: {result.get('recommended_action', 'N/A')}")
    print(f"   Narrative: {result['forensic_narrative'][:100]}...")
    print()
    
except Exception as e:
    print(f"❌ Agent 05 FAILED: {e}")
    sys.exit(1)

# Test Agent 07 Credit Narrative
print("Testing Agent 07 (Credit Narrative)...")
print("-" * 60)

import asyncio
from agents.agent_07_report import generate_groq_narrative

mock_assessment = {
    'business_type': 'Kirana Store',
    'location': 'Pune, Maharashtra',
    'median_monthly_inflow': 44000,
    'days_of_data': 90,
    'income_regularity_score': 0.83,
    'data_sources': ['WhatsApp', 'UPI', 'SMS', 'Electricity Bill', 'Google Maps'],
    'warmth_score': 0.847,
    'credit_grade': 'A',
    'signals': [{'signal': 'Income Regularity', 'score': 0.83}],
    'reconciliation_gap_pct': 0.18,
    'reconciliation_status': 'NORMAL_CASH',
    'reconciliation_narrative': 'Cash transactions standard for Kirana',
    'maps_status': 'Verified',
    'maps_review_count': 47,
    'maps_rating': 4.2,
    'connection_type': 'COMMERCIAL',
    'final_limit': 105000,
    'assessment_confidence': 0.88
}

try:
    narrative = asyncio.run(generate_groq_narrative(mock_assessment))
    
    assert len(narrative) > 100, f"Narrative too short: {len(narrative)} chars"
    # Check that narrative contains specific numbers (not just template)
    has_numbers = any(char.isdigit() for char in narrative)
    assert has_numbers, "Narrative contains no specific numbers"
    
    print(f"✅ Agent 07 OK")
    print(f"   Narrative length: {len(narrative)} chars")
    print(f"   Narrative: {narrative[:150]}...")
    print()
    
except Exception as e:
    print(f"❌ Agent 07 FAILED: {e}")
    sys.exit(1)

# Test Supervisor Decision Functions
print("Testing Supervisor Decision Functions...")
print("-" * 60)

from agents.supervisor import supervisor_decide_phase_b, supervisor_final_decision

# Test Phase B decision
mock_phase_a = {
    'AGENT_02_WHATSAPP': {'confidence': 0.85, 'events': 42},
    'AGENT_01_OCR': {'confidence': 0.82, 'extractions': 15},
    'AGENT_03_KHATA': {'confidence': 0.88, 'transactions': 120}
}

try:
    decision_b = asyncio.run(supervisor_decide_phase_b(mock_phase_a, 12000, 0.85))
    
    assert 'phase_b_order' in decision_b, "Missing phase_b_order"
    assert 'reasoning' in decision_b, "Missing reasoning"
    assert len(decision_b['phase_b_order']) == 2, "Invalid phase_b_order length"
    
    print(f"✅ Supervisor Phase B Decision OK")
    print(f"   Order: {decision_b['phase_b_order']}")
    print(f"   Reasoning: {decision_b.get('reasoning', 'N/A')}")
    print()
    
except Exception as e:
    print(f"❌ Supervisor Phase B FAILED: {e}")
    sys.exit(1)

# Test Final decision
mock_summary = {
    'warmth_score': 0.847,
    'gap_classification': 'NORMAL_CASH',
    'agents_completed': ['AGENT_02', 'AGENT_01', 'AGENT_03', 'AGENT_04', 'AGENT_05']
}

try:
    decision_final = asyncio.run(supervisor_final_decision(mock_summary, 0.847, 'NORMAL_CASH'))
    
    assert 'action' in decision_final, "Missing action"
    assert 'confidence_band' in decision_final, "Missing confidence_band"
    assert 'reasoning' in decision_final, "Missing reasoning"
    assert decision_final['action'] in ['AUTO_ACCEPT', 'CLARIFY', 'FALLBACK'], f"Invalid action: {decision_final['action']}"
    
    print(f"✅ Supervisor Final Decision OK")
    print(f"   Action: {decision_final['action']}")
    print(f"   Confidence Band: {decision_final['confidence_band']}")
    print(f"   Reasoning: {decision_final.get('reasoning', 'N/A')}")
    print()
    
except Exception as e:
    print(f"❌ Supervisor Final Decision FAILED: {e}")
    sys.exit(1)

print("=" * 60)
print("✅ PHASE 6 PART 3 COMPLETE")
print("=" * 60)
print()
print("All agents successfully wired to Groq:")
print("  • Agent 05: Forensic analysis with hypothesis generation")
print("  • Agent 07: Credit narrative with senior banker persona")
print("  • Supervisor: Phase B and Final decision reasoning")
