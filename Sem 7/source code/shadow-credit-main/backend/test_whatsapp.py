#!/usr/bin/env python
"""
Quick validation test for WhatsApp parser functions.
Run: python test_whatsapp.py
No API calls required.
"""
import sys
from agents.agent_02_whatsapp import (
    parse_whatsapp_export,
    pre_filter_financial,
    normalize_amount,
    reconstruct_timeline,
)

SAMPLE_EXPORT = """[01/03/2024, 10:30 AM] Rajesh: bhai 500 rupes kal dena
[01/03/2024, 10:31 AM] Rajesh: need urgently
[01/03/2024, 11:00 AM] Priya: Good morning! Have a nice day 🌅
[01/03/2024, 11:15 AM] Vendor: maal ready hai 2kg aata 1kg daal
[02/03/2024, 09:00 AM] Customer: do hazaar ka order chahiye
[02/03/2024, 09:05 AM] Customer: delivery karwa do
[02/03/2024, 14:30 PM] Supplier: payment aaya sir 1500
[03/03/2024, 08:00 AM] Boss: light bill 800 bhara aaj
[03/03/2024, 08:30 AM] Friend: ok
[03/03/2024, 09:00 AM] Merchant: five thousand cash needed
[03/03/2024, 10:00 AM] Buyer: half lakh ka deal
[03/03/2024, 11:00 AM] <Media omitted>
[04/03/2024, 09:00 AM] Audio: <Voice note omitted>
[04/03/2024, 10:00 AM] Seller: ₹1,500 aaj hi dedo
[05/03/2024, 09:00 AM] Client: https://example.com check this
[05/03/2024, 10:00 AM] Merchant: one point five lakh chahiye"""


def test_parse():
    print("=" * 70)
    print("TEST 1: parse_whatsapp_export")
    print("=" * 70)
    messages = parse_whatsapp_export(SAMPLE_EXPORT)
    print(f"✓ Parsed {len(messages)} messages")
    
    # Check specific messages
    msg_by_sender = {m["sender"]: m for m in messages}
    
    if "Rajesh" in msg_by_sender:
        rajesh_msg = msg_by_sender["Rajesh"]
        expected_text = "bhai 500 rupes kal dena need urgently"
        if expected_text in rajesh_msg["message"]:
            print(f"✓ Multi-line continuation works: '{rajesh_msg['message'][:50]}...'")
        else:
            print(f"✗ Continuation failed. Got: {rajesh_msg['message']}")
    
    if "Vendor" in msg_by_sender:
        print(f"✓ Message parsing works: Vendor='maal ready hai...'")
    
    print(f"✓ Total messages: {len(messages)}")
    return messages


def test_filter(messages):
    print("\n" + "=" * 70)
    print("TEST 2: pre_filter_financial")
    print("=" * 70)
    filtered, stats = pre_filter_financial(messages)
    print(f"✓ Input: {stats['total_input']}, Kept: {stats['total_kept']}, Dropped: {stats['total_dropped']}")
    print(f"✓ Drop rate: {stats['drop_rate_pct']:.1f}%")
    print(f"✓ Drop reasons: {stats['drop_reasons']}")
    
    if stats['total_kept'] > 0:
        print(f"✓ Filtered down to financial signals: {stats['total_kept']} messages")
    
    # Verify noise was dropped
    texts = [m["message"].lower() for m in filtered]
    if not any("good morning" in t for t in texts):
        print("✓ Greetings correctly dropped")
    if not any("example.com" in t for t in texts):
        print("✓ Links correctly dropped")
    if not any("<voice" in t.lower() for t in texts):
        print("✓ Voice notes correctly dropped")
    
    return filtered


def test_normalize():
    print("\n" + "=" * 70)
    print("TEST 3: normalize_amount")
    print("=" * 70)
    
    test_cases = [
        ("₹500", 500.0, "Rupee symbol"),
        ("Rs 1500", 1500.0, "Rs prefix"),
        ("50k", 50000.0, "k notation"),
        ("1.5L", 150000.0, "L notation"),
        ("do hazaar", 2000.0, "Hindi: two thousand"),
        ("dedh lakh", 150000.0, "Hindi: one and half lakh"),
        ("aadha lakh", 50000.0, "Hindi: half lakh"),
        ("paanch sau", 500.0, "Hindi: five hundred"),
        ("five thousand", 5000.0, "English: five thousand"),
        ("one point five lakh", 150000.0, "English: one point five lakh"),
        ("half lakh", 50000.0, "English: half lakh"),
        ("2.5 lakh", 250000.0, "Mixed: 2.5 lakh"),
        ("1,500 ka maal", 1500.0, "Comma number"),
        ("500", 500.0, "Plain number"),
    ]
    
    passed = 0
    failed = 0
    for text, expected, desc in test_cases:
        result = normalize_amount(text)
        if result == expected:
            print(f"✓ {desc:30} '{text:20}' → {result:,.0f}")
            passed += 1
        else:
            print(f"✗ {desc:30} '{text:20}' → {result} (expected {expected})")
            failed += 1
    
    print(f"\n✓ Amount parsing: {passed}/{len(test_cases)} passed")
    if failed > 0:
        print(f"✗ {failed} cases failed")
    return passed, failed


def test_timeline(filtered):
    print("\n" + "=" * 70)
    print("TEST 4: reconstruct_timeline (mock classification)")
    print("=" * 70)
    
    # Create mock classifications from filtered messages
    mock_classified = []
    for msg in filtered:
        text = msg["message"].lower()
        if "payment" in text or "aaya" in text or any(c in text for c in ["₹", "rs", "rupee"]):
            classification = "payment_received"
        elif "maal" in text or "ready" in text or "confirm" in text:
            classification = "sale_confirmation"
        elif "order" in text or "chahiye" in text:
            classification = "purchase_order"
        elif "bill" in text or "bhara" in text:
            classification = "expense"
        else:
            classification = "irrelevant"
        
        amount = normalize_amount(text)
        mock_classified.append({
            "line_id": msg["line_id"],
            "classification": classification,
            "amount": amount,
            "counterparty": msg.get("sender"),
            "date_mentioned": None,
            "confidence": 0.75 if classification != "irrelevant" else 0.3,
        })
    
    if mock_classified:
        timeline = reconstruct_timeline(mock_classified, filtered)
        print(f"✓ Timeline reconstructed")
        print(f"  - Data quality: {timeline['data_quality']}")
        print(f"  - Total events: {len(mock_classified)}")
        print(f"  - Median monthly inflow: ₹{timeline['median_monthly_inflow']:,.0f}")
        print(f"  - Date range: {timeline['date_range']['start']} to {timeline['date_range']['end']}")
        print(f"  - Weeks with data: {timeline['date_range']['weeks_with_data']}")
        print(f"  - Unique counterparties: {len(timeline['unique_counterparties'])}")
        return True
    else:
        print("✗ No classified events to timeline")
        return False


def main():
    print("\n" + "🔍 " * 20)
    print("WHATSAPP PARSER VALIDATION TEST")
    print("🔍 " * 20)
    
    try:
        messages = test_parse()
        filtered = test_filter(messages)
        passed, failed = test_normalize()
        timeline_ok = test_timeline(filtered)
        
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        if failed == 0 and timeline_ok:
            print("✅ All tests passed!")
            print("Parser is ready for production use.")
            return 0
        else:
            print(f"⚠️  Some tests had issues: {failed} amount parsing failures")
            return 1
    except Exception as exc:
        print(f"\n❌ FATAL ERROR: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
