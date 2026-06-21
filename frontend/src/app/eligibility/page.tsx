"use client";

import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import {
  Card, CardHeader, CardTitle, CardContent,
  EligibilityBadge, RiskBadge, ScoreBar, CheckRow,
  LegalCitationCard, JudgmentCard, Alert, LoadingCenter,
} from "@/components/ui/index";
import { eligibilityApi, candidatesApi, ElectionType } from "@/lib/api";
import { ELECTION_TYPE_LABELS, formatDate } from "@/lib/utils";
import toast from "react-hot-toast";

const ELECTION_TYPES = Object.entries(ELECTION_TYPE_LABELS) as [ElectionType, string][];

export default function EligibilityPage() {
  const [candidateId, setCandidateId] = useState("");
  const [electionType, setElectionType] = useState<ElectionType>("lok_sabha");
  const [result, setResult] = useState<any>(null);

  const { data: candidates } = useQuery({
    queryKey: ["candidates"],
    queryFn: () => candidatesApi.list().then((r) => r.data),
  });

  const checkMutation = useMutation({
    mutationFn: () =>
      eligibilityApi.check({ candidate_id: candidateId, election_type: electionType }).then((r) => r.data),
    onSuccess: (data) => {
      setResult(data);
      toast.success("Eligibility check completed");
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Check failed");
    },
  });

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Eligibility Assessment</h1>
          <p className="text-sm text-gray-500 mt-0.5">Module 2 — Constitution of India + RPA 1951</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader><CardTitle>Run Eligibility Check</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="form-group">
                <label className="label">Candidate</label>
                <select
                  className="select"
                  value={candidateId}
                  onChange={(e) => setCandidateId(e.target.value)}
                >
                  <option value="">Select candidate…</option>
                  {candidates?.map((c: any) => (
                    <option key={c.id} value={c.id}>{c.full_name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="label">Election Type</label>
                <select
                  className="select"
                  value={electionType}
                  onChange={(e) => setElectionType(e.target.value as ElectionType)}
                >
                  {ELECTION_TYPES.map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>

              <button
                className="btn-primary w-full"
                onClick={() => checkMutation.mutate()}
                disabled={!candidateId || checkMutation.isPending}
              >
                {checkMutation.isPending ? "Checking…" : "Run Eligibility Check"}
              </button>

              <Alert variant="info">
                <p className="text-xs">
                  Checks 10+ eligibility criteria including citizenship, age, electoral roll
                  registration, office of profit, convictions, and more.
                </p>
              </Alert>
            </CardContent>
          </Card>

          {/* Legal Basis Reference */}
          <Card className="mt-4">
            <CardHeader><CardTitle>Legal Basis</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {[
                { ref: "Article 84", desc: "Qualifications for Parliament" },
                { ref: "Article 102", desc: "Disqualifications for Parliament" },
                { ref: "Article 173", desc: "Qualifications for State Legislature" },
                { ref: "Article 191", desc: "Disqualifications for State Legislature" },
                { ref: "Section 8", desc: "Conviction disqualification (RPA 1951)" },
                { ref: "Section 9A", desc: "Government contracts (RPA 1951)" },
                { ref: "Section 10A", desc: "Expenditure violations (RPA 1951)" },
              ].map((item) => (
                <div key={item.ref} className="flex items-start gap-2">
                  <span className="text-xs font-mono bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded flex-shrink-0">
                    {item.ref}
                  </span>
                  <span className="text-xs text-gray-500">{item.desc}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Result Panel */}
        <div className="lg:col-span-2">
          {checkMutation.isPending && <LoadingCenter message="Running eligibility checks…" />}

          {result && !checkMutation.isPending && (
            <div className="space-y-4">
              {/* Status Header */}
              <Card>
                <CardContent className="py-5">
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Eligibility Status</p>
                      <EligibilityBadge status={result.eligibility_status} className="text-sm px-3 py-1" />
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500 mb-1">Eligibility Score</p>
                      <p className="text-3xl font-bold text-gray-900">
                        {result.eligibility_score?.toFixed(0)}
                        <span className="text-base text-gray-400">/100</span>
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500 mb-1">Risk Score</p>
                      <p className="text-3xl font-bold text-orange-600">
                        {result.risk_score?.toFixed(0)}
                        <span className="text-base text-gray-400">/100</span>
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Risk Level</p>
                      <RiskBadge level={result.risk_level} className="text-sm px-3 py-1" />
                    </div>
                  </div>

                  {/* Score bars */}
                  <div className="mt-4 space-y-2">
                    <ScoreBar score={result.eligibility_score} label="Eligibility Score" />
                    <ScoreBar score={result.risk_score} label="Risk Score" isRiskScore />
                  </div>
                </CardContent>
              </Card>

              {/* Individual Checks */}
              <Card>
                <CardHeader><CardTitle>Check-by-Check Results</CardTitle></CardHeader>
                <CardContent className="pt-0">
                  <CheckRow label="Citizenship (Article 84/173)" passed={result.citizenship_check} />
                  <CheckRow
                    label="Age Requirement"
                    passed={result.age_check}
                    details={result.age_check_details}
                  />
                  <CheckRow
                    label="Electoral Roll Registration (Section 19 RPA 1950)"
                    passed={result.electoral_roll_check}
                    details={result.electoral_roll_check ? undefined : "Not registered as voter. Must register before nomination."}
                  />
                  <CheckRow
                    label="No Office of Profit (Article 102/191)"
                    passed={result.office_of_profit_check}
                  />
                  <CheckRow label="No Government Contracts (Section 9A)" passed={result.government_contract_check} />
                  <CheckRow label="Not Insolvent/Bankrupt (Section 9)" passed={result.insolvency_check} />
                  <CheckRow
                    label="No Disqualifying Conviction (Section 8)"
                    passed={result.conviction_check}
                    details={result.conviction_details?.length
                      ? `${result.conviction_details.length} disqualifying conviction(s) found`
                      : undefined}
                  />
                  <CheckRow label="Expenditure Compliance (Section 10A)" passed={result.election_expenditure_violation_check} />
                  <CheckRow label="Reservation Eligibility" passed={result.reservation_eligibility_check} />
                  <CheckRow label="Local Body Eligibility" passed={result.local_body_eligibility_check} />
                </CardContent>
              </Card>

              {/* Recommendations */}
              {result.recommendations?.length > 0 && (
                <Card>
                  <CardHeader><CardTitle>Priority Recommendations</CardTitle></CardHeader>
                  <CardContent className="space-y-3">
                    {result.recommendations.map((rec: any, i: number) => (
                      <div
                        key={i}
                        className={`rounded-lg p-3 border ${
                          rec.priority === "CRITICAL"
                            ? "bg-red-50 border-red-200"
                            : rec.priority === "HIGH"
                            ? "bg-orange-50 border-orange-200"
                            : "bg-blue-50 border-blue-200"
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-white border">
                            {rec.priority}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{rec.action}</p>
                            <p className="text-xs text-gray-500 mt-0.5">{rec.legal_basis}</p>
                            {rec.timeline && (
                              <p className="text-xs text-gray-400 mt-0.5">⏰ {rec.timeline}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Applicable Provisions */}
              {result.applicable_articles?.length > 0 && (
                <Card>
                  <CardHeader><CardTitle>Applicable Constitutional Provisions</CardTitle></CardHeader>
                  <CardContent className="space-y-2">
                    {result.applicable_articles.map((art: any, i: number) => (
                      <div key={i} className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                        <p className="text-xs font-bold text-amber-900">Article {art.article}</p>
                        <p className="text-xs text-amber-800 font-medium mt-0.5">{art.title}</p>
                        {art.key_points && (
                          <ul className="text-xs text-amber-700 mt-1 list-disc list-inside space-y-0.5">
                            {art.key_points.map((pt: string, j: number) => (
                              <li key={j}>{pt}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Judgments */}
              {result.applicable_judgments?.length > 0 && (
                <Card>
                  <CardHeader><CardTitle>Relevant Supreme Court Judgments</CardTitle></CardHeader>
                  <CardContent className="space-y-2">
                    {result.applicable_judgments.map((j: any, i: number) => (
                      <JudgmentCard key={i} judgment={{ ...j, case_name: j.case, citation: j.citation }} />
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Legal Explanation */}
              {result.legal_explanation && (
                <Card>
                  <CardHeader><CardTitle>Detailed Legal Explanation</CardTitle></CardHeader>
                  <CardContent>
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                      {result.legal_explanation}
                    </pre>
                  </CardContent>
                </Card>
              )}

              <p className="text-xs text-gray-400 text-center">
                Generated {formatDate(result.created_at)} · For informational purposes only · Consult qualified election counsel
              </p>
            </div>
          )}

          {!result && !checkMutation.isPending && (
            <div className="flex items-center justify-center h-64 text-center">
              <div>
                <p className="text-4xl mb-3">✅</p>
                <p className="text-gray-600 font-medium">Select a candidate and election type</p>
                <p className="text-sm text-gray-400 mt-1">Run the eligibility check to see results</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
