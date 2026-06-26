<div align="center">

# 🗳️ ECCRP
## Election Compliance & Candidate Readiness Platform

**AI-powered SaaS that converts Indian election law into actionable compliance workflows**

[![Track](https://img.shields.io/badge/Track-01%20Data%20%26%20AI-FF9933?style=for-the-badge)](https://hack2skill.com/event/india_runs)
[![Hackathon](https://img.shields.io/badge/INDIA%20RUNS-Hack2skill-0A1628?style=for-the-badge)](https://hack2skill.com/event/india_runs)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.12-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs)](https://nextjs.org)
[![OpenAI](https://img.shields.io/badge/GPT--4o-RAG%20Powered-412991?style=for-the-badge&logo=openai)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

---

*India runs 4 elections a year. No AI tool existed to keep candidates compliant — until now.*

**[📖 API Docs](#api) · [🚀 Quick Start](#quick-start) · [📦 15 Modules](#modules) · [⚖️ Legal Coverage](#legal) · [🤖 AI Architecture](#ai)**

</div>

---

## 🚨 The Problem

India's election law is scattered across hundreds of PDFs — Constitution of India, RPA 1950/1951, ECI Circulars, Supreme Court judgments. The consequences of not knowing it are severe:

| Problem | Impact |
|---------|--------|
| 73% of candidates file incomplete Form 26 affidavits | Election petition → disqualification |
| Campaigns cross ECI expenditure limits unknowingly | Section 10A RPA: 3-year ban |
| MCC violations go undetected until ECI notice | Criminal complaint, campaign halt |
| SC judgment changes ignored (Lily Thomas 2013) | Instant disqualification post-conviction |
| No transparency tool for voters | Violates ADR Supreme Court mandate (2002) |

**No platform existed that converts all of this into real-time compliance guidance.**

---

## 💡 The Solution

ECCRP is a **production-grade AI SaaS** with **15 compliance modules** covering every Indian election type — from Lok Sabha to Gram Panchayat.

```
Constitution of India  +  RPA 1950/51  +  ECI Guidelines  +  SC Judgments
                                    │
                          ┌─────────▼──────────┐
                          │   AI/RAG Engine     │
                          │  GPT-4o + OpenSearch│
                          └─────────┬──────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
    ✅ Eligibility             💰 Expenditure            📢 MCC Check
    📋 Affidavit AI            📅 Timeline               ⚖️ Judgment Chain
    🤖 AI Assistant            🌐 Public Portal          📊 Risk Engine
```

---

## 🚀 Quick Start

**Prerequisites:** Docker Desktop, OpenAI API key

```bash
# 1. Clone
git clone https://github.com/Akshayreddy617/eccrp
cd eccrp

# 2. Configure
cp backend/.env.example backend/.env
# → Edit backend/.env, set OPENAI_API_KEY=sk-your-key

# 3. Launch (all services)
docker-compose up -d

# 4. Seed judgment database
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@eccrp.in","password":"Admin@123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/api/v1/admin/seed/judgments \
  -H "Authorization: Bearer $TOKEN"
```

| Service | URL |
|---------|-----|
| 🖥️ Frontend | http://localhost:3000 |
| ⚡ Backend API | http://localhost:8000 |
| 📖 API Docs (Swagger) | http://localhost:8000/api/v1/docs |
| 📊 Grafana Monitoring | http://localhost:3001 |
| 🔍 OpenSearch | http://localhost:9200 |

---

## 📦 15 Compliance Modules {#modules}

| # | Module | Description | Legal Basis |
|---|--------|-------------|-------------|
| 1 | **Election Selection Engine** | Auto-loads constitutional provisions, laws, SEC rules & judgments for any election | Constitution + RPA |
| 2 | **Eligibility Assessment** | 10-check engine: citizenship, age, convictions, office of profit, insolvency | Art. 84/102/173/191 |
| 3 | **Nomination Readiness** | Weighted document checklist — Form 26, electoral roll, assets, photos | Section 33 RPA 1951 |
| 4 | **Affidavit Validator** | AI extracts Form 26 fields, flags missing data & legal risks | Section 33A + ADR 2002 |
| 5 | **Compliance Risk Engine** | 5-dimension risk radar: eligibility, disclosure, legal, expenditure, MCC | Aggregate |
| 6 | **Election Timeline Planner** | All dates + compliance deadlines + `.ics` calendar export | Section 78 RPA 1951 |
| 7 | **Expenditure Tracker** | Category dashboard, risk alerts at 70/85/95% of ECI limit | Section 77/78/10A |
| 8 | **MCC Checker** | 50+ keyword rules + LLM — detects violations with ECI citations | ECI MCC Guidelines |
| 9 | **Knowledge Repository** | Full-text searchable Constitution, RPA Acts, ECI Circulars | All sources |
| 10 | **SC Judgment Library** | 6 landmark judgments with ratio decidendi | Supreme Court |
| 11 | **Judgment Impact Engine** | Scenario → Law → SC Judgment → Compliance chain | All judgments |
| 12 | **AI Governance Assistant** | RAG-powered natural language election law Q&A | Legal corpus |
| 13 | **Knowledge Graph** | D3.js visualization of legal provision relationships | Neo4j |
| 14 | **Consultant Dashboard** | Multi-candidate compliance tracking | All modules |
| 15 | **Public Transparency Portal** | Open candidate disclosure search (no login required) | ADR 2002 |

---

## 🤖 AI / RAG Architecture {#ai}

```
User Query: "Can I contest if a criminal case is pending?"
        │
        ▼ Query Rewriting (GPT-4o, temperature=0.1)
        │
        ▼ Embedding Generation (text-embedding-3-small, 1536 dim)
        │
        ▼ Hybrid Search — OpenSearch KNN + BM25
          ┌─────────────────────────────────────────┐
          │  eccrp_laws      → Constitution + RPA   │
          │  eccrp_judgments → 6 SC Judgments        │
          │  eccrp_knowledge → ECI Circulars + MCC  │
          └─────────────────────────────────────────┘
        │
        ▼ Context Assembly (Top-10 docs, similarity ≥ 0.7)
        │
        ▼ GPT-4o Response
          ✓ Direct answer in plain English
          ✓ Legal citation (Article / Section number)
          ✓ SC Judgment reference (case name + citation)
          ✓ Confidence score (0.0 – 1.0)
          ✓ Recommended action
          ✓ Mandatory legal disclaimer
```

**Example Q&A:**
> **Q:** Can I contest elections if a criminal case is pending against me?
>
> **A:** Yes, pending cases (not convicted) do not bar candidacy. However, ALL pending cases MUST be disclosed in Form 26. Failure = grounds for election petition.
> **Legal Basis:** Section 33A RPA 1951 | **Judgment:** ADR v. Union of India (2002) 5 SCC 294 | **Confidence:** 91%

---

## ⚖️ Legal Coverage {#legal}

### Constitutional Provisions
- **Article 84** — Qualifications for Parliament (citizenship, age ≥25 LS / ≥30 RS, electoral roll)
- **Article 102** — Disqualifications for Parliament (office of profit, insolvency, conviction)
- **Article 173** — Qualifications for State Legislature
- **Article 191** — Disqualifications for State Legislature
- **Article 243F** — Panchayat member disqualifications
- **Article 243V** — Municipality member disqualifications

### RPA 1951 — Key Sections Implemented
| Section | Description | Consequence |
|---------|-------------|-------------|
| 8(3) | Conviction ≥ 2 years | Instant disqualification (Lily Thomas 2013) |
| 9A | Government contracts | Disqualification |
| 10A | Fail to file expenditure account | 3-year disqualification |
| 33A | Mandatory affidavit disclosure | Election petition if violated |
| 77/78 | Election expenditure accounts | Must file within 30 days of result |
| 123 | Corrupt practices (bribery, hate speech) | Voided election + criminal charges |
| 126 | Campaign silence period | 48 hours before polling |

### Landmark Supreme Court Judgments — Programmatically Mapped
| Case | Year | Impact |
|------|------|--------|
| ADR v. Union of India | 2002 | Mandatory Form 26 disclosure; voters' right to know |
| Lily Thomas v. Union of India | 2013 | Instant disqualification on conviction ≥ 2 years |
| Public Interest Foundation | 2019 | Parties must disclose reasons for fielding criminal candidates |
| PUCL v. Union of India | 2013 | NOTA is a fundamental right under Art. 19(1)(a) |
| Kuldip Nayar v. UoI | 2006 | No domicile requirement for Rajya Sabha |
| Indira Gandhi v. Raj Narain | 1975 | Free & fair elections = basic feature of Constitution |

---

## 🛠️ Tech Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│  Frontend         Next.js 14 · TypeScript · Tailwind CSS            │
│                   Zustand · React Query · Recharts · D3.js           │
├─────────────────────────────────────────────────────────────────────┤
│  Backend          FastAPI (Python 3.12) · SQLAlchemy async           │
│                   Alembic · Pydantic v2 · JWT + RBAC (7 roles)      │
├─────────────────────────────────────────────────────────────────────┤
│  AI / RAG         LangChain · OpenAI GPT-4o · text-embedding-3-small│
│                   LangGraph · Confidence Scoring · Citation Engine   │
├─────────────────────────────────────────────────────────────────────┤
│  Data             PostgreSQL 16 · Redis · Neo4j · MinIO (S3)        │
├─────────────────────────────────────────────────────────────────────┤
│  Search           OpenSearch 2.x — KNN vectors + BM25 hybrid        │
│                   3 indices: eccrp_laws, eccrp_judgments, eccrp_knowledge │
├─────────────────────────────────────────────────────────────────────┤
│  Infrastructure   Docker Compose · Kubernetes (HPA 2–10 pods)       │
│                   GitHub Actions CI/CD · Prometheus · Grafana        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing

```bash
# Unit tests (60+ tests)
cd backend && pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (Playwright)
cd frontend && npx playwright test

# Type checking
cd frontend && npm run type-check
```

**Coverage:**
- ✅ Eligibility scoring logic (all 10 checks, edge cases)
- ✅ MCC keyword detection (50+ rules)
- ✅ JWT security (create, decode, expiry, tampering)
- ✅ Timeline deadline calculation
- ✅ Expenditure risk thresholds
- ✅ All API endpoints (auth, candidates, elections, eligibility, MCC, judgments, public portal)
- ✅ E2E: login, dashboard, eligibility check, AI assistant, MCC checker, public portal

---

## 📁 Project Structure

```
eccrp/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # 16 endpoint modules
│   │   ├── ai/rag/engine.py     # Full RAG pipeline
│   │   ├── core/                # Config, JWT, middleware, logging
│   │   ├── db/models/           # 25 SQLAlchemy ORM models
│   │   ├── services/            # Eligibility + MCC business logic
│   │   └── db/migrations/       # Alembic async migrations
│   └── tests/
│       ├── unit/                # 60+ unit tests
│       ├── integration/         # API contract tests
│       └── e2e/                 # Playwright browser tests
├── frontend/
│   └── src/
│       ├── app/                 # 15 Next.js 14 page modules
│       ├── components/ui/       # Reusable component library
│       ├── lib/                 # API client + utility helpers
│       └── store/               # Zustand auth store
├── infrastructure/
│   ├── docker/                  # Dockerfiles (backend + frontend)
│   ├── k8s/base/                # Kubernetes manifests + HPA
│   └── monitoring/              # Prometheus + Grafana config
├── docs/
│   ├── TECHNICAL_DESIGN.md      # System architecture + DB design
│   ├── API_REFERENCE.md         # Full API reference
│   ├── USER_GUIDE.md            # Module-by-module user guide
│   └── DEPLOYMENT_GUIDE.md      # Local + Kubernetes deployment
├── docker-compose.yml           # Full stack: 10 services
├── SUBMISSION.md                # Hackathon submission details
└── .github/workflows/ci-cd.yml  # CI/CD pipeline
```

---

## 👥 Target Users

| User | What They Get |
|------|---------------|
| 🗳️ **Candidates** | Eligibility check, affidavit validation, expenditure tracking, MCC compliance |
| 🏢 **Consultants** | Multi-candidate dashboard, aggregate risk view, pending action alerts |
| ⚖️ **Lawyers** | AI legal research with SC judgment citations, natural language Q&A |
| 📰 **Journalists** | Public transparency portal, candidate disclosure search |
| 🏛️ **Political Parties** | Pre-screening candidates for eligibility risks |
| 🌐 **Voters** | Open portal — no login — to search any candidate's disclosures |

---

## 📊 Scale

- 🗳️ **543** Lok Sabha constituencies
- 🏛️ **4,000+** State Assembly seats
- 🏘️ **250,000+** Panchayat / Municipal wards
- 👥 **1.4 billion** voters with right to access candidate disclosures
- 🌐 **9 election types** fully supported

---

## 📖 API Reference {#api}

Full Swagger UI available at: `http://localhost:8000/api/v1/docs`

Key endpoints:

```bash
# Eligibility Check
POST /api/v1/eligibility/check
{ "candidate_id": "uuid", "election_type": "lok_sabha" }

# AI Assistant
POST /api/v1/ai/query
{ "query": "Can I contest if a criminal case is pending?" }

# MCC Check
POST /api/v1/mcc/check
{ "election_id": "uuid", "activity_description": "Distributing sarees to voters" }

# Expenditure Dashboard
GET /api/v1/expenditure/dashboard/{candidate_id}/{election_id}

# SC Judgment Impact
GET /api/v1/judgments/impact/scenario?scenario=pending+criminal+case

# Public Portal (no auth)
GET /api/v1/public/candidates?name=Ravi+Kumar
```

---

## ⚠️ Legal Disclaimer

ECCRP provides AI-assisted compliance guidance based on publicly available Indian election law. All outputs are for **informational purposes only** and do **not constitute legal advice**. Always consult a qualified election law practitioner for specific legal matters.

---

## 🏆 Hackathon

**INDIA RUNS × Hack2skill**  
Track 01 — The Data & AI Challenge  
[View Submission](https://hack2skill.com/event/india_runs)

---

<div align="center">

**Built for Indian Democracy. Powered by AI. Legally Traceable.**

*© 2024 Akshay Reddy · MIT License*

</div>
