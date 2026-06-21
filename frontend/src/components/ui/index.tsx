// ECCRP Reusable UI Components
"use client";

import React from "react";
import { cn, RISK_COLORS, ELIGIBILITY_COLORS, MCC_COLORS, scoreBarColor, riskScoreBarColor } from "@/lib/utils";
import { RiskLevel, EligibilityStatus, MCCStatus } from "@/lib/api";

// ── Badge ──────────────────────────────────────────────────────────────────

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "outline";
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
      variant === "outline" ? "bg-transparent" : "",
      className
    )}>
      {children}
    </span>
  );
}

// ── Risk Badge ─────────────────────────────────────────────────────────────

export function RiskBadge({ level, className }: { level: RiskLevel | string; className?: string }) {
  const label = { low: "Low Risk", medium: "Medium Risk", high: "High Risk", critical: "Critical Risk" }[level] ?? level;
  return (
    <Badge className={cn(RISK_COLORS[level as RiskLevel] ?? "text-gray-600 bg-gray-50 border-gray-200", className)}>
      {label}
    </Badge>
  );
}

// ── Eligibility Badge ──────────────────────────────────────────────────────

export function EligibilityBadge({ status, className }: { status: EligibilityStatus | string; className?: string }) {
  const label = {
    eligible:             "Eligible",
    potentially_eligible: "Potentially Eligible",
    high_risk:            "High Risk",
    disqualified:         "Disqualified",
  }[status] ?? status;
  return (
    <Badge className={cn(ELIGIBILITY_COLORS[status as EligibilityStatus] ?? "text-gray-600 bg-gray-50 border-gray-200", className)}>
      {label}
    </Badge>
  );
}

// ── MCC Badge ──────────────────────────────────────────────────────────────

export function MCCBadge({ status, className }: { status: MCCStatus | string; className?: string }) {
  const label = {
    compliant:           "✅ Compliant",
    potential_violation: "⚠️ Potential Violation",
    violation:           "❌ Violation",
  }[status] ?? status;
  return (
    <Badge className={cn(MCC_COLORS[status as MCCStatus] ?? "text-gray-600 bg-gray-50 border-gray-200", className)}>
      {label}
    </Badge>
  );
}

// ── Score Bar ──────────────────────────────────────────────────────────────

interface ScoreBarProps {
  score: number;
  label?: string;
  showValue?: boolean;
  isRiskScore?: boolean;
  size?: "sm" | "md" | "lg";
}

export function ScoreBar({ score, label, showValue = true, isRiskScore = false, size = "md" }: ScoreBarProps) {
  const pct = Math.min(100, Math.max(0, score));
  const colorFn = isRiskScore ? riskScoreBarColor : scoreBarColor;

  const heights = { sm: "h-1.5", md: "h-2.5", lg: "h-4" };

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-xs text-gray-500">{label}</span>}
          {showValue && (
            <span className="text-xs font-semibold text-gray-700">{pct.toFixed(1)}</span>
          )}
        </div>
      )}
      <div className={cn("w-full bg-gray-200 rounded-full", heights[size])}>
        <div
          className={cn("rounded-full transition-all duration-500", heights[size], colorFn(isRiskScore ? pct : pct))}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ── Check Row ──────────────────────────────────────────────────────────────

export function CheckRow({ label, passed, details }: { label: string; passed: boolean | null | undefined; details?: string }) {
  const icon = passed === true ? "✅" : passed === false ? "❌" : "⏳";
  const textColor = passed === true ? "text-green-700" : passed === false ? "text-red-700" : "text-gray-500";
  return (
    <div className="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0">
      <span className="text-base mt-0.5">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className={cn("text-sm font-medium", textColor)}>{label}</p>
        {details && <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{details}</p>}
      </div>
    </div>
  );
}

// ── Card ──────────────────────────────────────────────────────────────────

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("bg-white rounded-xl border border-gray-200 shadow-sm", className)}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("px-6 py-4 border-b border-gray-100", className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h3 className={cn("text-base font-semibold text-gray-900", className)}>{children}</h3>;
}

export function CardContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("px-6 py-4", className)}>{children}</div>;
}

// ── Alert ──────────────────────────────────────────────────────────────────

type AlertVariant = "info" | "warning" | "error" | "success";
const ALERT_STYLES: Record<AlertVariant, string> = {
  info:    "bg-blue-50 border-blue-200 text-blue-800",
  warning: "bg-yellow-50 border-yellow-200 text-yellow-800",
  error:   "bg-red-50 border-red-200 text-red-800",
  success: "bg-green-50 border-green-200 text-green-800",
};

export function Alert({ variant = "info", title, children }: {
  variant?: AlertVariant; title?: string; children: React.ReactNode;
}) {
  return (
    <div className={cn("rounded-lg border p-4", ALERT_STYLES[variant])}>
      {title && <p className="font-semibold text-sm mb-1">{title}</p>}
      <div className="text-sm">{children}</div>
    </div>
  );
}

// ── Loading Spinner ────────────────────────────────────────────────────────

export function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizes = { sm: "w-4 h-4", md: "w-6 h-6", lg: "w-10 h-10" };
  return (
    <div className={cn("animate-spin rounded-full border-2 border-gray-200 border-t-blue-600", sizes[size])} />
  );
}

export function LoadingCenter({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <Spinner size="lg" />
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  );
}

// ── Empty State ────────────────────────────────────────────────────────────

export function EmptyState({ icon, title, description, action }: {
  icon?: React.ReactNode; title: string; description?: string; action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center px-4">
      {icon && <div className="text-4xl mb-2">{icon}</div>}
      <p className="text-base font-semibold text-gray-900">{title}</p>
      {description && <p className="text-sm text-gray-500 max-w-sm">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

// ── Stats Card ────────────────────────────────────────────────────────────

export function StatCard({ label, value, sub, color = "blue" }: {
  label: string; value: string | number; sub?: string; color?: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={cn("text-2xl font-bold mt-1", `text-${color}-600`)}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

// ── Countdown Badge ────────────────────────────────────────────────────────

export function CountdownBadge({ days, label }: { days: number | null | undefined; label: string }) {
  if (days == null) return null;
  const urgent = days <= 3;
  const warning = days <= 7;
  return (
    <div className={cn(
      "rounded-lg border px-3 py-2 text-center",
      urgent ? "bg-red-50 border-red-200" : warning ? "bg-yellow-50 border-yellow-200" : "bg-blue-50 border-blue-200"
    )}>
      <p className={cn("text-xl font-bold", urgent ? "text-red-700" : warning ? "text-yellow-700" : "text-blue-700")}>
        {days}
      </p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}

// ── Legal Citation Card ────────────────────────────────────────────────────

export function LegalCitationCard({ citation }: { citation: any }) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
      <div className="flex items-start gap-2">
        <span className="text-amber-600 text-sm">⚖️</span>
        <div>
          <p className="text-xs font-semibold text-amber-900">
            {citation.source_type?.replace(/_/g, " ").toUpperCase()} — {citation.section_number || citation.section || ""}
          </p>
          <p className="text-xs text-amber-700 mt-0.5">{citation.title}</p>
        </div>
      </div>
    </div>
  );
}

// ── Judgment Card ──────────────────────────────────────────────────────────

export function JudgmentCard({ judgment }: { judgment: any }) {
  return (
    <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
      <p className="text-xs font-semibold text-purple-900">{judgment.case_name}</p>
      {judgment.citation && (
        <p className="text-xs text-purple-600 mt-0.5">{judgment.citation}</p>
      )}
      {judgment.relevance && (
        <p className="text-xs text-purple-700 mt-1">{judgment.relevance}</p>
      )}
    </div>
  );
}

// ── Section Divider ───────────────────────────────────────────────────────

export function SectionDivider({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-3 my-4">
      <div className="flex-1 h-px bg-gray-200" />
      <span className="text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap">{title}</span>
      <div className="flex-1 h-px bg-gray-200" />
    </div>
  );
}
