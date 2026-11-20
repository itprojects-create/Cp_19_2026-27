<div align="center">

# 🏦 Shadow Credit

### AI-Powered Credit Assessment for Indian MSMEs

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Automating credit decisions for unbanked small businesses in 90 seconds**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API](#-api-endpoints) • [Demo](#-demo-mode)

</div>

---

## 🎯 Problem Statement

**380 million Indians** lack access to formal credit. Traditional banks require:
- 📄 3+ years of ITR filings
- 🏛️ GST registration
- 💳 Credit history (CIBIL score)

**Kirana stores and small retailers** operate informally with:
- WhatsApp payment confirmations
- UPI transaction screenshots
- Handwritten ledgers (Khata books)
- No formal documentation

**Shadow Credit** bridges this gap by extracting financial signals from informal documents and generating bank-grade credit assessments.

---

## ✨ Features

### 🤖 7 Specialized AI Agents

| Agent | Function |
|-------|----------|
| **Agent 00** | Google Maps verification — validates business existence, ratings, reviews |
| **Agent 01** | OCR extraction — processes bills, UPI screenshots with Hindi support |
| **Agent 02** | WhatsApp parser — classifies financial transactions from Hinglish chats |
| **Agent 03** | Khata Book — parses handwritten ledger entries |
| **Agent 04** | Credit Warmth Score — ML-based scoring using 7 financial signals |
| **Agent 05** | Forensic Reconciliation — detects gaps, generates RBI-compliant hypotheses |
| **Agent 06** | Compliance — RBI MSME checklist verification |
| **Agent 07** | Credit Report — generates professional PDF memos |

### 🎛️ Intelligent Orchestration

- **Supervisor Agent** coordinates all agents with dynamic execution
- **Human-in-the-loop** — pipeline pauses for clarification, resumes automatically
- **Real-time WebSocket** streaming shows live agent progress
- **Auto-decision engine**: AUTO_ACCEPT / CLARIFY / FALLBACK based on confidence

### 🔒 Privacy & Compliance

- **AES-256-GCM** encryption for all sensitive data
- **DPDP Act 2023** compliant — consent tracking, right-to-erasure
- **Immutable audit log** — database triggers prevent tampering
- **No unencrypted PII** stored

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional)

### 1. Clone & Setup Environment

```bash
git clone https://github.com/pranavpanchal1326/shadow-credit.git
cd shadow-credit

# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

### 2. Configure Environment Variables

```env
# Required
MASTER_ENCRYPTION_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
GROQ_API_KEY=<get free key from console.groq.com>

# Optional
GOOGLE_MAPS_API_KEY=<for business verification>
```

### 3. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Open Application

```
http://localhost:3000/apply
```

### Docker Alternative

```bash
docker-compose up
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 15)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Apply   │  │Processing│  │  Result  │  │    Dashboard     │ │
│  │   Form   │  │  Stream  │  │  Display │  │    (RM View)     │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ WebSocket + REST
┌─────────────────────────────▼───────────────────────────────────┐
│                        BACKEND (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    SUPERVISOR AGENT                       │   │
│  │   Orchestrates pipeline • Decision engine • Clarification │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌────────┬────────┬────────┼────────┬────────┬────────┬─────┐  │
│  │Agent 00│Agent 01│Agent 02│Agent 03│Agent 04│Agent 05│  06 │  │
│  │  Maps  │  OCR   │WhatsApp│ Khata  │Warmth  │Forensic│Compl│  │
│  └────────┴────────┴────────┴────────┴────────┴────────┴─────┘  │
│                              │                                   │
│  ┌──────────────────────────▼──────────────────────────────┐    │
│  │              Agent 07 — Credit Report Generator          │    │
│  │                   (ReportLab PDF + QR Code)              │    │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                     EXTERNAL SERVICES                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Groq    │  │  Google  │  │ EasyOCR  │  │     SQLite       │ │
│  │  LLM     │  │  Maps    │  │ (Local)  │  │   (Encrypted)    │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📡 API Endpoints

### Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/sessions` | Create new session (requires consent) |
| `GET` | `/api/v1/sessions/{id}` | Fetch session status |
| `POST` | `/api/v1/sessions/{id}/analyze` | Trigger analysis pipeline |
| `POST` | `/api/v1/sessions/{id}/clarify` | Answer clarification question |
| `POST` | `/api/v1/sessions/{id}/export` | Download PDF report |
| `DELETE` | `/api/v1/sessions/{id}` | Right-to-erasure (DPDP) |

### Document Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ingest/whatsapp/{id}` | Upload WhatsApp chat |
| `POST` | `/api/v1/ingest/upi/{id}` | Upload UPI screenshot |
| `POST` | `/api/v1/ingest/bill/{id}` | Upload utility bill |
| `POST` | `/api/v1/ingest/khata/{id}` | Upload ledger photo |

### Real-time Events

| Protocol | Endpoint | Description |
|----------|----------|-------------|
| `WebSocket` | `/ws/{session_id}` | Live agent progress stream |

---

## 🎭 Demo Mode

Three pre-configured personas for testing:

| Persona | Scenario | Duration |
|---------|----------|----------|
| **Suresh** | Clean approval — straightforward case | ~45 sec |
| **Meena** | Discrepancy detected — triggers clarification modal | ~60 sec |
| **Raju** | Seasonal pattern — requires analysis | ~48 sec |

```bash
# Create demo session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"demo_mode": true, "consent_given": true}'

# Trigger analysis with persona
curl -X POST "http://localhost:8000/api/v1/sessions/{session_id}/analyze?persona_id=persona02_discrepancy"
```

---

## 🧠 Credit Scoring Model

**XGBoost-based ML model** with 7 weighted signals:

| Signal | Weight | Description |
|--------|--------|-------------|
| Income Regularity | 26.6% | Consistency of monthly inflows |
| Inflow-Claim Consistency | 20.9% | WhatsApp claims vs. UPI verification |
| Business Continuity | 19.0% | Google Maps presence, reviews, tenure |
| Seasonal Patterns | 14.25% | Revenue fluctuation analysis |
| Network Reliability | 9.5% | Repeat customer transactions |
| Data Source Diversity | 4.75% | Multiple verification sources |
| Behavioral Consistency | 5.0% | Transaction timing patterns |

**Credit Grade Scale:**
- **A+**: ≥0.85 — Auto-approve
- **A**: ≥0.75 — High confidence
- **B+**: ≥0.65 — Moderate confidence  
- **B**: ≥0.55 — Clarification needed
- **C**: <0.55 — Manual review

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — async Python web framework
- **Groq** — LLaMA 3.3 70B for reasoning
- **XGBoost + SHAP** — ML scoring with explainability
- **EasyOCR** — offline OCR with Hindi support
- **SQLite** — encrypted database with WAL mode
- **ReportLab** — PDF generation

### Frontend
- **Next.js 15** — React framework
- **Tailwind CSS** — styling
- **Radix UI** — accessible components
- **Zustand** — state management
- **React Query** — data fetching
- **Recharts** — visualizations

---

## 📁 Project Structure

```
shadow-credit/
├── backend/
│   ├── agents/           # 7 AI agents + supervisor
│   ├── api/              # REST endpoints
│   ├── core/             # Security, events, AI client
│   ├── db/               # Database schema & queries
│   └── main.py           # FastAPI application
├── frontend/
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   └── hooks/            # Custom hooks
└── docker-compose.yml    # Container orchestration
```

---

## 💰 Cost

| Service | Cost |
|---------|------|
| Groq API | **Free** (500+ calls/day) |
| EasyOCR | **Free** (local) |
| Google Maps | ~$0.50 (on $200 free credit) |
| **Total** | **$0.00** |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built for Indian MSMEs** 🇮🇳

*Democratizing credit access through AI*

</div>
