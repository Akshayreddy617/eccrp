// ECCRP Frontend API Client
import axios, { AxiosInstance, AxiosRequestConfig } from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ── Types ──────────────────────────────────────────────────────────────────

export type ElectionType =
  | "lok_sabha" | "rajya_sabha" | "legislative_assembly" | "legislative_council"
  | "gram_panchayat" | "mandal_parishad" | "zilla_parishad"
  | "municipality" | "municipal_corporation";

export type EligibilityStatus = "eligible" | "potentially_eligible" | "high_risk" | "disqualified";
export type RiskLevel = "low" | "medium" | "high" | "critical";
export type MCCStatus = "compliant" | "potential_violation" | "violation";
export type UserRole = "super_admin" | "admin" | "consultant" | "candidate" | "lawyer" | "journalist" | "researcher" | "public";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Candidate {
  id: string;
  user_id: string;
  full_name: string;
  date_of_birth?: string;
  gender?: string;
  pan_number?: string;
  party_affiliation?: string;
  is_independent: boolean;
  has_criminal_cases: boolean;
  has_pending_criminal_cases: boolean;
  holds_office_of_profit: boolean;
  is_active: boolean;
  created_at: string;
}

export interface EligibilityCheck {
  id: string;
  candidate_id: string;
  election_type: ElectionType;
  eligibility_status: EligibilityStatus;
  eligibility_score: number;
  risk_score: number;
  risk_level: RiskLevel;
  citizenship_check?: boolean;
  age_check?: boolean;
  age_check_details?: string;
  electoral_roll_check?: boolean;
  office_of_profit_check?: boolean;
  conviction_check?: boolean;
  conviction_details: any[];
  applicable_articles: any[];
  applicable_sections: any[];
  applicable_judgments: any[];
  legal_explanation?: string;
  recommendations: any[];
  created_at: string;
}

export interface RiskAssessment {
  id: string;
  candidate_id: string;
  eligibility_risk?: RiskLevel;
  eligibility_risk_score?: number;
  disclosure_risk?: RiskLevel;
  disclosure_risk_score?: number;
  legal_risk?: RiskLevel;
  legal_risk_score?: number;
  expenditure_risk?: RiskLevel;
  expenditure_risk_score?: number;
  mcc_risk?: RiskLevel;
  mcc_risk_score?: number;
  overall_risk?: RiskLevel;
  overall_risk_score?: number;
  executive_summary?: string;
  priority_actions: any[];
  created_at: string;
}

export interface ExpenditureDashboard {
  candidate_id: string;
  election_id: string;
  expenditure_limit?: number;
  total_spent: number;
  limit_utilization_pct?: number;
  risk_level: RiskLevel;
  by_category: Array<{ category: string; total: number; count: number; percentage: number }>;
  daily_trend: Array<{ date: string; amount: number }>;
  risk_alerts: string[];
  recent_entries: any[];
}

export interface MCCCheckResult {
  id: string;
  mcc_status: MCCStatus;
  violation_category?: string;
  violation_details?: string;
  applicable_mcc_rules: any[];
  eci_circular_refs: any[];
  recommended_action?: string;
  ai_confidence_score?: number;
  created_at: string;
}

export interface AIQueryResponse {
  query: string;
  answer: string;
  legal_basis: any[];
  relevant_judgments: any[];
  recommended_action?: string;
  confidence_score: number;
  disclaimer: string;
  sources: any[];
}

export interface ElectionTimeline {
  election: any;
  key_dates: Record<string, string | null>;
  countdown: { days_to_polling?: number; days_to_nomination_deadline?: number };
  timeline: TimelineAction[];
  deadlines: TimelineAction[];
  milestones: TimelineAction[];
  legal_notes: string[];
}

export interface TimelineAction {
  date: string;
  title: string;
  description: string;
  category: string;
  is_deadline: boolean;
}

// ── Axios Instance ─────────────────────────────────────────────────────────

const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE,
    headers: { "Content-Type": "application/json" },
    timeout: 30000,
  });

  // Request interceptor: attach JWT
  client.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Response interceptor: handle 401
  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401 && typeof window !== "undefined") {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          try {
            const resp = await axios.post(`${API_BASE}/auth/refresh`, {
              refresh_token: refreshToken,
            });
            const { access_token, refresh_token } = resp.data;
            localStorage.setItem("access_token", access_token);
            localStorage.setItem("refresh_token", refresh_token);
            error.config.headers.Authorization = `Bearer ${access_token}`;
            return client.request(error.config);
          } catch {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            window.location.href = "/login";
          }
        } else {
          window.location.href = "/login";
        }
      }
      return Promise.reject(error);
    }
  );

  return client;
};

export const apiClient = createApiClient();

// ── API Functions ──────────────────────────────────────────────────────────

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role: string }) =>
    apiClient.post<User>("/auth/register", data),
  login: (email: string, password: string) =>
    apiClient.post<TokenResponse>("/auth/login", { email, password }),
  refresh: (refreshToken: string) =>
    apiClient.post<TokenResponse>("/auth/refresh", { refresh_token: refreshToken }),
  logout: (refreshToken: string) =>
    apiClient.post("/auth/logout", { refresh_token: refreshToken }),
  me: () => apiClient.get<User>("/auth/me"),
};

export const candidatesApi = {
  list: (params?: { page?: number; search?: string }) =>
    apiClient.get<Candidate[]>("/candidates/", { params }),
  get: (id: string) => apiClient.get<Candidate>(`/candidates/${id}`),
  create: (data: Partial<Candidate>) => apiClient.post<Candidate>("/candidates/", data),
  update: (id: string, data: Partial<Candidate>) =>
    apiClient.put<Candidate>(`/candidates/${id}`, data),
};

export const electionsApi = {
  select: (data: { election_type: ElectionType; state_code: string; constituency_name?: string }) =>
    apiClient.post("/elections/select", data),
  list: (params?: { election_type?: string; year?: number }) =>
    apiClient.get("/elections/", { params }),
  get: (id: string) => apiClient.get(`/elections/${id}`),
  create: (data: any) => apiClient.post("/elections/", data),
};

export const eligibilityApi = {
  check: (data: { candidate_id: string; election_type: ElectionType; state_id?: string }) =>
    apiClient.post<EligibilityCheck>("/eligibility/check", data),
  getLatest: (candidateId: string) =>
    apiClient.get<EligibilityCheck>(`/eligibility/candidate/${candidateId}/latest`),
  getHistory: (candidateId: string) =>
    apiClient.get<EligibilityCheck[]>(`/eligibility/candidate/${candidateId}`),
};

export const complianceApi = {
  assess: (candidateId: string, electionId?: string) =>
    apiClient.post<RiskAssessment>(
      `/compliance/assess/${candidateId}`,
      null,
      { params: electionId ? { election_id: electionId } : {} }
    ),
  getLatest: (candidateId: string) =>
    apiClient.get<RiskAssessment>(`/compliance/candidate/${candidateId}/latest`),
};

export const expenditureApi = {
  add: (data: any) => apiClient.post("/expenditure/", data),
  dashboard: (candidateId: string, electionId: string) =>
    apiClient.get<ExpenditureDashboard>(`/expenditure/dashboard/${candidateId}/${electionId}`),
  list: (candidateId: string, electionId: string, params?: any) =>
    apiClient.get(`/expenditure/${candidateId}/${electionId}/entries`, { params }),
};

export const mccApi = {
  check: (data: any) => apiClient.post<MCCCheckResult>("/mcc/check", data),
  history: (electionId: string, params?: any) =>
    apiClient.get(`/mcc/election/${electionId}/history`, { params }),
  rules: () => apiClient.get("/mcc/rules"),
};

export const aiApi = {
  query: (query: string, context?: any, sessionId?: string) =>
    apiClient.post<AIQueryResponse>("/ai/query", { query, context, session_id: sessionId }),
  feedback: (queryLogId: string, wasHelpful: boolean) =>
    apiClient.post(`/ai/feedback/${queryLogId}`, null, { params: { was_helpful: wasHelpful } }),
};

export const knowledgeApi = {
  search: (data: { query: string; election_type?: string; limit?: number }) =>
    apiClient.post("/knowledge/search", data),
  listRules: (params?: any) => apiClient.get("/knowledge/rules", { params }),
  getRule: (id: string) => apiClient.get(`/knowledge/rules/${id}`),
  listArticles: (params?: any) => apiClient.get("/knowledge/articles", { params }),
};

export const judgmentsApi = {
  list: (params?: any) => apiClient.get("/judgments/", { params }),
  getLandmarks: () => apiClient.get("/judgments/landmarks"),
  get: (id: string) => apiClient.get(`/judgments/${id}`),
  getImpactByScenario: (scenario: string) =>
    apiClient.get("/judgments/impact/scenario", { params: { scenario } }),
};

export const dashboardApi = {
  consultant: () => apiClient.get("/dashboard/consultant"),
  notifications: (params?: any) => apiClient.get("/dashboard/notifications", { params }),
  markRead: (notificationId: string) =>
    apiClient.post(`/dashboard/notifications/${notificationId}/read`),
};

export const timelineApi = {
  get: (electionId: string) => apiClient.get<ElectionTimeline>(`/timeline/${electionId}`),
  exportIcs: (electionId: string) =>
    apiClient.get(`/timeline/${electionId}/export.ics`, { responseType: "blob" }),
};

export const nominationApi = {
  upload: (candidateId: string, electionId: string, formData: FormData) =>
    apiClient.post(`/nomination/upload/${candidateId}/${electionId}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  getReadiness: (candidateId: string, electionId: string) =>
    apiClient.get(`/nomination/${candidateId}/${electionId}`),
};

export const affidavitApi = {
  upload: (candidateId: string, electionId: string, formData: FormData) =>
    apiClient.post(`/affidavit/upload/${candidateId}/${electionId}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  getLatest: (candidateId: string, electionId: string) =>
    apiClient.get(`/affidavit/${candidateId}/${electionId}/latest`),
};

export const publicApi = {
  searchCandidates: (params?: any) => apiClient.get("/public/candidates", { params }),
  getCandidateDisclosures: (candidateId: string) =>
    apiClient.get(`/public/candidates/${candidateId}/disclosures`),
};
