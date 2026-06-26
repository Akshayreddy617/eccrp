# 🗳️ ECCRP — India Runs Hackathon Submission

**Track:** Track 01 — The Data & AI Challenge  
**Team:** Akshay Reddy  
**GitHub:** https://github.com/Akshayreddy617/eccrp  
**Hackathon:** INDIA RUNS by Redrob AI × Hack2skill

---

## 🚨 The Problem

India runs 4 elections every year — Parliament, State Assemblies, and hundreds of thousands of local body elections. Yet:

- **73% of candidates** file incomplete Form 26 affidavits (ADR study)
- **Thousands of election petitions** are filed annually for disclosure failures
- **Candidates are disqualified** for crossing expenditure limits they didn't know existed
- **MCC violations** happen because campaigns don't know which activities are prohibited
- **India's 1.4 billion people** have zero AI tools built for their electoral reality

The Constitution, RPA 1950/1951, ECI Guidelines, and Supreme Court judgments exist — but they are scattered across hundreds of PDFs, inaccessible to the candidate in Anantapur or the consultant in Pune.

**No platform converts Indian election law into real-time compliance action.**

---

## 💡 Our Solution: ECCRP

**Election Compliance & Candidate Readiness Platform** is a production-grade AI SaaS that converts Indian election law into 15 actionable compliance modules — covering every election type from Lok Sabha to Gram Panchayat.

### What makes it different

| Old Way | ECCRP Way |
|---------|-----------|
| Lawyer reads 300-page RPA manually | AI checks eligibility in seconds |
| Candidate files incomplete Form 26 | AI extracts & validates affidavit fields |
| Campaign spends blindly, gets disqualified | Real-time expenditure limit dashboard |
| Activity violates MCC unknowingly | Instant AI MCC violation detection |
| No way to know SC judgment impact | Scenario → Law → Judgment → Action chain |

---

## 🤖 AI Architecture

```
User Query (natural language)
        │
        ▼
  Query Rewriting (GPT-4o, temp=0.1)
        │
        ▼
  Embedding Generation (text-embedding-3-small)
        │
        ▼
  Hybrid Search — OpenSearch KNN + BM25
  ┌─────────────────────────────────────┐
  │  eccrp_laws      (Constitution +    │
  │                   RPA 1950/1951)    │
  │  eccrp_judgments (6 landmark SC     │
  │                   judgments)        │
  │  eccrp_knowledge (ECI Circulars +   │
  │                   MCC Guidelines)   │
  └─────────────────────────────────────┘
        │
        ▼
  Context Assembly (Top-10 docs)
        │
        ▼
  GPT-4o Response with:
  ✓ Legal citations (Article / Section)
  ✓ Judgment references
  ✓ Confidence score (0–1)
  ✓ Recommended action
  ✓ Mandatory disclaimer
```

---

## 📦 15 Compliance Modules

| Module | Name | What It Does |
|--------|------|-------------|
| 1 | Election Selection Engine | Auto-loads all applicable laws for any election type |
| 2 | Eligibility Assessment | 10-check engine: citizenship, age, convictions, office of profit |
| 3 | Nomination Readiness | Document checklist with weighted scoring |
| 4 | Affidavit Validator | AI extracts Form 26 fields, flags missing/inconsistent data |
| 5 | Compliance Risk Engine | 5-dimension risk radar: eligibility, disclosure, legal, expenditure, MCC |
| 6 | Election Timeline Planner | All dates + deadlines + calendar (.ics) export |
| 7 | Expenditure Tracker | Category-wise dashboard, alerts at 70/85/95% of ECI limit |
| 8 | MCC Checker | 50+ keyword rules + LLM — flags violations with ECI citations |
| 9 | Knowledge Repository | Constitution, RPA Acts, ECI Circulars — full-text searchable |
| 10 | SC Judgment Library | 6 landmark judgments with ratio decidendi |
| 11 | Judgment Impact Engine | Scenario → Law → Judgment → Compliance chain |
| 12 | AI Governance Assistant | RAG-powered natural language election law Q&A |
| 13 | Knowledge Graph | D3.js visualization of legal provision relationships |
| 14 | Consultant Dashboard | Multi-candidate compliance tracking for election consultants |
| 15 | Public Transparency Portal | Open candidate disclosure search (no login required) |

---

## ⚖️ Legal Coverage

**Constitution of India**
- Articles 84, 102 — Parliament qualifications & disqualifications
- Articles 173, 191 — State Legislature
- Articles 243F, 243V — Panchayats & Municipalities

**Representation of the People Acts**
- Section 8(3) + Lily Thomas (2013) — Instant disqualification on conviction ≥2 years
- Section 33A + ADR (2002) — Mandatory Form 26 affidavit disclosure
- Section 10A — 3-year disqualification for failing to file expenditure account
- Section 123 — Corrupt practices (bribery, undue influence, hate speech)
- Section 126 — 48-hour campaign silence before polling

**Landmark Supreme Court Judgments Programmatically Mapped**
1. ADR v. Union of India (2002) — voters' right to know
2. Lily Thomas v. Union of India (2013) — immediate disqualification
3. Public Interest Foundation (2019) — party disclosure obligations
4. PUCL v. Union of India (2013) — NOTA right
5. Kuldip Nayar (2006) — Rajya Sabha domicile
6. Indira Gandhi v. Raj Narain (1975) — free & fair elections as basic feature

---

## 🛠️ Tech Stack

```
Backend:        FastAPI (Python 3.12) · SQLAlchemy async · Alembic
Database:       PostgreSQL 16 · Redis · Neo4j (Knowledge Graph)
AI/RAG:         LangChain · OpenAI GPT-4o · text-embedding-3-small
Search:         OpenSearch 2.x (KNN vectors + BM25 hybrid)
Storage:        MinIO (S3-compatible)
Frontend:       Next.js 14 · TypeScript · Tailwind CSS
State:          Zustand · React Query
Charts:         Recharts · D3.js
Infrastructure: Docker Compose · Kubernetes (HPA) · GitHub Actions CI/CD
Monitoring:     Prometheus · Grafana
Security:       JWT + bcrypt · RBAC (7 roles) · Rate limiting · Full audit logs
```

---

## 🧪 Testing

- **60+ unit tests** — eligibility scoring, MCC rules, JWT security, timeline logic
- **API integration tests** — all endpoints tested via httpx AsyncClient
- **Playwright E2E tests** — login, dashboard, eligibility, AI assistant, MCC, public portal
- **CI/CD** — GitHub Actions runs all tests on every push

---

## 🚀 Quick Start (3 minutes)

```bash
git clone https://github.com/Akshayreddy617/eccrp
cd eccrp
cp backend/.env.example backend/.env
# Add your OPENAI_API_KEY to backend/.env
docker-compose up -d

# Seed data
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"email":"admin@eccrp.in","password":"Admin@123"}' -H "Content-Type: application/json" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -X POST http://localhost:8000/api/v1/admin/seed/judgments -H "Authorization: Bearer $TOKEN"
```

**Frontend:** http://localhost:3000  
**API Docs:** http://localhost:8000/api/v1/docs

---

## 📂 Repository Structure

```
eccrp/
├── backend/app/
│   ├── api/v1/endpoints/   # 16 endpoint modules
│   ├── ai/rag/engine.py    # Full RAG pipeline
│   ├── services/           # Eligibility + MCC business logic
│   └── db/models/          # 25 SQLAlchemy models
├── frontend/src/app/       # 15 Next.js page modules
├── docs/                   # TDD, API Reference, User Guide, Deployment
├── infrastructure/         # Docker, Kubernetes, Prometheus, Grafana
└── .github/workflows/      # CI/CD pipeline
```

---

## 📊 Impact

- **Candidates** — Know eligibility before filing, prevent disqualification
- **Consultants** — Manage 50+ candidates from one dashboard
- **Lawyers** — Instant legal research with SC judgment citations
- **Journalists** — Public portal for disclosure transparency
- **Voters** — Access candidate disclosures as mandated by ADR judgment (2002)
- **Scale** — Built for 543 Lok Sabha + 4000+ Assembly + 250,000+ local body constituencies

---

## ⚠️ Disclaimer

ECCRP provides AI-assisted compliance guidance for informational purposes only. It does not constitute legal advice. Consult a qualified election law practitioner for specific legal matters.

---

*Built for Indian Democracy. Powered by AI. Legally Traceable.*  
*INDIA RUNS × Hack2skill — Track 01: Data & AI Challenge*
