"""
ECCRP Integration Tests - API Endpoints
Uses httpx AsyncClient to test FastAPI routes end-to-end.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.main import app
from app.db.session import get_db, Base
from app.core.config import settings

# ── Test Database ──────────────────────────────────────────────────────────

TEST_DATABASE_URL = "postgresql+asyncpg://eccrp:eccrp_secret@localhost:5432/eccrp_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    """Create a user and return auth headers."""
    # Register
    resp = await client.post("/api/v1/auth/register", json={
        "email": "testuser@eccrp.in",
        "password": "TestPass@123",
        "full_name": "Test User",
        "role": "candidate",
    })
    # Login
    resp = await client.post("/api/v1/auth/login", json={
        "email": "testuser@eccrp.in",
        "password": "TestPass@123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "new_user@eccrp.in",
            "password": "NewPass@123",
            "full_name": "New User",
            "role": "consultant",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new_user@eccrp.in"
        assert data["role"] == "consultant"
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {
            "email": "duplicate@eccrp.in",
            "password": "DupPass@123",
            "full_name": "Dup User",
            "role": "candidate",
        }
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_register_weak_password(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "weak@eccrp.in",
            "password": "simple",
            "full_name": "Weak User",
        })
        assert resp.status_code == 422

    async def test_login_success(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "login_test@eccrp.in",
            "password": "LoginPass@123",
            "full_name": "Login Test",
        })
        resp = await client.post("/api/v1/auth/login", json={
            "email": "login_test@eccrp.in",
            "password": "LoginPass@123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "testuser@eccrp.in",
            "password": "WrongPassword@123",
        })
        assert resp.status_code == 401

    async def test_get_me_authenticated(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert "email" in resp.json()

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 403  # No bearer token


# ── Candidate Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestCandidateEndpoints:
    async def test_create_candidate(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/candidates/", json={
            "full_name": "Ravi Kumar",
            "party_affiliation": "Test Party",
            "is_independent": False,
            "has_criminal_cases": False,
            "has_pending_criminal_cases": False,
            "holds_office_of_profit": False,
            "has_government_contracts": False,
            "is_bankrupt_or_insolvent": False,
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["full_name"] == "Ravi Kumar"
        assert "id" in data

    async def test_create_candidate_invalid_pan(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/candidates/", json={
            "full_name": "Invalid PAN",
            "pan_number": "INVALID",
        }, headers=auth_headers)
        assert resp.status_code == 422

    async def test_list_candidates(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/candidates/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_candidate_not_found(self, client: AsyncClient, auth_headers: dict):
        from uuid import uuid4
        resp = await client.get(f"/api/v1/candidates/{uuid4()}", headers=auth_headers)
        assert resp.status_code == 404


# ── Election Selection Tests ───────────────────────────────────────────────

@pytest.mark.asyncio
class TestElectionSelection:
    async def test_select_lok_sabha(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/elections/select", json={
            "election_type": "lok_sabha",
            "state_code": "AP",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["election_type"] == "lok_sabha"
        assert len(data["applicable_provisions"]) > 0
        assert len(data["applicable_laws"]) > 0
        assert len(data["applicable_judgments"]) > 0

    async def test_select_legislative_assembly(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/elections/select", json={
            "election_type": "legislative_assembly",
            "state_code": "TN",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Should have Article 173 for state elections
        articles = [p["article"] for p in data["applicable_provisions"]]
        assert "173" in articles


# ── MCC Check Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestMCCChecker:
    @pytest_asyncio.fixture(autouse=True)
    async def create_election(self, client: AsyncClient, auth_headers: dict):
        """Create a test election for MCC checks."""
        # First create a state and constituency (simplified - use existing data)
        pass

    async def test_mcc_rules_endpoint(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/mcc/rules", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "rules" in data
        assert data["total"] > 0


# ── Knowledge Search Tests ────────────────────────────────────────────────

@pytest.mark.asyncio
class TestKnowledgeSearch:
    async def test_search_returns_results_structure(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/knowledge/search", json={
            "query": "criminal conviction election",
            "limit": 5,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "query" in data
        assert "results" in data
        assert "total" in data
        assert "search_time_ms" in data


# ── Judgment Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestJudgments:
    async def test_get_landmark_judgments(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/judgments/landmarks", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "judgments" in data
        assert len(data["judgments"]) >= 5  # At least 5 pre-seeded

    async def test_all_landmark_judgments_have_required_fields(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/judgments/landmarks", headers=auth_headers)
        for j in resp.json()["judgments"]:
            assert "case_name" in j
            assert "citation" in j
            assert "ratio_decidendi" in j
            assert "impact_summary" in j
            assert "relevant_sections" in j

    async def test_judgment_impact_scenario_criminal(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/judgments/impact/scenario",
            params={"scenario": "Candidate has a pending criminal case under IPC 302"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        impacts = resp.json()
        assert len(impacts) > 0
        assert "applicable_law" in impacts[0]
        assert "compliance_requirement" in impacts[0]

    async def test_judgment_impact_scenario_expenditure(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get(
            "/api/v1/judgments/impact/scenario",
            params={"scenario": "Candidate is spending heavily on campaign vehicles"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        impacts = resp.json()
        assert any("expenditure" in str(imp).lower() for imp in impacts)


# ── Health Check Tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestHealthEndpoints:
    async def test_root_endpoint(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "platform" in data
        assert "ECCRP" in data["platform"]

    async def test_health_endpoint(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


# ── Public Portal Tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestPublicPortal:
    async def test_public_candidate_search_no_auth(self, client: AsyncClient):
        """Public endpoints should work without authentication."""
        resp = await client.get("/api/v1/public/candidates")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data

    async def test_public_candidate_search_with_name(self, client: AsyncClient):
        resp = await client.get("/api/v1/public/candidates", params={"name": "Test"})
        assert resp.status_code == 200

    async def test_public_nonexistent_candidate_404(self, client: AsyncClient):
        from uuid import uuid4
        resp = await client.get(f"/api/v1/public/candidates/{uuid4()}/disclosures")
        assert resp.status_code == 404
