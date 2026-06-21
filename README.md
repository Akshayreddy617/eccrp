# 🗳️ ECCRP — Election Compliance & Candidate Readiness Platform

**India's premier AI-powered election compliance SaaS platform**

ECCRP converts the Constitution of India, RPA 1950/1951, ECI Guidelines, and Supreme Court judgments into actionable compliance workflows for candidates, political parties, lawyers, consultants, journalists, and governance researchers.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         ECCRP Platform                          │
├─────────────┬──────────────┬──────────────┬────────────────────┤
│   Next.js   │   FastAPI    │  PostgreSQL  │    OpenSearch      │
│  Frontend   │   Backend    │   Database   │   Vector Search    │
├─────────────┼──────────────┼──────────────┼────────────────────┤
│   React     │  LangChain   │    Redis     │      Neo4j         │
│  Recharts   │  RAG Engine  │    Cache     │  Knowledge Graph   │
├─────────────┴──────────────┴──────────────┴────────────────────┤
│              Kubernetes / Docker Compose                        │
│         Prometheus + Grafana Monitoring                         │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Feature Modules

| # | Module | Description |
|---|--------|-------------|
| 1 | Election Selection Engine | Auto-loads constitutional provisions for any election |
| 2 | Eligibility Assessment Engine | 10+ checks: citizenship, age, convictions, office of profit |
| 3 | Nomination Readiness Engine | Document checklist and readiness scoring |
| 4 | Affidavit Validator | AI-powered Form 26 extraction and validation |
| 5 | Compliance Risk Engine | 5-dimension risk aggregation with radar chart |
| 6 | Election Timeline Planner | Dates, deadlines, calendar export (.ics) |
| 7 | Expenditure Tracker | Category tracking, limit monitoring, risk alerts |
| 8 | MCC Checker | AI + rule-based Model Code of Conduct violation detection |
| 9 | Knowledge Repository | Constitution, RPA Acts, ECI Circulars, Rules |
| 10 | SC Judgment Library | 6+ landmark judgments with full ratio decidendi |
| 11 | Judgment Impact Engine | Scenario → Law → Judgment → Compliance chain |
| 12 | AI Governance Assistant | RAG-powered election law Q&A |
| 13 | Knowledge Graph | D3.js visualization of legal provision relationships |
| 14 | Consultant Dashboard | Multi-candidate compliance overview |
| 15 | Public Transparency Portal | Unauthenticated candidate disclosure search |

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop 4.x
- Docker Compose v2.x
- OpenAI API key (for AI features)

### 1. Clone and configure

```bash
git clone https://github.com/your-org/eccrp.git
cd eccrp

# Configure backend
cp backend/.env.example backend/.env
# Edit backend/.env — at minimum set OPENAI_API_KEY
```

### 2. Start all services

```bash
docker-compose up -d
```

Services started:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **OpenSearch**: http://localhost:9200
- **Neo4j Browser**: http://localhost:7474
- **MinIO Console**: http://localhost:9001
- **Grafana**: http://localhost:3001

### 3. Seed initial data

```bash
# Register admin user via API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@eccrp.in","password":"Admin@123","full_name":"Admin User","role":"super_admin"}'

# Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@eccrp.in","password":"Admin@123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Seed landmark judgments
curl -X POST http://localhost:8000/api/v1/admin/seed/judgments \
  -H "Authorization: Bearer $TOKEN"

# Initialize OpenSearch indices (AI features)
curl -X POST http://localhost:8000/api/v1/admin/ingest/legal-corpus \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🛠️ Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

### Run Tests

```bash
# Backend unit tests
cd backend
pytest tests/unit/ -v --tb=short

# Backend integration tests (requires running DB)
pytest tests/integration/ -v

# Frontend type check
cd frontend
npm run type-check
```

---

## 🔐 Authentication & RBAC

| Role | Access |
|------|--------|
| `super_admin` | Full platform access + admin panel |
| `admin` | All features + user management |
| `consultant` | All candidates + multi-candidate dashboard |
| `candidate` | Own profile only |
| `lawyer` | Read-only + AI assistant |
| `journalist` | Public portal + knowledge base |
| `researcher` | Knowledge base + judgments |
| `public` | Public portal only (no auth required) |

---

## ⚖️ Supported Election Types

- **Parliament**: Lok Sabha, Rajya Sabha
- **State Legislature**: Legislative Assembly, Legislative Council
- **Local Bodies**: Gram Panchayat, Mandal Parishad, Zilla Parishad
- **Urban Bodies**: Municipality, Municipal Corporation

---

## 📚 Legal Coverage

### Constitutional Provisions
- Articles 84, 102 (Parliament qualifications/disqualifications)
- Articles 173, 191 (State Legislature)
- Articles 243F, 243V (Local bodies)

### Representation of the People Acts
- Section 8, 8A — Conviction and corrupt practices disqualification
- Section 9, 9A — Insolvency and government contracts
- Section 10A — Expenditure account failure (3-year disqualification)
- Section 33A — Mandatory affidavit disclosure
- Section 77, 78 — Expenditure accounts
- Section 123 — Corrupt practices
- Section 126 — 48-hour campaign silence

### Landmark Judgments
- **ADR v. Union of India (2002)** — Mandatory disclosure
- **Lily Thomas v. Union of India (2013)** — Instant disqualification on conviction
- **Public Interest Foundation (2019)** — Party disclosure obligations
- **PUCL v. Union of India (2013)** — NOTA right
- **Kuldip Nayar (2006)** — Rajya Sabha domicile
- **Indira Gandhi v. Raj Narain (1975)** — Free & fair elections as basic feature

---

## 🤖 AI/RAG Architecture

```
User Query
    │
    ▼
Query Rewriting (LLM)
    │
    ▼
Embedding Generation (text-embedding-3-small)
    │
    ▼
Hybrid Search (OpenSearch: semantic + keyword)
    │
    ├── eccrp_laws index
    ├── eccrp_judgments index
    └── eccrp_knowledge index
    │
    ▼
Context Assembly (Top-K retrieved docs)
    │
    ▼
Prompt Construction (System + Legal Context + Query)
    │
    ▼
LLM Generation (GPT-4o)
    │
    ▼
Citation Extraction + Confidence Scoring
    │
    ▼
Structured Response (Answer + Citations + Judgments + Disclaimer)
```

---

## 📊 Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/eccrp_grafana)
- Key metrics: API latency, DB connections, AI query latency, error rates

---

## 🚢 Production Deployment

```bash
# Build images
docker build -t eccrp-backend:latest -f infrastructure/docker/Dockerfile.backend backend/
docker build -t eccrp-frontend:latest -f infrastructure/docker/Dockerfile.frontend frontend/

# Kubernetes
kubectl apply -f infrastructure/k8s/base/deployment.yaml

# Scale
kubectl scale deployment eccrp-backend --replicas=5 -n eccrp
```

---

## 📁 Project Structure

```
eccrp/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/     # 16 API modules
│   │   ├── ai/rag/               # RAG engine
│   │   ├── core/                 # Config, security, middleware
│   │   ├── db/models/            # SQLAlchemy ORM
│   │   └── services/             # Business logic
│   └── tests/
│       ├── unit/                 # Service-level unit tests
│       └── integration/          # API integration tests
├── frontend/
│   └── src/
│       ├── app/                  # Next.js 14 pages (15 modules)
│       ├── components/ui/        # Reusable components
│       ├── lib/                  # API client, utilities
│       └── store/                # Zustand state management
├── infrastructure/
│   ├── docker/                   # Dockerfiles
│   ├── k8s/                      # Kubernetes manifests
│   ├── monitoring/               # Prometheus + Grafana
│   └── terraform/                # IaC
├── docs/                         # Documentation
├── docker-compose.yml
└── .github/workflows/ci-cd.yml
```

---

## ⚠️ Legal Disclaimer

ECCRP provides AI-assisted compliance guidance based on Indian election law. All outputs are for **informational purposes only** and do **not constitute legal advice**. Always consult a qualified election law practitioner for specific legal matters.

---

## 📄 License

MIT License — See LICENSE file for details.

**Built for Indian Democracy. Powered by AI. Legally Traceable.**
