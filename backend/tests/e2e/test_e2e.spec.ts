// ECCRP End-to-End Tests (Playwright)
import { test, expect } from "@playwright/test";

const BASE_URL = process.env.BASE_URL || "http://localhost:3000";
const API_URL = process.env.API_URL || "http://localhost:8000/api/v1";

// ── Auth Flow ──────────────────────────────────────────────────────────────

test.describe("Authentication Flow", () => {
  const TEST_EMAIL = `e2e_${Date.now()}@eccrp.in`;
  const TEST_PASSWORD = "E2ETest@123";

  test("should register a new user", async ({ page }) => {
    await page.goto(`${BASE_URL}/register`);
    await page.fill('[placeholder*="email" i]', TEST_EMAIL);
    await page.fill('[placeholder*="password" i]', TEST_PASSWORD);
    await page.fill('[placeholder*="name" i]', "E2E Test User");
    await page.click('button[type="submit"], button:has-text("Register")');
    await expect(page).toHaveURL(/login|dashboard/, { timeout: 10000 });
  });

  test("should login and reach dashboard", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('[type="email"]', "admin@eccrp.in");
    await page.fill('[type="password"]', "Admin@123");
    await page.click('button[type="submit"], button:has-text("Sign In")');
    await expect(page).toHaveURL(/dashboard/, { timeout: 10000 });
    await expect(page.locator("h1")).toContainText(/Welcome/i);
  });

  test("should reject invalid credentials", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('[type="email"]', "wrong@eccrp.in");
    await page.fill('[type="password"]', "WrongPass@123");
    await page.click('button[type="submit"], button:has-text("Sign In")');
    // Should stay on login or show error
    await expect(page).toHaveURL(/login/, { timeout: 5000 });
  });
});

// ── Dashboard ──────────────────────────────────────────────────────────────

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('[type="email"]', "admin@eccrp.in");
    await page.fill('[type="password"]', "Admin@123");
    await page.click('button:has-text("Sign In")');
    await page.waitForURL(/dashboard/);
  });

  test("should display dashboard stats", async ({ page }) => {
    await expect(page.locator("text=Total Candidates")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Quick Actions")).toBeVisible();
  });

  test("sidebar navigation should work", async ({ page }) => {
    await page.click('text=Eligibility');
    await expect(page).toHaveURL(/eligibility/);

    await page.click('text=AI Assistant');
    await expect(page).toHaveURL(/ai-assistant/);

    await page.click('text=MCC Checker');
    await expect(page).toHaveURL(/mcc/);
  });
});

// ── Eligibility Check ──────────────────────────────────────────────────────

test.describe("Eligibility Check", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('[type="email"]', "admin@eccrp.in");
    await page.fill('[type="password"]', "Admin@123");
    await page.click('button:has-text("Sign In")');
    await page.waitForURL(/dashboard/);
  });

  test("should load eligibility page with legal reference panel", async ({ page }) => {
    await page.goto(`${BASE_URL}/eligibility`);
    await expect(page.locator("text=Run Eligibility Check")).toBeVisible();
    await expect(page.locator("text=Legal Basis")).toBeVisible();
    await expect(page.locator("text=Article 84")).toBeVisible();
    await expect(page.locator("text=Section 8")).toBeVisible();
  });
});

// ── AI Assistant ───────────────────────────────────────────────────────────

test.describe("AI Assistant", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('[type="email"]', "admin@eccrp.in");
    await page.fill('[type="password"]', "Admin@123");
    await page.click('button:has-text("Sign In")');
    await page.waitForURL(/dashboard/);
  });

  test("should display AI assistant with example questions", async ({ page }) => {
    await page.goto(`${BASE_URL}/ai-assistant`);
    await expect(page.locator("text=AI Governance Assistant")).toBeVisible();
    await expect(page.locator("text=Example Questions")).toBeVisible();
  });

  test("should click example question and populate input", async ({ page }) => {
    await page.goto(`${BASE_URL}/ai-assistant`);
    const exampleBtn = page.locator("button").filter({ hasText: /criminal case/i }).first();
    await exampleBtn.click();
    const input = page.locator("textarea");
    await expect(input).toHaveValue(/criminal/i);
  });
});

// ── MCC Checker ────────────────────────────────────────────────────────────

test.describe("MCC Checker", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('[type="email"]', "admin@eccrp.in");
    await page.fill('[type="password"]', "Admin@123");
    await page.click('button:has-text("Sign In")');
    await page.waitForURL(/dashboard/);
  });

  test("should display MCC rules reference", async ({ page }) => {
    await page.goto(`${BASE_URL}/mcc`);
    await expect(page.locator("text=MCC Compliance Checker")).toBeVisible();
    await expect(page.locator("text=MCC Rules Reference")).toBeVisible({ timeout: 10000 });
  });

  test("should populate description from example click", async ({ page }) => {
    await page.goto(`${BASE_URL}/mcc`);
    const exBtn = page.locator("button").filter({ hasText: /saree/i }).first();
    await exBtn.click();
    const textarea = page.locator("textarea");
    await expect(textarea).toHaveValue(/saree/i);
  });
});

// ── Public Portal ──────────────────────────────────────────────────────────

test.describe("Public Transparency Portal", () => {
  test("should be accessible without login", async ({ page }) => {
    await page.goto(`${BASE_URL}/public`);
    await expect(page.locator("text=Public Transparency Portal")).toBeVisible();
    await expect(page.locator('input[placeholder*="candidate"]')).toBeVisible();
  });

  test("should show search results structure", async ({ page }) => {
    await page.goto(`${BASE_URL}/public`);
    await page.fill('input[placeholder*="candidate"]', "test");
    await page.click('button:has-text("Search")');
    await page.waitForTimeout(2000);
    // Either results or empty state
    const hasResults = await page.locator("text=candidate(s) found").isVisible().catch(() => false);
    const hasEmpty = await page.locator("text=Search for any candidate").isVisible().catch(() => false);
    expect(hasResults || hasEmpty).toBeTruthy();
  });
});

// ── Judgment Library ───────────────────────────────────────────────────────

test.describe("Judgment Library", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('[type="email"]', "admin@eccrp.in");
    await page.fill('[type="password"]', "Admin@123");
    await page.click('button:has-text("Sign In")');
    await page.waitForURL(/dashboard/);
  });

  test("should display landmark judgments", async ({ page }) => {
    await page.goto(`${BASE_URL}/judgments`);
    await expect(page.locator("text=Supreme Court Judgment Library")).toBeVisible();
    // Check for key judgments
    await expect(page.locator("text=Lily Thomas")).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Association for Democratic Reforms")).toBeVisible();
  });

  test("should switch to impact engine tab", async ({ page }) => {
    await page.goto(`${BASE_URL}/judgments`);
    await page.click("text=Judgment Impact Engine");
    await expect(page.locator("text=Module 11")).toBeVisible();
    await expect(page.locator("textarea")).toBeVisible();
  });
});

// ── API Health ─────────────────────────────────────────────────────────────

test.describe("API Health", () => {
  test("backend health endpoint should return 200", async ({ request }) => {
    const resp = await request.get(`${API_URL.replace("/api/v1", "")}/health`);
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.status).toBe("healthy");
  });

  test("landmark judgments endpoint should return data", async ({ request }) => {
    // Login first
    const loginResp = await request.post(`${API_URL}/auth/login`, {
      data: { email: "admin@eccrp.in", password: "Admin@123" },
    });
    if (!loginResp.ok()) return; // Skip if no admin user seeded

    const { access_token } = await loginResp.json();
    const resp = await request.get(`${API_URL}/judgments/landmarks`, {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.judgments.length).toBeGreaterThan(0);
  });
});
