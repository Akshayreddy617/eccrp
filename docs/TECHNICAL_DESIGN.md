# ECCRP Technical Design Document
**Version**: 1.0.0 | **Date**: 2024 | **Status**: Production Ready

---

## 1. System Architecture

### 1.1 High-Level Architecture

The ECCRP platform follows a microservices-ready monolith architecture with clear domain boundaries, designed for horizontal scaling on Kubernetes.

```
                        ┌──────────────────┐
                        │   Cloudflare CDN  │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │   Nginx Ingress   │
                        └────┬────────┬────┘
                             │        │
               ┌─────────────▼──┐  ┌──▼──────────────┐
               │  Next.js 14    │  │  FastAPI Backend  │
               │  Frontend      │  │  (3+ replicas)    │
               │  (2 replicas)  │  │                   │
               └────────────────┘  └──┬────┬────┬─────┘
                                      │    │    │
                    ┌─────────────────┘    │    └──────────────┐
                    │                      │                   │
          ┌─────────▼──────┐    ┌──────────▼──────┐  ┌───────▼──────┐
          │  PostgreSQL 16  │    │  OpenSearch 2.x  │  │   Neo4j 5.x  │
          │  (Primary DB)   │    │  (Vector Search) │  │  (Graph DB)  │
          └────────────────┘    └─────────────────┘  └──────────────┘
                    │
          ┌─────────▼──────┐    ┌─────────────────┐  ┌──────────────┐
          │   Redis 7.x     │    │   MinIO          │  │  Celery      │
          │  (Cache+Queue)  │    │  (File Storage)  │  │  (Workers)   │
          └────────────────┘    └─────────────────┘  └──────────────┘
```

### 1.2 Technology Stack Rationale

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend Framework | FastAPI + Python 3.12 | Async-native, auto-generated OpenAPI, type safety |
| Frontend | Next.js 14 + TypeScript | SSR/SSG, App Router, excellent DX |
| Primary DB | PostgreSQL 16 + asyncpg | JSONB for flexible legal data, ACID compliance |
| Search | OpenSearch 2.x | KNN vector search + full-text, open source |
| Cache | Redis 7.x | Session store, rate limiting, Celery broker |
| Graph DB | Neo4j 5.x | Natural fit for legal provision relationship mapping |
| Object Store | MinIO | S3-compatible, self-hosted, GDPR-friendly |
| AI/LLM | LangChain + OpenAI GPT-4o | Production-grade RAG, hallucination prevention |
| ORM | SQLAlchemy 2.x async | Async sessions, migration support |
| Migrations | Alembic | Version-controlled schema changes |
| Styling | Tailwind CSS + Shadcn | Design system, accessible components |
| State | Zustand + React Query | Lightweight global state, server state caching |

---

## 2. Database Design

### 2.1 Entity Relationship Overview

```
States ──< Districts ──< Constituencies
                                │
                         Elections (type, year)
                                │
                    ElectionParticipations
                         │              │
                    Candidates        Expenditures
                         │
                ┌────────┼────────┐
                │        │        │
          Eligibility  Affidavit  NominationDocs
          Checks                  
                │
          RiskAssessments
                
MCCChecks ──> Elections
          
LegalRules ──< JudgmentMappings ──> Judgments
          
KnowledgeGraphNodes ──< KnowledgeGraphEdges
          
Users ──< Candidates
      ──< AuditLogs
      ──< Notifications
      ──< RefreshTokens
      ──< AIQueryLogs
```

### 2.2 Key Design Decisions

1. **JSONB extensively used** for legal provisions, criminal case details, risk factors — allows flexible schema evolution without migrations for semi-structured legal data.

2. **UUID primary keys** throughout — enables distributed ID generation, avoids sequential enumeration attacks.

3. **Soft deletes** via `is_active` flags — preserves audit trail, meets legal data retention requirements.

4. **is_latest flag** on EligibilityCheck, RiskAssessment — efficient retrieval of current state without complex subqueries.

5. **Separate KnowledgeGraphNode/Edge tables** mirror Neo4j data for SQL-based audit and reporting while Neo4j handles graph traversals.

### 2.3 Indexing Strategy

```sql
-- High-frequency lookup indexes
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_candidates_user_id ON candidates(user_id);
CREATE INDEX ix_eligibility_checks_candidate_latest ON eligibility_checks(candidate_id, is_latest);
CREATE INDEX ix_expenditures_candidate_election ON expenditures(candidate_id, election_id);
CREATE INDEX ix_audit_logs_created ON audit_logs(created_at);
CREATE INDEX ix_constituency_state_type ON constituencies(state_id, election_type);
```

---

## 3. API Design

### 3.1 API Versioning
All endpoints are prefixed with `/api/v1/`. Breaking changes increment the version.

### 3.2 Authentication Flow
```
POST /api/v1/auth/login
  → Returns access_token (JWT, 60min) + refresh_token (64-byte random, 30 days)

POST /api/v1/auth/refresh
  → Token rotation: old refresh token revoked, new pair issued

POST /api/v1/auth/logout
  → Revokes refresh token server-side
```

### 3.3 Standard Response Format
```json
// Success
{ "id": "uuid", "field": "value", "created_at": "ISO8601" }

// Error
{ "detail": "Human-readable error message" }

// Paginated
{ "items": [...], "total": 100, "page": 1, "page_size": 20, "total_pages": 5 }
```

### 3.4 Key API Endpoints

| Method | Endpoint | Module | Description |
|--------|----------|--------|-------------|
| POST | `/auth/register` | Auth | Register new user |
| POST | `/auth/login` | Auth | Login + get JWT |
| POST | `/elections/select` | M1 | Load applicable provisions |
| POST | `/eligibility/check` | M2 | Run eligibility assessment |
| GET | `/eligibility/candidate/{id}/latest` | M2 | Latest check result |
| POST | `/nomination/upload/{c}/{e}` | M3 | Upload nomination doc |
| GET | `/nomination/{c}/{e}` | M3 | Readiness score |
| POST | `/affidavit/upload/{c}/{e}` | M4 | Validate Form 26 |
| POST | `/compliance/assess/{id}` | M5 | Generate risk report |
| GET | `/timeline/{election_id}` | M6 | Timeline + deadlines |
| POST | `/expenditure/` | M7 | Add expenditure entry |
| GET | `/expenditure/dashboard/{c}/{e}` | M7 | Dashboard |
| POST | `/mcc/check` | M8 | MCC violation check |
| POST | `/knowledge/search` | M9 | Search legal corpus |
| GET | `/judgments/landmarks` | M10 | Landmark judgments |
| GET | `/judgments/impact/scenario` | M11 | Impact chain |
| POST | `/ai/query` | M12 | AI governance question |
| GET | `/graph/visualization/full` | M13 | Graph data |
| GET | `/dashboard/consultant` | M14 | Consultant view |
| GET | `/public/candidates` | M15 | Public search |

---

## 4. AI/RAG Architecture

### 4.1 Document Ingestion Pipeline
```
Legal PDF/Text
      │
      ▼
Text Extraction (PyMuPDF/docx2txt)
      │
      ▼
RecursiveCharacterTextSplitter
  chunk_size=1000, overlap=200
      │
      ▼
OpenAI Embeddings (text-embedding-3-small, 1536 dim)
      │
      ▼
OpenSearch Index (KNN + BM25 hybrid)
  eccrp_laws / eccrp_judgments / eccrp_knowledge
```

### 4.2 RAG Query Pipeline
```
User Query
    │
    ▼
Query Rewriting (GPT-4o, temperature=0.1)
    │
    ▼
Embedding Generation
    │
    ▼
Hybrid Search (KNN score * 0.7 + BM25 * 0.3)
    │
    ▼
Top-K (10) Results Filtering (similarity >= 0.7)
    │
    ▼
Context Formatting (section ref + content)
    │
    ▼
Prompt: System (legal expert persona + MCC rules) + Context + Query
    │
    ▼
GPT-4o Generation (temperature=0.1, max_tokens=4096)
    │
    ▼
Confidence Scoring:
  base = top_retrieval_score / 10
  doc_factor = doc_count / top_k
  final = base * 0.7 + doc_factor * 0.3
  penalize if uncertainty phrases detected
    │
    ▼
Structured Response + Citations + Judgments + Disclaimer
```

### 4.3 Hallucination Prevention
- Low temperature (0.1) for deterministic legal outputs
- Explicit instruction to cite provision numbers
- Explicit instruction to say "I don't know" when uncertain
- Confidence score surfaced to user
- Always-present legal disclaimer
- Source attribution for every citation

---

## 5. Security Architecture

### 5.1 Authentication Security
- bcrypt password hashing (12 rounds)
- JWT with HS256, 60-minute expiry
- Refresh token rotation (revoke on use)
- Account lockout after 5 failed attempts (30 min)
- Rate limiting: 120 req/min per IP (Redis-backed in production)

### 5.2 Input Validation
- Pydantic v2 strict validation on all inputs
- PAN number format validation (regex)
- Phone number format validation (E.164)
- Password complexity enforcement (uppercase + digit + special char)
- File type whitelist + size limits for uploads

### 5.3 OWASP Protections
- **SQL Injection**: SQLAlchemy parameterized queries, no raw SQL
- **XSS**: Next.js default escaping, CSP headers
- **CSRF**: SameSite=Strict cookies, JWT in Authorization header
- **Path Traversal**: File storage via MinIO object keys (not filesystem)
- **Sensitive Data**: No PAN/Aadhaar in logs, truncated in responses
- **Rate Limiting**: Per-IP middleware on all endpoints
- **Audit Trail**: All mutations logged to audit_logs table

---

## 6. Scalability Design

### 6.1 Horizontal Scaling
- Backend: Stateless FastAPI workers behind Nginx (HPA: 2-10 pods)
- Frontend: Next.js standalone build (2 replicas)
- Database: Read replicas for heavy query loads
- Cache: Redis cluster for session/cache

### 6.2 Performance Targets
| Metric | Target |
|--------|--------|
| API P95 latency | < 200ms (non-AI) |
| AI query latency | < 5s (RAG pipeline) |
| Eligibility check | < 500ms |
| Dashboard load | < 1s |
| Concurrent users | 1,000+ |

### 6.3 Caching Strategy
- Eligibility checks: Cached by (candidate_id, election_type) for 1 hour
- Legal rules / judgments: Cached 24 hours (rarely change)
- Election data: Cached 1 hour
- AI responses: Not cached (each query unique)

---

## 7. Data Flow: Eligibility Check

```
Frontend: POST /eligibility/check
    { candidate_id, election_type, state_id }
          │
          ▼
EligibilityService.run_full_check()
          │
    ┌─────┴──────┐
    │             │
Load Candidate  Mark previous checks
from PostgreSQL is_latest=False
    │
    ▼
Run 10 checks in parallel (pure Python, no external calls):
  ✓ citizenship_check()
  ✓ age_check()            ← DOB from DB vs. AGE_REQUIREMENTS map
  ✓ electoral_roll_check() ← roll number + state present
  ✓ office_of_profit_check()
  ✓ government_contract_check()
  ✓ insolvency_check()
  ✓ conviction_check()     ← Section 8(3) RPA 1951 logic
  ✓ corrupt_practices_check()
  ✓ election_expenditure_check()
  ✓ local_body_check()
    │
    ▼
_calculate_scores()
  → Critical failures → DISQUALIFIED (score=0, risk=CRITICAL)
  → Weighted scoring → Eligibility status + Risk level
    │
    ▼
_build_legal_explanation()
_build_recommendations()
    │
    ▼
Persist EligibilityCheck → PostgreSQL
    │
    ▼
Return EligibilityCheckResponse
```

---

## 8. MCC Check Data Flow

```
POST /mcc/check { election_id, activity_description, activity_type }
    │
    ▼
MCCService.check_activity()
    │
    ├─ Step 1: Rule-based check
    │   KEYWORD_RULE_MAP (50+ keywords → MCC rule)
    │   Returns: MCCStatus + triggered_rules[]
    │
    └─ Step 2: AI-enhanced analysis (if OPENAI_API_KEY configured)
        LLM prompt: activity + triggered rules + full MCC rules reference
        Returns: violation_details, confidence, recommended_action
    │
    ▼
Persist MCCCheck → PostgreSQL
    │
    ▼
Return MCCCheckResponse with:
  mcc_status (compliant/potential_violation/violation)
  violation_category
  applicable_mcc_rules (with severity)
  eci_circular_refs
  recommended_action
  ai_confidence_score
```

---

## 9. Deployment Guide

### 9.1 Environment Variables (Production)
```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:pass@rds-endpoint:5432/eccrp
REDIS_URL=redis://elasticache-endpoint:6379/0
JWT_SECRET_KEY=<64-char random string from secrets.token_urlsafe(64)>
SECRET_KEY=<64-char random string>
OPENAI_API_KEY=sk-...
OPENSEARCH_URL=https://opensearch-endpoint:9200
NEO4J_URI=bolt://neo4j-endpoint:7687
MINIO_ENDPOINT=s3.amazonaws.com  # Or MinIO in production
CORS_ORIGINS=["https://eccrp.in"]
ALLOWED_HOSTS=["api.eccrp.in"]
RATE_LIMIT_PER_MINUTE=120
BCRYPT_ROUNDS=12
```

### 9.2 Production Checklist
- [ ] Change all default passwords and secret keys
- [ ] Enable TLS/HTTPS (cert-manager + Let's Encrypt)
- [ ] Configure PostgreSQL with SSL
- [ ] Enable OpenSearch security plugin
- [ ] Set up automated database backups (daily)
- [ ] Configure Grafana alerting for error rates
- [ ] Enable CloudFlare WAF
- [ ] Set `DEBUG=false`, `DATABASE_ECHO=false`
- [ ] Review CORS_ORIGINS — no wildcards in production
- [ ] Seed judgment database via admin API
- [ ] Ingest legal corpus into OpenSearch

---

## 10. Testing Strategy

### 10.1 Test Pyramid
```
          /\
         /E2E\        Playwright (key user flows)
        /──────\
       /Integra-\     httpx AsyncClient (API contracts)
      /──────────\
     /Unit Tests  \   pytest (service logic, scoring, rules)
    /______________\
```

### 10.2 Key Test Scenarios
- Eligibility: All 10 checks pass / fail combinations
- Scoring: Disqualification triggers (insolvency, serious conviction)
- MCC: Keyword detection for 50+ activity types
- Auth: Login, token refresh, lockout, role enforcement
- API contracts: 200/201/401/403/404/422 status codes
- Legal accuracy: Age requirements per election type

---

*End of Technical Design Document*
