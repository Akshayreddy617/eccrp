# ECCRP API Reference
**Base URL**: `https://api.eccrp.in/api/v1`  
**Format**: JSON  
**Auth**: Bearer JWT token in Authorization header

---

## Authentication

### POST /auth/register
Create a new user account.

**Request**:
```json
{
  "email": "candidate@example.com",
  "password": "SecurePass@123",
  "full_name": "Ravi Kumar",
  "role": "candidate"
}
```
**Roles**: `candidate` | `consultant` | `lawyer` | `journalist` | `researcher`

**Response 201**:
```json
{
  "id": "uuid",
  "email": "candidate@example.com",
  "full_name": "Ravi Kumar",
  "role": "candidate",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### POST /auth/login
Authenticate and receive JWT tokens.

**Request**:
```json
{ "email": "candidate@example.com", "password": "SecurePass@123" }
```

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "64-char-random-token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### POST /auth/refresh
Exchange refresh token for new tokens (rotation).

**Request**: `{ "refresh_token": "..." }`  
**Response 200**: Same as login

---

### GET /auth/me
Get current user profile.

**Headers**: `Authorization: Bearer <access_token>`  
**Response 200**: User object

---

## Elections

### POST /elections/select
**Module 1**: Load applicable provisions for election type.

**Request**:
```json
{
  "election_type": "lok_sabha",
  "state_code": "AP",
  "constituency_name": "Anantapur"
}
```

**Response 200**:
```json
{
  "election_type": "lok_sabha",
  "state": "Andhra Pradesh",
  "applicable_provisions": [
    { "article": "84", "title": "Qualifications for Parliament", "key_points": [...] }
  ],
  "applicable_laws": [
    { "section": "8", "title": "Disqualification on conviction" }
  ],
  "applicable_sec_rules": [...],
  "applicable_judgments": [
    { "case": "Lily Thomas v. Union of India", "citation": "(2013) 7 SCC 653", ... }
  ],
  "constituency_details": { "name": "Anantapur", "number": 15, "reservation_category": "GEN" }
}
```

**Election types**:
`lok_sabha` | `rajya_sabha` | `legislative_assembly` | `legislative_council` | `gram_panchayat` | `mandal_parishad` | `zilla_parishad` | `municipality` | `municipal_corporation`

---

## Eligibility

### POST /eligibility/check
**Module 2**: Run full eligibility assessment.

**Request**:
```json
{
  "candidate_id": "uuid",
  "election_type": "lok_sabha",
  "state_id": "uuid",
  "election_id": "uuid"
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "candidate_id": "uuid",
  "election_type": "lok_sabha",
  "eligibility_status": "eligible",
  "eligibility_score": 95.0,
  "risk_score": 5.0,
  "risk_level": "low",
  "citizenship_check": true,
  "age_check": true,
  "age_check_details": "Age: 44 years. Required: ≥25 years per Article 84(b). PASS",
  "electoral_roll_check": true,
  "office_of_profit_check": true,
  "government_contract_check": true,
  "insolvency_check": true,
  "conviction_check": true,
  "conviction_details": [],
  "applicable_articles": [...],
  "applicable_sections": [...],
  "applicable_judgments": [...],
  "legal_explanation": "Eligibility Assessment for Lok Sabha...",
  "recommendations": [
    { "priority": "LOW", "action": "Proceed with nomination", "legal_basis": "Section 33 RPA 1951" }
  ],
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Eligibility statuses**: `eligible` | `potentially_eligible` | `high_risk` | `disqualified`

---

### GET /eligibility/candidate/{candidate_id}/latest
Get latest eligibility check for a candidate.

---

## Compliance Risk

### POST /compliance/assess/{candidate_id}
**Module 5**: Generate comprehensive risk assessment.

**Query params**: `election_id` (optional UUID)

**Response 201**:
```json
{
  "id": "uuid",
  "candidate_id": "uuid",
  "eligibility_risk": "low",
  "eligibility_risk_score": 5.0,
  "eligibility_risk_factors": [],
  "disclosure_risk": "medium",
  "disclosure_risk_score": 35.0,
  "disclosure_risk_factors": [
    { "risk": "Affidavit not filed", "legal_basis": "Section 33A RPA 1951" }
  ],
  "legal_risk": "low",
  "legal_risk_score": 10.0,
  "legal_risk_factors": [],
  "expenditure_risk": "low",
  "expenditure_risk_score": 15.0,
  "expenditure_risk_factors": [],
  "mcc_risk": "low",
  "mcc_risk_score": 0.0,
  "mcc_risk_factors": [],
  "overall_risk": "medium",
  "overall_risk_score": 18.5,
  "executive_summary": "🟡 MEDIUM RISK (19/100): Several compliance items need attention...",
  "priority_actions": [
    { "source": "disclosure", "action": "File Form 26 affidavit", "legal_basis": "Section 33A RPA 1951" }
  ],
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Expenditure

### POST /expenditure/
Add an expenditure entry.

**Request**:
```json
{
  "candidate_id": "uuid",
  "election_id": "uuid",
  "category": "vehicle",
  "description": "Hire of 3 campaign vehicles for rally",
  "amount": 45000,
  "expense_date": "2024-03-15T10:00:00Z",
  "vendor_name": "Travel Agency XYZ",
  "vendor_pan": "AABCT1234D",
  "receipt_number": "TA/2024/123"
}
```

**Categories**: `vehicle` | `advertising_print` | `advertising_digital` | `advertising_outdoor` | `meetings_rallies` | `travel` | `volunteers` | `campaign_materials` | `sound_equipment` | `other`

---

### GET /expenditure/dashboard/{candidate_id}/{election_id}
**Module 7**: Get expenditure dashboard.

**Response 200**:
```json
{
  "candidate_id": "uuid",
  "election_id": "uuid",
  "expenditure_limit": 7500000,
  "total_spent": 2350000,
  "limit_utilization_pct": 31.3,
  "risk_level": "low",
  "by_category": [
    { "category": "vehicle", "total": 850000, "count": 12, "percentage": 36.2 }
  ],
  "daily_trend": [
    { "date": "2024-03-01", "amount": 125000 }
  ],
  "risk_alerts": [],
  "recent_entries": [...]
}
```

---

## MCC Checker

### POST /mcc/check
**Module 8**: Check campaign activity against MCC.

**Request**:
```json
{
  "election_id": "uuid",
  "activity_description": "Distributing sarees to voters in Tirupati",
  "activity_type": "gift_distribution",
  "activity_date": "2024-03-18T18:00:00Z",
  "activity_location": "Tirupati, Andhra Pradesh"
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "mcc_status": "violation",
  "violation_category": "bribery",
  "violation_details": "Distributing sarees constitutes bribery under Section 123(1) RPA 1951...",
  "applicable_mcc_rules": [
    {
      "id": "MCC-BRIBE-01",
      "category": "Bribery",
      "rule": "No distribution of liquor, cash, gifts...",
      "severity": "critical"
    }
  ],
  "eci_circular_refs": [
    { "source": "ECI MCC Part VI; Section 123(1) RPA 1951" }
  ],
  "recommended_action": "Stop the activity immediately and consult your election law counsel.",
  "ai_confidence_score": 0.95,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**MCC statuses**: `compliant` | `potential_violation` | `violation`

---

## AI Assistant

### POST /ai/query
**Module 12**: Ask an election law question.

**Request**:
```json
{
  "query": "Can I contest elections if a criminal case is pending against me?",
  "context": { "election_type": "lok_sabha" },
  "session_id": "optional-uuid-for-conversation-tracking"
}
```

**Response 200**:
```json
{
  "query": "Can I contest elections if a criminal case is pending against me?",
  "answer": "Yes, you can contest elections even if a criminal case is pending...",
  "legal_basis": [
    {
      "source_type": "rp_act_1951",
      "section_number": "8(3)",
      "title": "Disqualification on conviction",
      "relevance_score": 0.94
    }
  ],
  "relevant_judgments": [
    {
      "case_name": "Lily Thomas v. Union of India",
      "citation": "(2013) 7 SCC 653",
      "relevance": "Pending cases ≠ disqualification; conviction with ≥2 years does"
    }
  ],
  "recommended_action": "Disclose all pending cases in Form 26 mandatory affidavit",
  "confidence_score": 0.91,
  "disclaimer": "This answer is generated by an AI system for informational purposes only...",
  "sources": [...]
}
```

---

## Judgments

### GET /judgments/landmarks
**Module 10**: Get all landmark election judgments.

**Response 200**:
```json
{
  "total": 6,
  "judgments": [
    {
      "case_name": "Association for Democratic Reforms v. Union of India",
      "citation": "(2002) 5 SCC 294",
      "year": 2002,
      "court": "Supreme Court of India",
      "issue": "Whether voters have right to know candidate background",
      "ratio_decidendi": "Voters have fundamental right under Art. 19(1)(a)...",
      "impact_summary": "Established mandatory Form 26 disclosure...",
      "relevant_sections": [{"section": "33A", "act": "RPA 1951"}],
      "is_landmark": true
    }
  ]
}
```

---

### GET /judgments/impact/scenario
**Module 11**: Get judgment impact chain for a scenario.

**Query param**: `scenario=Candidate has pending criminal case`

**Response 200**:
```json
[
  {
    "scenario": "Candidate has pending criminal case under IPC",
    "applicable_law": { "section": "8(3)", "act": "Representation of the People Act 1951" },
    "relevant_judgment": {
      "case_name": "Lily Thomas v. Union of India",
      "citation": "(2013) 7 SCC 653",
      "year": 2013
    },
    "compliance_requirement": "Disclose ALL pending criminal cases in Form 26...",
    "recommended_action": "File complete affidavit with criminal case details..."
  }
]
```

---

## Timeline

### GET /timeline/{election_id}
**Module 6**: Get election timeline with compliance deadlines.

**Response 200**:
```json
{
  "election": { "id": "uuid", "name": "AP Assembly 2024", "expenditure_limit": 4000000 },
  "key_dates": {
    "notification_date": "2024-03-01",
    "nomination_end": "2024-03-08",
    "withdrawal_date": "2024-03-11",
    "polling_date": "2024-03-25",
    "result_date": "2024-03-28"
  },
  "countdown": { "days_to_polling": 15, "days_to_nomination_deadline": 3 },
  "timeline": [
    {
      "date": "2024-03-08",
      "title": "DEADLINE: Last Day for Nomination",
      "description": "Final day to file nomination...",
      "category": "deadline",
      "is_deadline": true
    }
  ],
  "legal_notes": ["MCC comes into force on election notification date..."]
}
```

### GET /timeline/{election_id}/export.ics
Export timeline as iCalendar file (Content-Type: text/calendar).

---

## Public Portal (No Auth Required)

### GET /public/candidates
Search candidate disclosures.

**Query params**: `name`, `party`, `page`, `page_size`

**Response 200**:
```json
{
  "results": [
    {
      "id": "uuid",
      "full_name": "Ravi Kumar",
      "party_affiliation": "Test Party",
      "has_criminal_cases": false,
      "has_pending_criminal_cases": false
    }
  ],
  "total": 1,
  "page": 1
}
```

---

### GET /public/candidates/{candidate_id}/disclosures
Get full public disclosures for a candidate.

**Response 200**:
```json
{
  "candidate": { "full_name": "Ravi Kumar", "party_affiliation": "...", "education": "..." },
  "disclosures": {
    "has_criminal_cases": false,
    "criminal_cases_count": 0,
    "assets_movable": { "cash": 50000, "bank_deposits": 250000 },
    "assets_immovable": {},
    "liabilities": {},
    "criminal_cases": [],
    "affidavit_date": "2024-03-05"
  },
  "election_history": [],
  "data_source": "Publicly declared affidavit data (Form 26)...",
  "disclaimer": "..."
}
```

---

## Error Reference

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (delete/update) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/expired token) |
| 403 | Forbidden (insufficient role) |
| 404 | Not Found |
| 409 | Conflict (duplicate email) |
| 422 | Unprocessable Entity (schema validation) |
| 429 | Rate Limited (120 req/min per IP) |
| 503 | Service Unavailable (dependency down) |

---

## Rate Limits
- Default: 120 requests per minute per IP
- AI queries: 20 per minute per user
- Exceeded: HTTP 429 with `Retry-After: 60` header
