import os
import socket
import sqlite3

import requests


def check(label, fn):
    try:
        result = fn()
        print(f"  ✅ {label}: {result}")
        return True
    except Exception as e:
        print(f"  ❌ {label}: {e}")
        return False


print("\n🔍 Shadow Credit — System Status Check\n" + "=" * 45)

# 1. FastAPI Backend
check(
    "Backend (port 8000)",
    lambda: requests.get("http://localhost:8000/api/v1/health", timeout=3).json()["data"]["status"],
)

# 2. Next.js Frontend
check(
    "Frontend (port 3000)",
    lambda: str(requests.get("http://localhost:3000", timeout=3).status_code),
)

# 3. Groq API
def check_groq():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        env_path = os.path.join("backend", ".env")
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        break
    if not key:
        raise Exception("NOT SET — add to backend/.env")
    return f"SET ({key[:8]}...)"


check("Groq API key set", check_groq)

# 4. SQLite DB
check(
    "SQLite DB exists",
    lambda: "OK"
    if os.path.exists("backend/data/shadow_credit.db")
    else (_ for _ in ()).throw(Exception("Missing")),
)


# 5. Demo personas seeded
def check_personas():
    conn = sqlite3.connect("data/shadow_credit.db")
    count = conn.execute("SELECT COUNT(*) FROM sessions WHERE demo_mode=1").fetchone()[0]
    conn.close()
    if count >= 3:
        return f"{count} personas seeded"
    raise Exception(f"Only {count} found — run seed_personas.py")


check("Demo personas", check_personas)

# 6. demo_sessions.json
check(
    "demo_sessions.json",
    lambda: "OK"
    if os.path.exists("scripts/demo_sessions.json")
    else (_ for _ in ()).throw(Exception("Missing — run seed_personas.py")),
)


# 7. Ports in use (netstat alternative)
def port_open(port):
    s = socket.socket()
    s.settimeout(1)
    result = s.connect_ex(("127.0.0.1", port))
    s.close()
    return result == 0


check(
    "Port 8000 listening",
    lambda: "YES" if port_open(8000) else (_ for _ in ()).throw(Exception("Backend not listening")),
)
check(
    "Port 3000 listening",
    lambda: "YES" if port_open(3000) else (_ for _ in ()).throw(Exception("Frontend not listening")),
)

print("\n" + "=" * 45)
