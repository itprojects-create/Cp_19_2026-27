from pathlib import Path
import json
import random
from datetime import datetime, timedelta

# Create directories
Path("data/personas/persona01_clean").mkdir(parents=True, exist_ok=True)
Path("data/personas/persona02_discrepancy").mkdir(parents=True, exist_ok=True)
Path("data/personas/persona03_seasonal").mkdir(parents=True, exist_ok=True)

# ── PERSONA 1: Suresh Kumar — Clean Kirana, 90 days ───
p1 = [
# Week 1
"01/01/2026, 09:12 - Ramesh Bhosale: bhai kal ka udhaar 240 tha",
"01/01/2026, 09:14 - Suresh: haan aaj le lo",
"01/01/2026, 10:45 - Suresh: Ramesh bhai 240 mili PhonePe ✓",
"01/01/2026, 14:22 - Priya Deshpande: suresh bhai amul butter hai?",
"01/01/2026, 14:23 - Suresh: kal aayega delivery mein",
"02/01/2026, 08:03 - Suresh: <Media omitted>",
"02/01/2026, 11:15 - Ashok Patil: 2 kg basmati dena bhai ghar pe dedo",
"02/01/2026, 11:45 - Suresh: ₹180 delivered ✓",
"02/01/2026, 11:46 - Ashok Patil: done bhai 👍",
"03/01/2026, 07:58 - Suresh: <Media omitted>",
"03/01/2026, 13:30 - Sunita More: suresh bhai 500 wala maggi pack aur ek kg namak",
"03/01/2026, 14:02 - Suresh: total ₹162",
"03/01/2026, 14:05 - Sunita More: ₹162 sent ✓",
"04/01/2026, 09:00 - Vijay Kadam: bhai kal paisa nahi tha aaj dunga",
"04/01/2026, 09:01 - Suresh: koi baat nahi Vijay bhai",
"04/01/2026, 18:30 - Vijay Kadam: ₹340 cash diya",
"05/01/2026, 10:10 - Ramesh Bhosale: 5 kg aata 2 kg sugar 1L oil chahiye",
"05/01/2026, 10:45 - Suresh: ₹520 total PhonePe karo",
"05/01/2026, 10:47 - Ramesh Bhosale: ₹520 sent",
"06/01/2026, 12:00 - Priya Deshpande: bhai aaj band hai kya?",
"06/01/2026, 12:01 - Suresh: nahi khula hai aao",
"07/01/2026, 09:30 - Suresh: aaj sabzi wala nahi aaya stock thoda kam",
"07/01/2026, 17:45 - Vijay Kadam: bhai kal 1000 ka wholesale chahiye",
"07/01/2026, 17:46 - Suresh: theek hai kal 9 baje aana",
# Week 2
"08/01/2026, 08:00 - Suresh: <Media omitted>",
"08/01/2026, 09:10 - Vijay Kadam: aa gaya bhai",
"08/01/2026, 09:45 - Suresh: ₹1040 ho gaya thoda discount diya",
"08/01/2026, 09:47 - Vijay Kadam: ₹1040 PhonePe ✓",
"09/01/2026, 11:00 - Ashok Patil: bhai Parle-G 10 packet aur 2 kg dal",
"09/01/2026, 11:32 - Suresh: ₹245 total",
"09/01/2026, 11:40 - Ashok Patil: ₹245 sent",
"10/01/2026, 14:10 - Sunita More: bhai aaj ka total batao mera",
"10/01/2026, 14:12 - Suresh: Sunita ji ₹1,840 baaki hai is month",
"10/01/2026, 14:15 - Sunita More: ok kal clear karti hoon",
"11/01/2026, 10:00 - Priya Deshpande: ₹1840 sent bhai khata clear",
"11/01/2026, 10:02 - Suresh: received ✓ shukriya Priya ji",
"12/01/2026, 08:05 - Suresh: <Media omitted>",
"12/01/2026, 16:30 - Ramesh Bhosale: bhai Makar Sankranti ke liye til gul hai?",
"12/01/2026, 16:31 - Suresh: haan aao",
"13/01/2026, 10:20 - Ramesh Bhosale: ₹380 liya til gul aur rewdi",
"13/01/2026, 10:22 - Suresh: ₹380 mili ✓ Sankranti ki shubhkamnayein 🎉",
"14/01/2026, 09:00 - Vijay Kadam: bhai happy Makar Sankranti",
"14/01/2026, 09:01 - Suresh: same to you Vijay bhai 🙏",
# Week 3-4
"15/01/2026, 11:00 - Ashok Patil: bhai pura mahine ka hisaab batao",
"15/01/2026, 11:15 - Suresh: Ashok bhai ₹2,150 baaki hai",
"15/01/2026, 11:20 - Ashok Patil: ₹2150 done",
"16/01/2026, 08:00 - Suresh: <Media omitted>",
"17/01/2026, 13:45 - Sunita More: bhai kapoor aur dhoop batti hai?",
"17/01/2026, 13:46 - Suresh: haan dono hai",
"17/01/2026, 14:20 - Sunita More: ₹95 diya cash",
"18/01/2026, 09:30 - Priya Deshpande: bhai subah jaldi khulte ho?",
"18/01/2026, 09:31 - Suresh: 7:30 se khulta hoon",
"19/01/2026, 07:35 - Priya Deshpande: ₹420 diya subah wala saman",
"20/01/2026, 10:00 - Ramesh Bhosale: bhai 2 crate Bisleri chahiye",
"20/01/2026, 10:02 - Suresh: ₹480 ho gaye delivery free",
"20/01/2026, 10:10 - Ramesh Bhosale: ₹480 PhonePe ✓",
"21/01/2026, 08:05 - Suresh: <Media omitted>",
"22/01/2026, 15:00 - Vijay Kadam: bhai sham ko 5 baje milna hai",
"22/01/2026, 17:05 - Vijay Kadam: ₹2,200 cash wholesale payment",
"23/01/2026, 09:00 - Suresh: aaj stock late aaya sorry sab",
"24/01/2026, 11:10 - Ashok Patil: koi nahi bhai",
"25/01/2026, 14:30 - Sunita More: bhai Republic Day ke liye kuch special?",
"25/01/2026, 14:31 - Suresh: haan tiranga wali mithai aayi hai 🇮🇳",
"26/01/2026, 09:00 - Priya Deshpande: happy republic day suresh bhai!",
"26/01/2026, 09:01 - Suresh: Jai Hind! 🇮🇳 aaj bhi khula hoon",
"27/01/2026, 16:45 - Ramesh Bhosale: bhai ₹680 ka maal liya kal",
"27/01/2026, 16:46 - Suresh: ₹680 mili PhonePe ✓",
"28/01/2026, 10:00 - Vijay Kadam: bhai month end mein zyada order dunga",
"28/01/2026, 10:01 - Suresh: bilkul bhai ready hoon",
"29/01/2026, 08:05 - Suresh: <Media omitted>",
"30/01/2026, 17:00 - Vijay Kadam: ₹3,400 wholesale January last order",
"30/01/2026, 17:02 - Suresh: ₹3400 received ✓ shukriya Vijay bhai",
"31/01/2026, 21:00 - Suresh: January total ₹47,200 ho gaya alhamdulillah 🙏",
# Feb
"01/02/2026, 09:00 - Ashok Patil: bhai naya mahina shuru",
"01/02/2026, 09:01 - Suresh: haan Ashok bhai, aao fresh start",
"03/02/2026, 14:20 - Sunita More: bhai Valentine gifts hai kuch?",
"03/02/2026, 14:21 - Suresh: chocolate box aaya hai ₹150 se shuru",
"05/02/2026, 11:00 - Priya Deshpande: ₹590 diya aaj",
"07/02/2026, 08:00 - Suresh: <Media omitted>",
"10/02/2026, 16:00 - Ramesh Bhosale: bhai February mein thoda slow hai na",
"10/02/2026, 16:01 - Suresh: haan thoda season ka asar hai",
"14/02/2026, 12:00 - Vijay Kadam: bhai Valentine pe offer?",
"14/02/2026, 12:01 - Suresh: haan chocolate 10% off aaj only 😄",
"14/02/2026, 14:30 - Vijay Kadam: ₹450 diya",
"20/02/2026, 08:05 - Suresh: <Media omitted>",
"22/02/2026, 18:00 - Ashok Patil: bhai pura Feb total?",
"22/02/2026, 18:10 - Suresh: Ashok bhai ₹1,950 ho gaya tumhara",
"22/02/2026, 18:12 - Ashok Patil: ₹1950 PhonePe ✓",
"28/02/2026, 21:30 - Suresh: February done ₹38,900 total thoda kam tha 📊",
# March
"01/03/2026, 09:00 - Suresh: <Media omitted>",
"05/03/2026, 11:30 - Sunita More: bhai Holi ke liye rang gulal aaya?",
"05/03/2026, 11:31 - Suresh: kal aayega Sunita ji",
"07/03/2026, 10:00 - Priya Deshpande: bhai ₹1,200 aaj Holi shopping",
"07/03/2026, 10:05 - Suresh: ₹1200 mili ✓ Happy Holi advance 🎨",
"10/03/2026, 08:00 - Suresh: <Media omitted>",
"15/03/2026, 14:00 - Ramesh Bhosale: bhai March mein stock badha do",
"15/03/2026, 14:01 - Suresh: haan supplier ko bol diya",
"20/03/2026, 17:45 - Vijay Kadam: ₹4,100 wholesale March order",
"20/03/2026, 17:46 - Suresh: ₹4100 received ✓",
"25/03/2026, 08:05 - Suresh: <Media omitted>",
"25/03/2026, 21:00 - Suresh: March almost done ₹52,000+ lag raha hai 💪",
]

# ── PERSONA 2: Rajesh Sharma — Cash Discrepancy ────────
p2 = [
"01/01/2026, 10:00 - Rajesh: aaj WhatsApp se ₹1800 ka maal gaya",
"01/01/2026, 11:30 - Mahesh Jadhav: ₹2000 cash diya wholesale bhai",
"01/01/2026, 11:31 - Rajesh: ok received",
"02/01/2026, 09:00 - Rajesh: <Media omitted>",
"02/01/2026, 15:00 - Building contractor Sunil: bhai 5000 ka maal chahiye tiling ke liye",
"02/01/2026, 15:01 - Rajesh: aao",
"02/01/2026, 18:00 - Building contractor Sunil: ₹5000 cash ek saath diya",
"03/01/2026, 12:00 - Rajesh: aaj bhi ₹2,400 ka business hua",
"04/01/2026, 10:00 - Mahesh Jadhav: bhai PhonePe se nahi hoga? Cash hi dena padega?",
"04/01/2026, 10:01 - Rajesh: haan contractor log cash dete hain mostly",
"05/01/2026, 08:00 - Rajesh: <Media omitted>",
"05/01/2026, 19:00 - Rajesh: aaj ka total ₹3,200 ho gaya",
"07/01/2026, 11:00 - Mahesh Jadhav: ₹1500 cash diya aaj",
"08/01/2026, 16:00 - Building contractor Sunil: bhai phir 3000 chahiye site pe",
"08/01/2026, 17:30 - Building contractor Sunil: ₹3000 cash diya",
"10/01/2026, 09:00 - Rajesh: <Media omitted>",
"10/01/2026, 20:00 - Rajesh: is hafte ₹12,000+ ka business hua alhamdulillah",
"12/01/2026, 14:00 - Mahesh Jadhav: ₹2200 diya aaj",
"14/01/2026, 11:00 - Rajesh: Sankranti pe ₹4,500 ek din mein cash mila",
"15/01/2026, 08:00 - Rajesh: <Media omitted>",
"15/01/2026, 10:00 - Customer Deepak: bhai ₹850 PhonePe se",
"15/01/2026, 10:02 - Rajesh: received ✓",
"17/01/2026, 16:00 - Building contractor Sunil: site pe 8000 ka maal chahiye bhai",
"17/01/2026, 18:00 - Building contractor Sunil: ₹8000 cash diya",
"17/01/2026, 18:01 - Rajesh: ok",
"20/01/2026, 08:05 - Rajesh: <Media omitted>",
"20/01/2026, 21:00 - Rajesh: January half mein ₹28,000 ho gaya",
"22/01/2026, 12:00 - Mahesh Jadhav: bhai tu sirf cash kyun leta hai?",
"22/01/2026, 12:02 - Rajesh: arre contractor log aise hi dete hain",
"25/01/2026, 14:00 - Customer Deepak: ₹1,200 sent PhonePe",
"27/01/2026, 17:00 - Building contractor Sunil: ₹6000 cash last January order",
"30/01/2026, 21:00 - Rajesh: January mein total ₹52,000 hua hoga",
"01/02/2026, 08:00 - Rajesh: <Media omitted>",
"05/02/2026, 11:00 - Mahesh Jadhav: ₹3000 cash diya",
"10/02/2026, 16:00 - Building contractor Sunil: ₹7500 cash February order",
"12/02/2026, 09:00 - Customer Deepak: ₹650 PhonePe",
"15/02/2026, 08:05 - Rajesh: <Media omitted>",
"20/02/2026, 19:00 - Rajesh: February mein ₹38,000 cash business hua",
"25/02/2026, 14:00 - Mahesh Jadhav: bhai kab tak cash hi chalega?",
"25/02/2026, 14:01 - Rajesh: supplier bhi cash leta hai toh main bhi leta hoon",
"01/03/2026, 09:00 - Rajesh: <Media omitted>",
"08/03/2026, 18:00 - Building contractor Sunil: ₹9000 cash March bada order",
"15/03/2026, 20:00 - Rajesh: March mein bhi ₹40,000+ ka scope dikh raha hai",
"20/03/2026, 08:05 - Rajesh: <Media omitted>",
"22/03/2026, 11:00 - Customer Deepak: ₹1,100 PhonePe ✓",
"25/03/2026, 17:00 - Building contractor Sunil: ₹11,000 cash March final",
"25/03/2026, 17:01 - Rajesh: ok mila",
]

# ── PERSONA 3: Akbar Khan — Seasonal Tailor ───────────
p3 = [
# Jan (peak season, post-wedding)
"01/01/2026, 10:00 - Akbar: Naya Saal Mubarak sab ko 🎉",
"01/01/2026, 11:30 - Riya Madam: Akbar bhai sherwani ready hai?",
"01/01/2026, 11:31 - Akbar: haan aaj le jaiye fitting perfect hai",
"01/01/2026, 14:00 - Riya Madam: ₹8500 final payment diya ✓",
"02/01/2026, 09:00 - Akbar: <Media omitted>",
"03/01/2026, 10:30 - Farhan Sheikh: bhai 2 suits ready ho gaye?",
"03/01/2026, 10:31 - Akbar: haan aao",
"03/01/2026, 12:00 - Farhan Sheikh: ₹12,000 diya dono suits ke liye",
"05/01/2026, 16:00 - Meena Kulkarni: bhai blouse stitching ₹350?",
"05/01/2026, 16:01 - Akbar: haan kal aao",
"07/01/2026, 08:05 - Akbar: <Media omitted>",
"07/01/2026, 11:00 - Meena Kulkarni: ₹350 diya blouse liya",
"10/01/2026, 14:00 - Riya Madam: bhai February wedding ke liye lehenga chahiye",
"10/01/2026, 14:01 - Akbar: haan le sakte hain ₹4500 advance dena",
"10/01/2026, 14:10 - Riya Madam: ₹4500 advance PhonePe ✓",
"12/01/2026, 09:00 - Akbar: <Media omitted>",
"15/01/2026, 20:00 - Akbar: January pehla hafte ₹25,000+ aa gaya alhamdulillah 🙏",
"17/01/2026, 11:00 - Farhan Sheikh: bhai 3 more kurtas for brother's wedding",
"17/01/2026, 11:02 - Akbar: ₹5,400 hoga teen kurte",
"17/01/2026, 11:05 - Farhan Sheikh: ₹5400 sent ✓",
"20/01/2026, 08:00 - Akbar: <Media omitted>",
"22/01/2026, 15:00 - Meena Kulkarni: bhai saree blouse 4 pieces",
"22/01/2026, 15:01 - Akbar: ₹1,200 hoga",
"22/01/2026, 15:05 - Meena Kulkarni: ₹1200 sent ✓",
"28/01/2026, 21:00 - Akbar: January bahut achha gaya ₹72,000+ 📊",
# Feb (still good, wedding season)
"02/02/2026, 10:00 - Riya Madam: bhai lehenga fitting kab?",
"02/02/2026, 10:01 - Akbar: Saturday aao",
"05/02/2026, 16:00 - Riya Madam: perfect fitting! ₹12,000 balance diya",
"08/02/2026, 09:00 - Akbar: <Media omitted>",
"10/02/2026, 14:00 - Farhan Sheikh: bhai groom sherwani February end chahiye",
"10/02/2026, 14:02 - Akbar: ₹7500 hoga advance ₹3000 dena",
"10/02/2026, 14:10 - Farhan Sheikh: ₹3000 advance sent",
"15/02/2026, 08:05 - Akbar: <Media omitted>",
"18/02/2026, 11:00 - Meena Kulkarni: bhai petticoat stitching?",
"18/02/2026, 11:01 - Akbar: ₹150 each",
"20/02/2026, 12:00 - Farhan Sheikh: sherwani le gaya ₹4500 balance",
"25/02/2026, 08:00 - Akbar: <Media omitted>",
"28/02/2026, 21:00 - Akbar: February ₹58,000 ka kaam hua shukr hai",
# March (tapering off)
"02/03/2026, 10:00 - Akbar: <Media omitted>",
"05/03/2026, 14:00 - Riya Madam: bhai koi naya order nahi abhi",
"05/03/2026, 14:01 - Akbar: haan March thoda slow hota hai",
"08/03/2026, 11:00 - Meena Kulkarni: bhai 2 blouse",
"08/03/2026, 11:02 - Akbar: ₹700 hoga",
"08/03/2026, 14:00 - Meena Kulkarni: ₹700 sent",
"12/03/2026, 09:00 - Akbar: <Media omitted>",
"15/03/2026, 16:00 - Akbar: March mein kaam kam hai yaar roz alterations hi hain",
"18/03/2026, 11:00 - Farhan Sheikh: bhai trouser hemming 2 pieces",
"18/03/2026, 11:01 - Akbar: ₹120 each",
"18/03/2026, 14:00 - Farhan Sheikh: ₹240 diya",
"22/03/2026, 10:00 - Akbar: <Media omitted>",
"25/03/2026, 20:00 - Akbar: March mein ₹18,000 se zyada nahi hoga lagta 😔 Summer aane wala hai",
"25/03/2026, 20:01 - Riya Madam: Akbar bhai October mein phir aayenge shaadi season mein",
"25/03/2026, 20:02 - Akbar: haan Riya ji October November mein full booking ho jaati hai 😊",
]

Path("data/personas/persona_01_clean/whatsapp.txt").write_text("\n".join(p1), encoding="utf-8")
Path("data/personas/persona_02_discrepancy/whatsapp.txt").write_text("\n".join(p2), encoding="utf-8")
Path("data/personas/persona_03_seasonal/whatsapp.txt").write_text("\n".join(p3), encoding="utf-8")
print("✅ Realistic WhatsApp chats written for all 3 personas")

# ── FIX UPI DATA to match WhatsApp amounts ─────────────

# Persona 1: clean UPI matching WhatsApp credits
random.seed(42)
upi1 = []
amounts_p1 = [240,180,162,340,520,1040,245,1840,380,2150,95,420,480,2200,
              680,3400,590,450,1950,1200,4100,47,1200,4500,8500,350]
for i, amt in enumerate(amounts_p1):
    d = (datetime(2026,1,1) + timedelta(days=i*3)).strftime("%Y-%m-%d")
    names = ["ramesh","priya","ashok","sunita","vijay"]
    upi1.append({"transaction_id":f"UPI80{i:06d}","date":d,"time":f"{9+i%11:02d}:{15+i%40:02d}:00",
                 "amount":float(amt),"type":"CREDIT","counterparty_name":names[i%5].title()+" Customer",
                 "upi_id":f"{names[i%5]}@paytm","reference":"PhonePe"})
Path("data/personas/persona_01_clean/upi_events.json").write_text(json.dumps(upi1,indent=2),encoding="utf-8")

# Persona 2: UPI only captures ~35% of revenue (the forensic gap)
amounts_p2_upi = [850, 650, 1100, 1200]  # only digital payments
upi2 = []
for i, amt in enumerate(amounts_p2_upi):
    d = (datetime(2026,1,1) + timedelta(days=i*22)).strftime("%Y-%m-%d")
    upi2.append({"transaction_id":f"UPI90{i:06d}","date":d,"time":"11:00:00",
                 "amount":float(amt),"type":"CREDIT","counterparty_name":f"Customer Deepak",
                 "upi_id":"deepak.k@ybl","reference":"Google Pay"})
Path("data/personas/persona_02_discrepancy/upi_events.json").write_text(json.dumps(upi2,indent=2),encoding="utf-8")

# Persona 3: UPI shows clear seasonal curve
seasonal_upi = {1:2400,2:1933,3:700,4:350,5:200,6:220,7:280,8:600,9:1800,10:3800,11:4200,12:3100}
upi3 = []
for i in range(60):
    d = datetime(2026,1,1) - timedelta(days=i*6)
    amt = seasonal_upi.get(d.month, 1000)
    upi3.append({"transaction_id":f"UPI70{i:06d}","date":d.strftime("%Y-%m-%d"),"time":"12:00:00",
                 "amount":float(amt),"type":"CREDIT","counterparty_name":f"Client {i}",
                 "upi_id":f"client{i}@oksbi","reference":"PhonePe"})
Path("data/personas/persona_03_seasonal/upi_events.json").write_text(json.dumps(upi3,indent=2),encoding="utf-8")

print("✅ UPI data updated — Persona 2 cash gap is now forensically visible")
print("\n📊 Persona 2 story: WhatsApp shows ₹52k+ Jan revenue, UPI only ₹3,800 total")
print("   → AI should flag SIGNIFICANT_CASH_GAP and trigger clarification ✅")
print("📊 Persona 3 story: UPI amounts follow Oct>Nov>Jan>Feb>>>May seasonal curve")
print("   → AI should detect SEASONAL_CREDIT underwriting model ✅")
