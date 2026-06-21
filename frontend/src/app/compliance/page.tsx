"use client";
import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import { Card, CardHeader, CardTitle, CardContent, RiskBadge, ScoreBar, Alert, LoadingCenter } from "@/components/ui/index";
import { complianceApi, candidatesApi, electionsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";
import toast from "react-hot-toast";

export default function CompliancePage() {
  const [candidateId, setCandidateId] = useState("");
  const [electionId, setElectionId] = useState("");
  const [result, setResult] = useState<any>(null);

  const { data: candidates } = useQuery({ queryKey: ["candidates"], queryFn: () => candidatesApi.list().then(r => r.data) });
  const { data: elections } = useQuery({ queryKey: ["elections"], queryFn: () => electionsApi.list().then(r => r.data) });

  const assessMutation = useMutation({
    mutationFn: () => complianceApi.assess(candidateId, electionId || undefined).then(r => r.data),
    onSuccess: data => { setResult(data); toast.success("Risk assessment complete"); },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Assessment failed"),
  });

  const RISK_DIMENSIONS = result ? [
    { subject: "Eligibility", score: result.eligibility_risk_score ?? 0, fullMark: 100 },
    { subject: "Disclosure", score: result.disclosure_risk_score ?? 0, fullMark: 100 },
    { subject: "Legal", score: result.legal_risk_score ?? 0, fullMark: 100 },
    { subject: "Expenditure", score: result.expenditure_risk_score ?? 0, fullMark: 100 },
    { subject: "MCC", score: result.mcc_risk_score ?? 0, fullMark: 100 },
  ] : [];

  const RISK_ROWS = result ? [
    { label: "Eligibility Risk", level: result.eligibility_risk, score: result.eligibility_risk_score, factors: result.eligibility_risk_factors },
    { label: "Disclosure Risk", level: result.disclosure_risk, score: result.disclosure_risk_score, factors: result.disclosure_risk_factors },
    { label: "Legal Risk", level: result.legal_risk, score: result.legal_risk_score, factors: result.legal_risk_factors },
    { label: "Expenditure Risk", level: result.expenditure_risk, score: result.expenditure_risk_score, factors: result.expenditure_risk_factors },
    { label: "MCC Risk", level: result.mcc_risk, score: result.mcc_risk_score, factors: result.mcc_risk_factors },
  ] : [];

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Compliance Risk Engine</h1>
          <p className="text-sm text-gray-500 mt-0.5">Module 5 — Aggregated risk across all compliance dimensions</p>
        </div>
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="label">Candidate</label>
          <select className="select" value={candidateId} onChange={e => setCandidateId(e.target.value)}>
            <option value="">Select candidate…</option>
            {candidates?.map((c: any) => <option key={c.id} value={c.id}>{c.full_name}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Election (optional)</label>
          <select className="select" value={electionId} onChange={e => setElectionId(e.target.value)}>
            <option value="">All elections</option>
            {elections?.map((e: any) => <option key={e.id} value={e.id}>{e.name} ({e.year})</option>)}
          </select>
        </div>
        <div className="flex items-end">
          <button className="btn-primary w-full" onClick={() => assessMutation.mutate()} disabled={!candidateId || assessMutation.isPending}>
            {assessMutation.isPending ? "Assessing…" : "Generate Risk Assessment"}
          </button>
        </div>
      </div>

      {assessMutation.isPending && <LoadingCenter message="Aggregating risk signals…" />}

      {result && !assessMutation.isPending && (
        <div className="space-y-6">
          {/* Executive Summary */}
          <Card>
            <CardContent className="py-5">
              <div className="flex items-start justify-between gap-6 flex-wrap">
                <div className="flex-1">
                  <p className="text-xs text-gray-500 mb-1">Overall Risk Level</p>
                  <RiskBadge level={result.overall_risk} className="text-sm px-3 py-1.5 mb-3" />
                  <p className="text-sm text-gray-700 leading-relaxed">{result.executive_summary}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-400 mb-1">Risk Score</p>
                  <p className="text-4xl font-bold text-gray-900">{result.overall_risk_score?.toFixed(0)}<span className="text-lg text-gray-400">/100</span></p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Radar Chart */}
            <Card>
              <CardHeader><CardTitle>Risk Profile Radar</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={RISK_DIMENSIONS}>
                    <PolarGrid stroke="#e5e7eb" />
                    <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: "#6b7280" }} />
                    <Radar name="Risk Score" dataKey="score" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} strokeWidth={2} />
                    <Tooltip formatter={(v: any) => `${v.toFixed(1)}/100`} />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Score Breakdown */}
            <Card>
              <CardHeader><CardTitle>Risk Dimension Breakdown</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {RISK_ROWS.map((row) => (
                  <div key={row.label}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-700">{row.label}</span>
                      <div className="flex items-center gap-2">
                        {row.level && <RiskBadge level={row.level} />}
                        <span className="text-xs text-gray-500">{row.score?.toFixed(1)}</span>
                      </div>
                    </div>
                    <ScoreBar score={row.score ?? 0} isRiskScore size="sm" showValue={false} />
                    {row.factors?.length > 0 && (
                      <div className="mt-1 space-y-0.5">
                        {row.factors.slice(0, 2).map((f: any, fi: number) => (
                          <p key={fi} className="text-xs text-gray-400">• {f.risk ?? f.action ?? JSON.stringify(f)}</p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Priority Actions */}
          {result.priority_actions?.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Priority Actions</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {result.priority_actions.map((action: any, i: number) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <span className="text-orange-500 flex-shrink-0 mt-0.5">⚡</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{action.action ?? action.risk ?? JSON.stringify(action)}</p>
                      {action.legal_basis && <p className="text-xs text-gray-500 mt-0.5">{action.legal_basis}</p>}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <p className="text-xs text-gray-400 text-center">
            Generated {formatDate(result.created_at)} · For informational purposes only
          </p>
        </div>
      )}

      {!result && !assessMutation.isPending && (
        <div className="flex items-center justify-center h-48 text-center">
          <div>
            <p className="text-3xl mb-2">⚠️</p>
            <p className="text-gray-500">Select a candidate and run assessment to see risk profile</p>
          </div>
        </div>
      )}
    </AppShell>
  );
}
