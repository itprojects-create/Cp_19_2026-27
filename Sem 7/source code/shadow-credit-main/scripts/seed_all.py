import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "personas"

# ── PERSONA 1: Suresh Kumar — Clean Kirana ─────────────
P1 = DATA / "persona01_clean"
P1.mkdir(parents=True, exist_ok=True)

P1.joinpath("persona.json").write_text(json.dumps({
    "persona_id": "persona01_clean",
    "display_name": "Suresh Kumar",
    "business_name": "Suresh Kirana & General Store",
    "business_type": "Kirana Store",
    "location_masked": "Sadashiv Peth, Pune, Maharashtra",
    "years_in_operation": 7,
    "demo_mode": True,
    "expected_outcomes": {
        "warmth_grade": "A",
        "credit_limit_range": [95000, 115000],
        "warmth_score_range": [0.78, 0.86],
        "clarification_expected": False,
        "forensic_finding": "NORMAL_CASH",
        "compliance_pass_rate": 0.83
    }
}, indent=2), encoding="utf-8")

P1.joinpath("whatsapp.txt").write_text(
    "01/01/2026, 09:12 - Ramesh Bhosale: bhai kal ka udhaar 240 tha\n"
    "01/01/2026, 10:45 - Suresh: Ramesh bhai 240 mili PhonePe\n"
    "02/01/2026, 11:45 - Suresh: 180 delivered\n"
    "02/01/2026, 11:46 - Ashok Patil: done bhai\n"
    "03/01/2026, 14:05 - Sunita More: 162 sent\n"
    "04/01/2026, 18:30 - Vijay Kadam: 340 cash diya\n"
    "05/01/2026, 10:47 - Ramesh Bhosale: 520 sent 5kg aata 2kg sugar\n"
    "08/01/2026, 09:47 - Vijay Kadam: 1040 PhonePe wholesale\n"
    "09/01/2026, 11:40 - Ashok Patil: 245 sent Parle-G aur dal\n"
    "11/01/2026, 10:02 - Priya Deshpande: 1840 sent khata clear\n"
    "13/01/2026, 10:22 - Suresh: 380 mili Sankranti til gul\n"
    "15/01/2026, 11:20 - Ashok Patil: 2150 done\n"
    "17/01/2026, 14:20 - Sunita More: 95 diya cash kapoor dhoop batti\n"
    "19/01/2026, 07:35 - Priya Deshpande: 420 diya subah wala saman\n"
    "20/01/2026, 10:10 - Ramesh Bhosale: 480 PhonePe Bisleri crate\n"
    "22/01/2026, 17:05 - Vijay Kadam: 2200 cash wholesale payment\n"
    "27/01/2026, 16:46 - Suresh: 680 mili PhonePe\n"
    "30/01/2026, 17:02 - Suresh: 3400 received shukriya Vijay bhai\n"
    "31/01/2026, 21:00 - Suresh: January total 47200 ho gaya alhamdulillah\n"
    "05/02/2026, 11:00 - Priya Deshpande: 590 diya aaj\n"
    "14/02/2026, 14:30 - Vijay Kadam: 450 diya Valentine chocolate\n"
    "22/02/2026, 18:12 - Ashok Patil: 1950 PhonePe Feb clear\n"
    "28/02/2026, 21:30 - Suresh: February done 38900 total\n"
    "07/03/2026, 10:05 - Suresh: 1200 mili Holi shopping Priya ji\n"
    "20/03/2026, 17:46 - Suresh: 4100 received Vijay bhai March wholesale\n"
    "25/03/2026, 21:00 - Suresh: March almost done 52000 lag raha hai\n",
    encoding="utf-8")

P1.joinpath("upi_events.json").write_text(json.dumps([
    {"transaction_id":"UPI80000001","date":"2026-01-01","time":"10:45:00","amount":240.0,"type":"CREDIT","counterparty_name":"Ramesh Bhosale","upi_id":"ramesh@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000002","date":"2026-01-02","time":"11:45:00","amount":180.0,"type":"CREDIT","counterparty_name":"Ashok Patil","upi_id":"ashok@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000003","date":"2026-01-03","time":"14:05:00","amount":162.0,"type":"CREDIT","counterparty_name":"Sunita More","upi_id":"sunita@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000004","date":"2026-01-04","time":"18:30:00","amount":340.0,"type":"CREDIT","counterparty_name":"Vijay Kadam","upi_id":"vijay@paytm","reference":"Cash noted"},
    {"transaction_id":"UPI80000005","date":"2026-01-05","time":"10:47:00","amount":520.0,"type":"CREDIT","counterparty_name":"Ramesh Bhosale","upi_id":"ramesh@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000006","date":"2026-01-08","time":"09:47:00","amount":1040.0,"type":"CREDIT","counterparty_name":"Vijay Kadam","upi_id":"vijay@paytm","reference":"PhonePe wholesale"},
    {"transaction_id":"UPI80000007","date":"2026-01-09","time":"11:40:00","amount":245.0,"type":"CREDIT","counterparty_name":"Ashok Patil","upi_id":"ashok@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000008","date":"2026-01-11","time":"10:02:00","amount":1840.0,"type":"CREDIT","counterparty_name":"Priya Deshpande","upi_id":"priya@paytm","reference":"PhonePe khata clear"},
    {"transaction_id":"UPI80000009","date":"2026-01-13","time":"10:22:00","amount":380.0,"type":"CREDIT","counterparty_name":"Ramesh Bhosale","upi_id":"ramesh@paytm","reference":"PhonePe Sankranti"},
    {"transaction_id":"UPI80000010","date":"2026-01-15","time":"11:20:00","amount":2150.0,"type":"CREDIT","counterparty_name":"Ashok Patil","upi_id":"ashok@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000011","date":"2026-01-17","time":"14:20:00","amount":95.0,"type":"CREDIT","counterparty_name":"Sunita More","upi_id":"sunita@paytm","reference":"Cash"},
    {"transaction_id":"UPI80000012","date":"2026-01-19","time":"07:35:00","amount":420.0,"type":"CREDIT","counterparty_name":"Priya Deshpande","upi_id":"priya@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000013","date":"2026-01-20","time":"10:10:00","amount":480.0,"type":"CREDIT","counterparty_name":"Ramesh Bhosale","upi_id":"ramesh@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000014","date":"2026-01-22","time":"17:05:00","amount":2200.0,"type":"CREDIT","counterparty_name":"Vijay Kadam","upi_id":"vijay@paytm","reference":"Cash wholesale"},
    {"transaction_id":"UPI80000015","date":"2026-01-27","time":"16:46:00","amount":680.0,"type":"CREDIT","counterparty_name":"Ramesh Bhosale","upi_id":"ramesh@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000016","date":"2026-01-30","time":"17:02:00","amount":3400.0,"type":"CREDIT","counterparty_name":"Vijay Kadam","upi_id":"vijay@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000017","date":"2026-02-05","time":"11:00:00","amount":590.0,"type":"CREDIT","counterparty_name":"Priya Deshpande","upi_id":"priya@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000018","date":"2026-02-14","time":"14:30:00","amount":450.0,"type":"CREDIT","counterparty_name":"Vijay Kadam","upi_id":"vijay@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000019","date":"2026-02-22","time":"18:12:00","amount":1950.0,"type":"CREDIT","counterparty_name":"Ashok Patil","upi_id":"ashok@paytm","reference":"PhonePe"},
    {"transaction_id":"UPI80000020","date":"2026-03-07","time":"10:05:00","amount":1200.0,"type":"CREDIT","counterparty_name":"Priya Deshpande","upi_id":"priya@paytm","reference":"PhonePe Holi"},
    {"transaction_id":"UPI80000021","date":"2026-03-20","time":"17:46:00","amount":4100.0,"type":"CREDIT","counterparty_name":"Vijay Kadam","upi_id":"vijay@paytm","reference":"PhonePe wholesale"},
], indent=2), encoding="utf-8")

P1.joinpath("khata.csv").write_text(
    "Date,Party Name,Transaction Type,Amount,Balance,Notes\n"
    "01-Jan-2026,Ramesh Bhosale,Credit,240,240,PhonePe\n"
    "02-Jan-2026,Ashok Patil,Credit,180,420,PhonePe\n"
    "03-Jan-2026,Sunita More,Credit,162,582,PhonePe\n"
    "04-Jan-2026,Vijay Kadam,Credit,340,922,Cash\n"
    "05-Jan-2026,Ramesh Bhosale,Credit,520,1442,PhonePe\n"
    "08-Jan-2026,Vijay Kadam,Credit,1040,2482,Wholesale\n"
    "11-Jan-2026,Priya Deshpande,Credit,1840,4322,Khata clear\n"
    "15-Jan-2026,Ashok Patil,Credit,2150,6472,Monthly settle\n"
    "22-Jan-2026,Vijay Kadam,Credit,2200,8672,Wholesale cash\n"
    "30-Jan-2026,Vijay Kadam,Credit,3400,12072,Month end\n"
    "28-Feb-2026,Suresh,Debit,4200,7872,Stock purchase\n"
    "20-Mar-2026,Vijay Kadam,Credit,4100,11972,March wholesale\n",
    encoding="utf-8")

P1.joinpath("bill_metadata.json").write_text(json.dumps({
    "bill_type": "ELECTRICITY", "provider": "MSEDCL",
    "consumer_number": "PNE-001-1234",
    "billing_period": "01-Dec-2025 to 31-Dec-2025",
    "bill_date": "2026-01-05", "due_date": "2026-01-20",
    "amount_due": 1840.0, "units_consumed": 312,
    "address_partial": "Shop No. 4, Sadashiv Peth",
    "ocr_confidence": 0.91, "agent_id": "AGENT_01_OCR"
}, indent=2), encoding="utf-8")

P1.joinpath("maps_data.json").write_text(json.dumps({
    "name": "Suresh Kirana & General Store",
    "lat": 18.5127, "lon": 73.8421,
    "rating": 4.2, "review_count": 38, "listing_age_years": 6.5,
    "source": "openstreetmap_nominatim", "confidence": 0.84
}, indent=2), encoding="utf-8")

# ── PERSONA 2: Rajesh Sharma — Cash Discrepancy ────────
P2 = DATA / "persona02_discrepancy"
P2.mkdir(parents=True, exist_ok=True)

P2.joinpath("persona.json").write_text(json.dumps({
    "persona_id": "persona02_discrepancy",
    "display_name": "Rajesh Sharma",
    "business_name": "Rajesh General & Provision Store",
    "business_type": "General Store",
    "location_masked": "Kothrud, Pune, Maharashtra",
    "years_in_operation": 4,
    "demo_mode": True,
    "expected_outcomes": {
        "warmth_grade": "B+",
        "pre_clarification_credit_limit": 60000,
        "credit_limit_range": [75000, 90000],
        "clarification_expected": True,
        "clarification_trigger": "SIGNIFICANT_CASH_GAP",
        "forensic_finding": "SIGNIFICANT"
    }
}, indent=2), encoding="utf-8")

P2.joinpath("whatsapp.txt").write_text(
    "01/01/2026, 10:00 - Rajesh: aaj WhatsApp se 1800 ka maal gaya\n"
    "01/01/2026, 11:30 - Mahesh Jadhav: 2000 cash diya wholesale bhai\n"
    "02/01/2026, 18:00 - Building contractor Sunil: 5000 cash ek saath diya\n"
    "07/01/2026, 11:00 - Mahesh Jadhav: 1500 cash diya aaj\n"
    "08/01/2026, 17:30 - Building contractor Sunil: 3000 cash site pe\n"
    "10/01/2026, 20:00 - Rajesh: is hafte 12000 ka business hua\n"
    "12/01/2026, 14:00 - Mahesh Jadhav: 2200 diya aaj\n"
    "15/01/2026, 10:02 - Customer Deepak: 850 PhonePe se\n"
    "17/01/2026, 18:00 - Building contractor Sunil: 8000 cash diya\n"
    "20/01/2026, 21:00 - Rajesh: January half mein 28000 ho gaya\n"
    "22/01/2026, 12:02 - Rajesh: contractor log cash dete hain mostly\n"
    "25/01/2026, 14:00 - Customer Deepak: 1200 sent PhonePe\n"
    "27/01/2026, 17:00 - Building contractor Sunil: 6000 cash last January\n"
    "30/01/2026, 21:00 - Rajesh: January mein total 52000 hua hoga\n"
    "05/02/2026, 11:00 - Mahesh Jadhav: 3000 cash diya\n"
    "10/02/2026, 16:00 - Building contractor Sunil: 7500 cash February order\n"
    "12/02/2026, 09:00 - Customer Deepak: 650 PhonePe\n"
    "20/02/2026, 19:00 - Rajesh: February mein 38000 cash business hua\n"
    "08/03/2026, 18:00 - Building contractor Sunil: 9000 cash March bada order\n"
    "22/03/2026, 11:00 - Customer Deepak: 1100 PhonePe\n"
    "25/03/2026, 17:00 - Building contractor Sunil: 11000 cash March final\n"
    "25/03/2026, 20:00 - Rajesh: March mein 40000 ka scope dikh raha hai\n",
    encoding="utf-8")

P2.joinpath("upi_events.json").write_text(json.dumps([
    {"transaction_id":"UPI90000001","date":"2026-01-15","time":"10:02:00","amount":850.0,"type":"CREDIT","counterparty_name":"Customer Deepak","upi_id":"deepak@ybl","reference":"Google Pay"},
    {"transaction_id":"UPI90000002","date":"2026-01-25","time":"14:00:00","amount":1200.0,"type":"CREDIT","counterparty_name":"Customer Deepak","upi_id":"deepak@ybl","reference":"Google Pay"},
    {"transaction_id":"UPI90000003","date":"2026-02-12","time":"09:00:00","amount":650.0,"type":"CREDIT","counterparty_name":"Customer Deepak","upi_id":"deepak@ybl","reference":"Google Pay"},
    {"transaction_id":"UPI90000004","date":"2026-03-22","time":"11:00:00","amount":1100.0,"type":"CREDIT","counterparty_name":"Customer Deepak","upi_id":"deepak@ybl","reference":"Google Pay"},
], indent=2), encoding="utf-8")

P2.joinpath("khata.csv").write_text(
    "Date,Party Name,Transaction Type,Amount,Balance,Notes\n"
    "01-Jan-2026,Mahesh Jadhav,Credit,2000,2000,Cash wholesale\n"
    "02-Jan-2026,Sunil Contractor,Credit,5000,7000,Cash site order\n"
    "07-Jan-2026,Mahesh Jadhav,Credit,1500,8500,Cash\n"
    "08-Jan-2026,Sunil Contractor,Credit,3000,11500,Cash\n"
    "12-Jan-2026,Mahesh Jadhav,Credit,2200,13700,Cash\n"
    "17-Jan-2026,Sunil Contractor,Credit,8000,21700,Cash large\n"
    "27-Jan-2026,Sunil Contractor,Credit,6000,27700,Cash\n"
    "05-Feb-2026,Mahesh Jadhav,Credit,3000,30700,Cash\n"
    "10-Feb-2026,Sunil Contractor,Credit,7500,38200,Cash\n"
    "08-Mar-2026,Sunil Contractor,Credit,9000,47200,Cash\n"
    "25-Mar-2026,Sunil Contractor,Credit,11000,58200,Cash final\n",
    encoding="utf-8")

P2.joinpath("bill_metadata.json").write_text(json.dumps({
    "bill_type": "ELECTRICITY", "provider": "MSEDCL",
    "amount_due": 1200.0, "units_consumed": 210,
    "ocr_confidence": 0.88, "agent_id": "AGENT_01_OCR"
}, indent=2), encoding="utf-8")

P2.joinpath("maps_data.json").write_text(json.dumps({
    "name": "Rajesh General Store",
    "lat": 18.5074, "lon": 73.8083,
    "source": "openstreetmap_nominatim", "confidence": 0.79
}, indent=2), encoding="utf-8")

# ── PERSONA 3: Akbar Khan — Seasonal Tailor ────────────
P3 = DATA / "persona03_seasonal"
P3.mkdir(parents=True, exist_ok=True)

P3.joinpath("persona.json").write_text(json.dumps({
    "persona_id": "persona03_seasonal",
    "display_name": "Akbar Khan",
    "business_name": "Akbar Master Tailors",
    "business_type": "Custom Tailoring",
    "location_masked": "Camp Area, Pune, Maharashtra",
    "years_in_operation": 11,
    "demo_mode": True,
    "expected_outcomes": {
        "warmth_grade": "B+",
        "credit_limit_range": [70000, 90000],
        "seasonal_detected": True,
        "peak_months": ["October", "November"],
        "underwriting_model": "SEASONAL_CREDIT",
        "clarification_expected": False,
        "forensic_finding": "NORMAL_CASH"
    }
}, indent=2), encoding="utf-8")

P3.joinpath("whatsapp.txt").write_text(
    "01/01/2026, 14:00 - Riya Madam: Akbar bhai sherwani ready hai?\n"
    "01/01/2026, 14:00 - Riya Madam: 8500 final payment diya\n"
    "03/01/2026, 12:00 - Farhan Sheikh: 12000 diya dono suits ke liye\n"
    "05/01/2026, 11:00 - Meena Kulkarni: 350 diya blouse liya\n"
    "10/01/2026, 14:10 - Riya Madam: 4500 advance PhonePe lehenga ke liye\n"
    "17/01/2026, 11:05 - Farhan Sheikh: 5400 sent teen kurte\n"
    "22/01/2026, 15:05 - Meena Kulkarni: 1200 sent 4 blouses\n"
    "31/01/2026, 21:00 - Akbar: January bahut achha gaya 72000 alhamdulillah\n"
    "05/02/2026, 16:00 - Riya Madam: 12000 balance lehenga liya\n"
    "10/02/2026, 14:10 - Farhan Sheikh: 3000 advance groom sherwani\n"
    "20/02/2026, 12:00 - Farhan Sheikh: 4500 balance sherwani\n"
    "28/02/2026, 21:00 - Akbar: February 58000 ka kaam hua shukr hai\n"
    "08/03/2026, 11:02 - Meena Kulkarni: 700 sent 2 blouses\n"
    "18/03/2026, 14:00 - Farhan Sheikh: 240 diya trouser hemming\n"
    "25/03/2026, 20:00 - Akbar: March mein 18000 se zyada nahi hoga lagta\n"
    "25/03/2026, 20:02 - Akbar: October November mein full booking ho jaati hai\n",
    encoding="utf-8")

seasonal = {1:2880,2:2320,3:700,4:350,5:200,6:220,7:280,8:600,9:1800,10:3800,11:4200,12:3100}
base = datetime(2026, 1, 1)
upi3 = []
for i in range(55):
    d = base - timedelta(days=i * 6)
    upi3.append({
        "transaction_id": f"UPI70{i:06d}",
        "date": d.strftime("%Y-%m-%d"),
        "time": "12:00:00",
        "amount": float(seasonal.get(d.month, 1000)),
        "type": "CREDIT",
        "counterparty_name": f"Client {i}",
        "upi_id": f"client{i}@oksbi",
        "reference": "PhonePe"
    })
P3.joinpath("upi_events.json").write_text(json.dumps(upi3, indent=2), encoding="utf-8")

P3.joinpath("khata.csv").write_text(
    "Date,Party Name,Transaction Type,Amount,Balance,Notes\n"
    "01-Jan-2026,Riya Madam,Credit,8500,8500,Sherwani final\n"
    "03-Jan-2026,Farhan Sheikh,Credit,12000,20500,2 suits\n"
    "10-Jan-2026,Riya Madam,Credit,4500,25000,Lehenga advance\n"
    "17-Jan-2026,Farhan Sheikh,Credit,5400,30400,3 kurtas\n"
    "05-Feb-2026,Riya Madam,Credit,12000,42400,Lehenga balance\n"
    "20-Feb-2026,Farhan Sheikh,Credit,7500,49900,Sherwani\n"
    "08-Mar-2026,Meena Kulkarni,Credit,700,50600,2 blouses\n"
    "18-Mar-2026,Farhan Sheikh,Credit,240,50840,Hemming\n",
    encoding="utf-8")

P3.joinpath("bill_metadata.json").write_text(json.dumps({
    "bill_type": "ELECTRICITY", "provider": "MSEDCL",
    "amount_due": 2100.0, "units_consumed": 380,
    "ocr_confidence": 0.89, "agent_id": "AGENT_01_OCR"
}, indent=2), encoding="utf-8")

P3.joinpath("maps_data.json").write_text(json.dumps({
    "name": "Akbar Master Tailors",
    "lat": 18.5136, "lon": 73.8817,
    "source": "openstreetmap_nominatim", "confidence": 0.82
}, indent=2), encoding="utf-8")

# ── SEED INTO DB ───────────────────────────────────────
DB = ROOT / "data" / "shadow_credit.db"
conn = sqlite3.connect(DB)
conn.execute("DELETE FROM artifacts WHERE agent_id='SEED_SCRIPT'")
conn.execute("DELETE FROM sessions  WHERE demo_mode=1")
conn.commit()

session_ids = {}
for pid, name, loc in [
    ("persona01_clean",       "Suresh Kumar",  "Sadashiv Peth, Pune"),
    ("persona02_discrepancy", "Rajesh Sharma", "Kothrud, Pune"),
    ("persona03_seasonal",    "Akbar Khan",    "Camp Area, Pune"),
]:
    sid = f"sc_{uuid.uuid4().hex[:8]}"
    session_ids[pid] = sid
    key_hash = hashlib.sha256(f"demo_seed_{pid}_{sid}".encode()).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO sessions "
        "(id, created_at, owner_name, location_masked, consent_given, session_key_hash, status, demo_mode) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (sid, now, name, loc, 1, key_hash, "PENDING", 1))
    conn.execute(
        "INSERT INTO artifacts "
        "(id, session_id, artifact_type, file_hash, encrypted_path, ocr_confidence, extracted_at, agent_id, processing_status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            f"art_{uuid.uuid4().hex[:8]}",
            sid,
            "WHATSAPP",
            f"demo_hash_{pid}",
            f"demo://personas/{pid}/whatsapp.txt.enc",
            1.0,
            now,
            "SEED_SCRIPT",
            "COMPLETE",
        ),
    )

conn.commit()
conn.close()

Path(__file__).parent.joinpath("demo_sessions.json").write_text(
    json.dumps({
        "persona01": session_ids["persona01_clean"],
        "persona02": session_ids["persona02_discrepancy"],
        "persona03": session_ids["persona03_seasonal"],
    }, indent=2), encoding="utf-8")

print("Persona files created:")
for pid in ["persona01_clean", "persona02_discrepancy", "persona03_seasonal"]:
    files = [f.name for f in (DATA / pid).iterdir()]
    print(f"  {pid}: {files}")

print("\nSeeded sessions:")
for k, v in session_ids.items():
    print(f"  {k}: {v}")
print("\nAll done!")
