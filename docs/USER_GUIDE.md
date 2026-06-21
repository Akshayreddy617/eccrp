# ECCRP User Guide
**Election Compliance & Candidate Readiness Platform**

---

## Getting Started

### Step 1 — Register
Navigate to `/register`. Choose your role:
- **Candidate** — Manage your own compliance
- **Consultant** — Manage multiple candidates
- **Lawyer** — Legal research + AI assistant
- **Journalist** — Knowledge base + public portal

### Step 2 — Add a Candidate
Go to **Candidates → New Candidate**. Fill in:
- Full name (as per official documents)
- Date of birth (required for age eligibility check)
- PAN number (format: ABCDE1234F)
- Electoral roll number + state
- Criminal case status (self-declared)
- Office of profit status

### Step 3 — Run Eligibility Check
Go to **Eligibility**. Select the candidate and election type. Click **Run Eligibility Check**.

The system checks 10+ criteria and returns:
- ✅ **Eligible** — Proceed with nomination
- ⚠️ **Potentially Eligible** — Address flagged issues
- 🔴 **High Risk** — Urgent legal consultation needed
- ❌ **Disqualified** — Cannot contest this election

---

## Module Guide

### Module 2 — Eligibility Assessment
**Path**: `/eligibility`

Checks performed:
| Check | Legal Basis |
|-------|-------------|
| Citizenship | Article 84(a) / 173(a) |
| Age ≥ 25 (LS/LA), 30 (RS/LC), 21 (local) | Article 84(b) / 173(b) |
| Electoral roll registration | Article 84(c) / Section 19 RPA 1950 |
| No office of profit | Article 102(1)(a) / 191(1)(a) |
| No government contracts | Section 9A RPA 1951 |
| Not insolvent | Section 9 RPA 1951 |
| No disqualifying conviction ≥ 2 years | Section 8(3) RPA 1951 |
| No expenditure violation | Section 10A RPA 1951 |

**Key judgment**: Lily Thomas v. Union of India (2013) — conviction with ≥2 years sentence = immediate disqualification even if appeal pending.

---

### Module 3 — Nomination Readiness
**Path**: `/nomination`

Upload documents to track readiness:
- **Form 26** (Affidavit) — 25 points
- **Electoral Roll Proof** — 20 points
- **Assets Declaration** — 15 points
- **Criminal Disclosure** — 15 points
- **Identity/Photograph** — 15 points
- **Liabilities Declaration** — 10 points

Score 100/100 = fully ready to file nomination.

---

### Module 4 — Affidavit Validator
**Path**: `/affidavit`

Upload Form 26 (PDF/image). AI extracts and validates:
- Movable assets (cash, bank deposits, vehicles, jewelry)
- Immovable assets (land, buildings)
- Liabilities (bank loans, other loans)
- Criminal cases (pending or convicted)
- PAN number and educational qualification

**Common validation errors**:
- Missing PAN — mandatory per ECI guidelines
- Spouse assets not included — must disclose
- Criminal cases not fully described — Section 33A violation risk
- Property value inconsistency — potential election petition ground

---

### Module 5 — Compliance Risk Engine
**Path**: `/compliance`

Generates a 5-dimension risk report:
1. **Eligibility Risk** — From eligibility check results
2. **Disclosure Risk** — From affidavit completeness
3. **Legal Risk** — From criminal case analysis
4. **Expenditure Risk** — From spending vs. limit
5. **MCC Risk** — From Model Code violations

Overall risk is a weighted average. **Critical risk (80-100)** requires immediate action.

---

### Module 6 — Election Timeline
**Path**: `/timeline`

Select an election to view:
- All key dates (notification, nomination, polling, counting)
- Countdown timers (days to polling, days to nomination deadline)
- Action items (what to do and when)
- Compliance deadlines (48-hour silence, expenditure filing)
- Export as `.ics` calendar file (works with Google Calendar, Outlook, Apple Calendar)

**Critical legal deadlines**:
- File nomination within nomination window (typically 4-7 days)
- Campaign silence: 48 hours before polling (Section 126 RPA 1951)
- File expenditure account: within 30 days of results (Section 78 RPA 1951)
  - **Failure = 3-year disqualification** (Section 10A RPA 1951)

---

### Module 7 — Expenditure Tracker
**Path**: `/expenditure`

Track all campaign expenses by category:
- Vehicle expenses
- Print/digital/outdoor advertising
- Meetings and rallies
- Travel
- Volunteers
- Campaign materials

**Risk alerts triggered at**:
- 70% utilisation — Medium risk warning
- 85% utilisation — High risk warning
- 95% utilisation — Critical: near disqualification threshold
- 100%+ — Violation of Section 10A RPA 1951

**Digital advertising note**: Spends >₹1 lakh require MCMC pre-certification per ECI guidelines.

---

### Module 8 — MCC Checker
**Path**: `/mcc`

Describe any campaign activity. The system checks against ECI Model Code of Conduct guidelines.

**Common violations**:
| Activity | Status | Legal Basis |
|----------|--------|-------------|
| Distributing sarees/gifts to voters | 🔴 Violation | Section 123(1) RPA 1951 |
| Using government vehicle for rally | 🔴 Violation | ECI MCC Part VII |
| TV ad without MCMC pre-certification | 🔴 Violation | Section 126A RPA 1951 |
| Biryani distribution before polling | ⚠️ Potential | Section 123(1) RPA 1951 |
| Templated social media post | ✅ Compliant | — |
| Press conference with no freebies | ✅ Compliant | — |

---

### Module 12 — AI Governance Assistant
**Path**: `/ai-assistant`

Ask any election law question in natural language. Examples:
- *"Can I contest if a criminal case is pending?"*
- *"What assets do I need to disclose in Form 26?"*
- *"What is the expenditure limit for Andhra Pradesh assembly?"*
- *"Can I campaign in a temple during MCC?"*
- *"What happens if I don't file my expenditure account?"*

The AI searches the legal corpus (Constitution, RPA Acts, ECI Circulars, SC Judgments) and provides answers with citations and confidence scores.

**Confidence score guide**:
- 80-100% — High confidence, well-supported by legal corpus
- 60-79% — Moderate confidence, general legal principles apply
- Below 60% — Low confidence, consult election lawyer

⚠️ *AI answers are for informational purposes only. Not legal advice.*

---

### Module 15 — Public Transparency Portal
**Path**: `/public` (no login required)

Search any candidate's publicly declared disclosures:
- Assets (movable and immovable)
- Liabilities
- Criminal cases
- Educational qualification
- Election history

Data source: Form 26 affidavits as required by Section 33A RPA 1951 and ADR v. Union of India (2002).

---

## Frequently Asked Questions

**Q: Can a person with a pending criminal case contest elections?**
A: Yes, pending cases (not convicted) do not bar candidacy. However, all pending cases MUST be disclosed in Form 26. Failure to disclose can lead to election petition. Ref: ADR v. Union of India (2002).

**Q: What if I am convicted but have filed an appeal?**
A: Per the Lily Thomas judgment (2013), a conviction with sentence ≥2 years results in **immediate disqualification** even if appeal is pending. Section 8(4) which provided 3-month protection was struck down as unconstitutional.

**Q: Do I need to disclose my spouse's assets?**
A: Yes. Form 26 requires disclosure of assets and liabilities of self, spouse, and dependent family members. Non-disclosure can lead to election petition on grounds of corrupt practice.

**Q: What is the expenditure limit for my election?**
A: Limits vary by election type and state. Current limits (as of ECI notification):
- Lok Sabha: ₹75 lakh (large states) / ₹54 lakh (small states)
- State Assembly: ₹28-40 lakh (varies by state)
- Enter your election in the system to see the specific limit.

**Q: When does the Model Code of Conduct start?**
A: MCC comes into effect **immediately** on the date the Election Commission announces the election schedule (notification date).

**Q: What if I miss filing my expenditure account?**
A: Section 10A RPA 1951: failure to file within 30 days of results = **3-year disqualification** from contesting any election.

---

## Legal Disclaimer

ECCRP provides AI-assisted compliance guidance based on publicly available Indian election law. All outputs are for **informational purposes only** and do **not constitute legal advice**. Laws and ECI guidelines may be updated. Always verify with current ECI notifications and consult a qualified election law practitioner for specific legal matters.
