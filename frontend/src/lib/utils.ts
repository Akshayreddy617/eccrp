// ECCRP Frontend Utility Helpers
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { RiskLevel, EligibilityStatus, MCCStatus, ElectionType } from "@/lib/api";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ── Risk Level Helpers ────────────────────────────────────────────────────

export const RISK_COLORS: Record<RiskLevel, string> = {
  low:      "text-green-700 bg-green-50 border-green-200",
  medium:   "text-yellow-700 bg-yellow-50 border-yellow-200",
  high:     "text-orange-700 bg-orange-50 border-orange-200",
  critical: "text-red-700 bg-red-50 border-red-200",
};

export const RISK_DOT: Record<RiskLevel, string> = {
  low:      "bg-green-500",
  medium:   "bg-yellow-500",
  high:     "bg-orange-500",
  critical: "bg-red-500",
};

export const RISK_ICONS: Record<RiskLevel, string> = {
  low:      "✅",
  medium:   "🟡",
  high:     "🔴",
  critical: "⛔",
};

export const ELIGIBILITY_COLORS: Record<EligibilityStatus, string> = {
  eligible:             "text-green-700 bg-green-50 border-green-200",
  potentially_eligible: "text-yellow-700 bg-yellow-50 border-yellow-200",
  high_risk:            "text-orange-700 bg-orange-50 border-orange-200",
  disqualified:         "text-red-700 bg-red-50 border-red-200",
};

export const MCC_COLORS: Record<MCCStatus, string> = {
  compliant:           "text-green-700 bg-green-50 border-green-200",
  potential_violation: "text-yellow-700 bg-yellow-50 border-yellow-200",
  violation:           "text-red-700 bg-red-50 border-red-200",
};

export const ELECTION_TYPE_LABELS: Record<ElectionType, string> = {
  lok_sabha:            "Lok Sabha",
  rajya_sabha:          "Rajya Sabha",
  legislative_assembly: "State Legislative Assembly",
  legislative_council:  "State Legislative Council",
  gram_panchayat:       "Gram Panchayat",
  mandal_parishad:      "Mandal Parishad",
  zilla_parishad:       "Zilla Parishad",
  municipality:         "Municipality",
  municipal_corporation:"Municipal Corporation",
};

// ── Format Helpers ────────────────────────────────────────────────────────

export function formatCurrency(amount: number | undefined | null): string {
  if (amount == null) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatScore(score: number | undefined | null): string {
  if (score == null) return "—";
  return `${score.toFixed(1)}/100`;
}

export function formatPercent(pct: number | undefined | null): string {
  if (pct == null) return "—";
  return `${pct.toFixed(1)}%`;
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
  });
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function daysUntil(dateStr: string | null | undefined): number | null {
  if (!dateStr) return null;
  const diff = new Date(dateStr).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / 86400000));
}

// ── Score Bar Color ───────────────────────────────────────────────────────

export function scoreBarColor(score: number): string {
  if (score >= 80) return "bg-green-500";
  if (score >= 60) return "bg-yellow-500";
  if (score >= 40) return "bg-orange-500";
  return "bg-red-500";
}

export function riskScoreBarColor(riskScore: number): string {
  if (riskScore <= 20) return "bg-green-500";
  if (riskScore <= 40) return "bg-yellow-500";
  if (riskScore <= 70) return "bg-orange-500";
  return "bg-red-500";
}

// ── Label helpers ─────────────────────────────────────────────────────────

export function labelEligibility(status: EligibilityStatus): string {
  return {
    eligible:             "Eligible",
    potentially_eligible: "Potentially Eligible",
    high_risk:            "High Risk",
    disqualified:         "Disqualified",
  }[status] ?? status;
}

export function labelRisk(level: RiskLevel): string {
  return { low: "Low", medium: "Medium", high: "High", critical: "Critical" }[level] ?? level;
}

export function labelMCC(status: MCCStatus): string {
  return {
    compliant:           "Compliant",
    potential_violation: "Potential Violation",
    violation:           "Violation",
  }[status] ?? status;
}

// ── Boolean check icon ────────────────────────────────────────────────────

export function checkIcon(value: boolean | null | undefined): string {
  if (value === true)  return "✅";
  if (value === false) return "❌";
  return "⏳";
}
