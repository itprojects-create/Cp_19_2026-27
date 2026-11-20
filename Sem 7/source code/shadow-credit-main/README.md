<div align="center">

# 🏦 Shadow Credit

### AI-Powered Credit Assessment for Indian MSMEs

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Making credit assessment more accessible to India's small and informal businesses.**

[Features](#-features) • [Workflow](#-how-it-works) • [Architecture](#-architecture) • [Tech Stack](#-technology-stack) • [Quick Start](#-quick-start) • [API](#-api-endpoints)

</div>

---

## 🎯 Problem Statement

Many small businesses in India, such as kirana stores, neighbourhood shops and local retailers, operate successfully without maintaining the formal financial records traditionally expected by banks.

Traditional credit assessment often relies on documents and records such as:

- Income Tax Returns (ITR)
- GST registration and filings
- Formal banking statements
- Established credit history

However, small and informal businesses may demonstrate their financial activity through other sources, including:

- WhatsApp payment confirmations and customer conversations
- UPI transaction screenshots
- Electricity and other utility bills
- Address proof
- Handwritten business ledgers (Khata books)

This creates an information gap: a business may have regular customers and consistent financial activity but may not have enough conventional documentation to demonstrate its creditworthiness.

**Shadow Credit** aims to bridge this gap by analysing alternative business information and generating structured credit assessment outputs.

---

## ✨ Features

### 🤖 Seven Specialized AI Agents + Supervisor

Shadow Credit uses seven agents in its main assessment workflow. A Supervisor Agent coordinates their execution.

| Agent                    | Function                                                                                                                      |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| **Maps Agent**           | Verifies the business location and gathers available business information through map services.                               |
| **OCR Agent**            | Extracts information from uploaded documents and images, including bills and UPI screenshots, with Hindi and English support. |
| **WhatsApp Agent**       | Parses exported WhatsApp business chats and identifies relevant financial information and transaction-related signals.        |
| **Warmth Agent**         | Uses an ML-based model to calculate the business's Credit Warmth Score from financial signals.                                |
| **Reconciliation Agent** | Compares information from different sources, identifies discrepancies and generates findings for review.                      |
| **Compliance Agent**     | Checks the available information against the project's MSME compliance checklist.                                             |
| **Report Agent**         | Generates the credit assessment report, including a PDF credit memo and QR code.                                              |

**Supervisor Agent**

- Coordinates the agents and manages the assessment workflow.
- Handles agent execution and the overall pipeline.
- Supports human-in-the-loop clarification when additional information is needed.
- Uses confidence-based outcomes such as `AUTO_ACCEPT`, `CLARIFY` and `FALLBACK`.
- Streams agent progress to the frontend through WebSockets.

> **Agent count clarification:** The main workflow is described as **seven agents plus one Supervisor**. Khata and SMS-related agent code may exist in the repository, but they are not counted as part of the seven-agent workflow described above.

### 📄 Multiple Document Sources

The platform accepts different types of information to build a broader picture of a business.

| Document / Data Source               | Purpose                                                                    |
| ------------------------------------ | -------------------------------------------------------------------------- |
| **WhatsApp chat export**             | Provides business conversations and payment-related messages for analysis. |
| **UPI screenshots**                  | Provide transaction-related information.                                   |
| **Electricity bill**                 | Supports address and business-location information.                        |
| **Address proof**                    | Helps establish the business or owner's address.                           |
| **Other supporting bills/documents** | Provide additional information relevant to the assessment.                 |

The application includes a document upload workflow and displays the submitted files before analysis begins. The exact accepted file extensions and upload-size limits should be checked against the current backend configuration.

### 🎛️ Intelligent Orchestration

- Supervisor-led coordination of the assessment pipeline.
- Human-in-the-loop clarification when the system needs additional information.
- Real-time WebSocket updates for agent progress and logs.
- Confidence-based handling of automatic acceptance, clarification and fallback cases.

### 📊 Credit Assessment

The project uses an XGBoost-based machine learning model to calculate a Credit Warmth Score using multiple financial and business signals.

The assessment considers factors such as income regularity, consistency between reported and verified information, business continuity, seasonal patterns, repeat-customer activity, source diversity and behavioural consistency.

### 📑 Three Assessment Outputs

The platform generates three types of outputs:

1. **Bank-Facing Credit Memo** – a structured assessment report intended for bank or lender review.
2. **Credit Passport** – a simplified credit profile for the business owner, with QR-based verification as described by the application.
3. **OCEN 4.0 JSON** – a machine-readable assessment output intended for compatible digital lending workflows.

### 🔒 Privacy and Security

The project includes security and privacy-related mechanisms such as:

- AES-256-GCM encryption for sensitive data.
- Consent tracking before document analysis.
- A session deletion flow intended to support the right to erasure.
- Audit logging and database-level protections.
- Hashing of uploaded artefacts and generated reports.

The exact security guarantees depend on the deployed configuration and implementation. See [Privacy and Consent](#-privacy-and-consent).

---

## 🔄 How It Works

```text
                    BUSINESS OWNER
                          |
                          v
                Enter business details
                          |
                          v
                 Upload documents
          (WhatsApp, UPI, bills, address proof)
                          |
                          v
                  Review application
                          |
                          v
                   Give consent
                          |
                          v
                  Start assessment
                          |
                          v
              +-----------------------+
              |    SUPERVISOR AGENT   |
              | Coordinates workflow  |
              +-----------------------+
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
      Maps Agent       OCR Agent       WhatsApp Agent
          |               |                |
          +---------------+----------------+
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
      Warmth Agent   Reconciliation    Compliance
                         Agent           Agent
          |               |                |
          +---------------+----------------+
                          |
                          v
                    Report Agent
                          |
                          v
               Consolidated assessment
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
       Credit Memo   Credit Passport    OCEN 4.0 JSON
```

### Step-by-step workflow

1. **Business onboarding:** The user enters the business name, owner's name, location and business category.
2. **Document submission:** The user uploads supporting records such as WhatsApp chat exports, UPI screenshots, electricity bills and address proof.
3. **Application review:** The application displays the business details and uploaded documents for review.
4. **Consent:** The user provides consent before the assessment starts.
5. **Agent processing:** The Supervisor coordinates the seven agents that analyse different aspects of the submitted information.
6. **Reconciliation and scoring:** Findings from the available sources are compared, and the Warmth scoring process evaluates the relevant financial signals.
7. **Report generation:** The Report Agent prepares the assessment outputs.
8. **Result display:** The user can view the generated credit assessment and its supported output formats.

---

## 🧠 Credit Scoring Model

Shadow Credit uses an **XGBoost-based machine learning model**, with scikit-learn and SHAP used for model support and explanations.

The model considers seven financial and behavioural signals:

| Signal                   | Weight | Description                                                    |
| ------------------------ | -----: | -------------------------------------------------------------- |
| Income Regularity        |  26.6% | Consistency of monthly inflows.                                |
| Inflow-Claim Consistency |  20.9% | Comparison of WhatsApp claims with UPI-related information.    |
| Business Continuity      |  19.0% | Business presence, available reviews and business tenure.      |
| Seasonal Patterns        | 14.25% | Analysis of revenue fluctuations and seasonal activity.        |
| Network Reliability      |   9.5% | Repeat-customer transaction patterns.                          |
| Data Source Diversity    |  4.75% | Availability of multiple information sources for verification. |
| Behavioral Consistency   |   5.0% | Patterns in transaction timing and activity.                   |

### Credit Grade Scale

| Grade  |  Score | Interpretation       |
| ------ | -----: | -------------------- |
| **A+** | ≥ 0.85 | Auto-approve         |
| **A**  | ≥ 0.75 | High confidence      |
| **B+** | ≥ 0.65 | Moderate confidence  |
| **B**  | ≥ 0.55 | Clarification needed |
| **C**  | < 0.55 | Manual review        |

The grades and thresholds above describe the scoring scale documented by the project. They should not be interpreted as a guarantee of loan approval or as an actual bank sanction decision.

---

## 📑 Assessment Outputs

### 1. Bank-Facing Credit Memo

A structured PDF credit assessment intended for review by banks and financial institutions. The project describes its format as aligned with SIDBI/PSU bank MSME credit appraisal requirements.

The generated report is intended to present relevant business information, financial signals and assessment findings in a lender-oriented format.

### 2. Credit Passport

A simplified credit profile intended for the business owner. It presents the assessment in a more accessible format and includes QR-based verification as described by the project.

### 3. OCEN 4.0 JSON

A structured JSON representation of the assessment intended for compatible systems and digital lending workflows.

The availability of a JSON output does not by itself establish a live connection to the OCEN network.

---

## 🏗️ Architecture

```text
┌───────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js 15)                     │
│                                                               │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────┐ │
│   │ Application│  │ Processing │  │  Results   │  │Dashboard│ │
│   │    Form    │  │   Stream   │  │  Display   │  │         │ │
│   └────────────┘  └────────────┘  └────────────┘  └─────────┘ │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                       REST API + WebSocket
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                      BACKEND (FastAPI)                        │
│                                                               │
│                  ┌─────────────────────┐                      │
│                  │   SUPERVISOR AGENT  │                      │
│                  │  Workflow control  │                      │
│                  └──────────┬──────────┘                      │
│                             │                                 │
│       ┌─────────┬───────────┼──────────┬──────────┐           │
│       │         │           │          │          │           │
│       ▼         ▼           ▼          ▼          ▼           │
│     Maps       OCR       WhatsApp    Warmth   Reconciliation  │
│     Agent     Agent       Agent      Agent       Agent        │
│       │         │           │          │          │           │
│       └─────────┴───────────┼──────────┴──────────┘           │
│                             │                                 │
│                   ┌─────────┴────────┐                        │
│                   ▼                  ▼                        │
│              Compliance           Report                      │
│                Agent              Agent                       │
└─────────────────────────────┬─────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                    DATA & EXTERNAL SERVICES                   │
│                                                               │
│  Groq / LLaMA 3.1 70B  │  OCR engines  │  Google Maps API     │
│  SQLite + aiosqlite    │  Local files  │  XGBoost + SHAP      │
└───────────────────────────────────────────────────────────────┘
```

### Main Components

- **Frontend:** Provides business onboarding, document upload, progress updates and assessment results.
- **Backend:** Handles application APIs, validation, processing and communication with the frontend.
- **Supervisor:** Coordinates the seven-agent assessment workflow.
- **AI agents:** Analyse business identity, documents, conversations, financial signals, reconciliation, compliance and report generation.
- **Database:** Stores application and session-related information.
- **External services:** Support language-model reasoning and business-location verification.

---

## 🛠️ Technology Stack

### Backend

| Technology               | Usage                                                                    |
| ------------------------ | ------------------------------------------------------------------------ |
| **FastAPI**              | Asynchronous Python backend and REST APIs.                               |
| **Uvicorn**              | ASGI server used to serve the FastAPI application.                       |
| **Pydantic**             | Request validation and data modelling.                                   |
| **SlowAPI**              | API rate limiting.                                                       |
| **WebSockets**           | Real-time agent progress and log streaming.                              |
| **Groq – LLaMA 3.1 70B** | Language-model support for WhatsApp parsing and report/reasoning agents. |

### Frontend

| Technology                   | Usage                                      |
| ---------------------------- | ------------------------------------------ |
| **Next.js 15 with React 18** | Frontend application framework.            |
| **TypeScript**               | Frontend programming language.             |
| **Tailwind CSS**             | Styling and responsive UI.                 |
| **Zustand**                  | Frontend state management.                 |
| **TanStack React Query**     | Data fetching and server-state management. |
| **Framer Motion**            | UI animations.                             |
| **Recharts**                 | Charts and data visualisation.             |
| **React Hook Form**          | Form management.                           |
| **Zod**                      | Form and data validation.                  |
| **reconnecting-websocket**   | WebSocket connection handling.             |

### Machine Learning and Data Processing

| Technology       | Usage                                         |
| ---------------- | --------------------------------------------- |
| **XGBoost**      | Credit Warmth Score prediction.               |
| **scikit-learn** | Machine-learning utilities and model support. |
| **SHAP**         | Explainability of model predictions.          |
| **Pandas**       | Processing Khata/ledger data.                 |

### OCR and Document Processing

| Technology    | Usage                                                             |
| ------------- | ----------------------------------------------------------------- |
| **PaddleOCR** | Primary OCR engine for extracting text from documents and images. |
| **EasyOCR**   | Hindi and English OCR fallback.                                   |
| **OpenCV**    | Image processing.                                                 |
| **Pillow**    | Image handling and processing.                                    |
| **ReportLab** | PDF credit memo generation.                                       |
| **qrcode**    | QR code generation for reports.                                   |
| **SHA-256**   | Hashing for uploaded artefacts and generated reports.             |

### Database and Storage

| Technology             | Usage                                            |
| ---------------------- | ------------------------------------------------ |
| **SQLite**             | Application database.                            |
| **aiosqlite**          | Asynchronous access to SQLite.                   |
| **Local disk storage** | Stores uploaded artefacts and generated reports. |

Uploads are stored under the session/artifact data directory, while generated reports are stored separately in the reports directory. The project configuration describes a 20 MB upload limit; confirm the active backend limit if it has changed.

### APIs, Maps and Deployment

| Technology                 | Usage                                      |
| -------------------------- | ------------------------------------------ |
| **Google Maps Places API** | Business location and place verification.  |
| **Docker Compose**         | Container-based application deployment.    |
| **cryptography**           | Encryption support, including AES-256-GCM. |

---

## 📁 Project Structure

The repository is organised into frontend and backend components.

```text
shadow-credit/
├── backend/
│   ├── agents/              # AI agents and Supervisor
│   ├── api/                 # REST API endpoints
│   ├── core/                # Security, events and AI client
│   ├── db/                  # Database schema and queries
│   │   └── schema.sql
│   ├── config.py            # Backend configuration
│   └── main.py              # FastAPI application
│
├── frontend/
│   ├── app/                 # Next.js pages and routes
│   ├── components/          # Reusable React components
│   └── hooks/               # Custom React hooks
│
├── data/
│   ├── artifacts/           # Uploaded session artefacts
│   └── reports/             # Generated reports
│
├── docker-compose.yml       # Docker Compose configuration
└── README.md
```

This is a high-level overview. Individual files and folders may vary depending on the current repository version.

---

## 🚀 Quick Start

### Prerequisites

Install the following before running the project:

- Python 3.11+
- Node.js 18+
- npm
- Docker
- Docker Compose
- Google Maps API key with the required Places API access
- Groq API key

### 1. Clone the Repository

```bash
git clone https://github.com/kashish1720/shadow-credit.git
cd shadow-credit
```

### 2. Configure Backend Environment

Create the backend environment file:

```bash
cp backend/.env.example backend/.env
```

Add the required configuration values to `backend/.env`. Use the exact environment-variable names expected by the project.

Example values:

```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
MASTER_ENCRYPTION_KEY=your_64_character_hex_key
```

Generate a 32-byte encryption key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into the environment configuration.

**Important:** Never commit `.env` files or real API keys to GitHub.

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

Open another terminal:

```bash
cd frontend
npm install
```

### 5. Start the Application

Start the backend:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Start the frontend in a separate terminal:

```bash
cd frontend
npm run dev
```

### 6. Open the Application

Open the frontend in your browser:

```text
http://localhost:3000/apply
```

The backend API runs on:

```text
http://localhost:8000
```

### Docker Deployment

Docker Compose is used for container-based deployment. Make sure Docker Desktop or Docker Engine and the Compose plugin are installed and running.

From the project root, run:

```bash
docker compose up --build
```

To stop the containers:

```bash
docker compose down
```

---

## ⚙️ Environment Configuration and Security

The backend uses environment-based configuration for service credentials and security settings.

At minimum, configure the API keys and encryption key required by the application. Refer to `backend/.env.example` and the backend configuration code for the exact variable names.

### Important repository security fix

Before publishing the repository:

- Set hardcoded default values for `GROQ_API_KEY`, `GOOGLE_MAPS_API_KEY` and `ANTHROPIC_API_KEY` in `backend/config.py` to empty strings (`""`).
- Load credentials from environment variables instead of source-code defaults.
- If any committed key was ever a real credential, revoke or rotate it.
- Ensure `.env` is included in `.gitignore`.
- Keep only safe placeholder values in `.env.example`.

Do not publish API keys, encryption keys, passwords or other secrets in source code or documentation.

---

## 📡 API Endpoints

The backend exposes REST APIs for session management and document ingestion, along with a WebSocket endpoint for real-time updates.

### Session Management

| Method   | Endpoint                        | Description                                           |
| -------- | ------------------------------- | ----------------------------------------------------- |
| `POST`   | `/api/v1/sessions`              | Creates a new session and records consent.            |
| `GET`    | `/api/v1/sessions/{id}`         | Fetches session status.                               |
| `POST`   | `/api/v1/sessions/{id}/analyze` | Starts the assessment pipeline.                       |
| `POST`   | `/api/v1/sessions/{id}/clarify` | Submits an answer to a clarification question.        |
| `POST`   | `/api/v1/sessions/{id}/export`  | Exports or downloads the PDF report.                  |
| `DELETE` | `/api/v1/sessions/{id}`         | Deletes session information through the erasure flow. |

### Document Ingestion

| Method | Endpoint                       | Description                          |
| ------ | ------------------------------ | ------------------------------------ |
| `POST` | `/api/v1/ingest/whatsapp/{id}` | Uploads an exported WhatsApp chat.   |
| `POST` | `/api/v1/ingest/upi/{id}`      | Uploads UPI transaction screenshots. |
| `POST` | `/api/v1/ingest/bill/{id}`     | Uploads a utility bill.              |
| `POST` | `/api/v1/ingest/khata/{id}`    | Uploads a ledger/Khata image.        |

Address proof and electricity bills are included in the document sources described by the project. Confirm their exact endpoint mapping and accepted file formats in the current backend before documenting a separate endpoint for each.

### Real-time Events

| Protocol    | Endpoint           | Description                                     |
| ----------- | ------------------ | ----------------------------------------------- |
| `WebSocket` | `/ws/{session_id}` | Streams live agent progress and session events. |

---

## 🔒 Privacy and Consent

Shadow Credit processes business-related information that may contain personal or financial data. The application includes a consent step before starting the assessment.

The project describes privacy and security features including:

- Consent tracking before document analysis.
- AES-256-GCM encryption for sensitive information.
- Session deletion functionality intended to support the right to erasure.
- Audit logging and database-level protections.
- SHA-256 hashing for uploaded artefacts and generated reports.

Users should upload only documents they are authorised to share. The actual data retention, access control, encryption configuration and deletion behaviour should be reviewed in the deployed implementation. Mention of the DPDP Act, 2023, or a consent screen alone does not establish legal compliance.

---

## 💰 Cost Considerations

The original project documentation lists the following indicative service costs:

| Service              | Cost information                                                                          |
| -------------------- | ----------------------------------------------------------------------------------------- |
| Groq API             | Free tier availability depends on current provider limits and usage.                      |
| EasyOCR              | Open-source and runs locally.                                                             |
| Google Maps Platform | Usage-based pricing; charges depend on API usage, account billing and applicable credits. |

Actual costs may change based on provider pricing, free-tier limits, API usage and deployment environment. Check the providers' current pricing before deployment.

---

## 🔮 Future Scope

Potential improvements include:

- Support for additional Indian languages.
- More business categories and category-specific assessment rules.
- Improved extraction and verification of uploaded financial documents.
- More detailed explanations for credit scores and risk indicators.
- A business dashboard to view and track previous assessments.
- Stronger document retention and deletion controls.
- Additional lender integrations and verified OCEN interoperability.
- Testing and calibration of the scoring model using suitable, consented and representative datasets.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built for Indian MSMEs 🇮🇳**

_Democratizing credit access through AI._

</div>
