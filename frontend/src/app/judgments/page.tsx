"use client";

import React, { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import {
  Card, CardHeader, CardTitle, CardContent,
  Badge, LoadingCenter, EmptyState,
} from "@/components/ui/index";
import { judgmentsApi } from "@/lib/api";
import toast from "react-hot-toast";

export default function JudgmentsPage() {
  const [scenario, setScenario] = useState("");
  const [impactResult, setImpactResult] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"landmarks" | "impact">("landmarks");

  const { data: landmarksData, isLoading } = useQuery({
    queryKey: ["judgments", "landmarks"],
    queryFn: () => judgmentsApi.getLandmarks().then((r) => r.data),
  });

  const impactMutation = useMutation({
    mutationFn: () => judgmentsApi.getImpactByScenario(scenario).then((r) => r.data),
    onSuccess: (data) => setImpactResult(data),
    onError: () => toast.error("Failed to get judgment impact"),
  });

  const TABS = [
    { key: "landmarks", label: "Landmark Judgments" },
    { key: "impact", label: "Judgment Impact Engine" },
  ] as const;

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Supreme Court Judgment Library</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Modules 10 & 11 — Landmark cases + Judgment Impact Engine
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6 w-fit">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`px-4 py-2 text-sm rounded-md font-medium transition-colors ${
              activeTab === tab.key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Landmark Judgments */}
      {activeTab === "landmarks" && (
        <>
          {isLoading ? (
            <LoadingCenter />
          ) : (
            <div className="space-y-4">
              {landmarksData?.judgments?.map((j: any, i: number) => (
                <Card key={i}>
                  <CardContent className="py-5">
                    <div className="flex flex-wrap items-start gap-3 mb-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2 flex-wrap">
                          {j.case_name}
                          {j.is_landmark && (
                            <Badge className="bg-purple-100 text-purple-700 border-purple-200">
                              ⭐ Landmark
                            </Badge>
                          )}
                        </h3>
                        <p className="text-sm text-purple-600 font-medium mt-0.5">
                          {j.citation} · {j.court} · {j.year}
                        </p>
                        {j.bench_composition && (
                          <p className="text-xs text-gray-400">{j.bench_composition}</p>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Issue</p>
                        <p className="text-sm text-gray-700">{j.issue}</p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Impact</p>
                        <p className="text-sm text-gray-700">{j.impact_summary}</p>
                      </div>
                    </div>

                    <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <p className="text-xs font-semibold text-amber-900 mb-1">Ratio Decidendi</p>
                      <p className="text-xs text-amber-800 leading-relaxed">{j.ratio_decidendi}</p>
                    </div>

                    {j.relevant_sections?.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {j.relevant_sections.map((s: any, si: number) => (
                          <span key={si} className="text-xs font-mono bg-gray-100 text-gray-700 px-2 py-0.5 rounded border">
                            {s.section || s.article
                              ? `${s.article ? "Art." : "Sec."} ${s.article || s.section} — ${s.act}`
                              : JSON.stringify(s)}
                          </span>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* Judgment Impact Engine */}
      {activeTab === "impact" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Module 11 — Judgment Impact Engine</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-500">
                Describe your situation and the engine maps it to:
                Applicable Law → Relevant Judgment → Compliance Requirement → Recommended Action.
              </p>

              <textarea
                className="input min-h-[100px] resize-none"
                placeholder="Describe the candidate's situation… e.g., 'The candidate has a pending criminal case under IPC Section 302' or 'The candidate owns property worth ₹5 crore' or 'The candidate is spending heavily on campaign vehicles'"
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
              />

              <div className="flex flex-wrap gap-2">
                {[
                  "Criminal case pending under IPC",
                  "Property worth crores — disclosure question",
                  "Campaign expenditure near limit",
                  "Holds office of profit in PSU",
                ].map((ex) => (
                  <button
                    key={ex}
                    className="text-xs bg-gray-100 hover:bg-blue-50 text-gray-600 hover:text-blue-700 px-2.5 py-1 rounded-full border border-transparent hover:border-blue-200 transition-colors"
                    onClick={() => setScenario(ex)}
                  >
                    {ex}
                  </button>
                ))}
              </div>

              <button
                className="btn-primary"
                onClick={() => impactMutation.mutate()}
                disabled={scenario.length < 10 || impactMutation.isPending}
              >
                {impactMutation.isPending ? "Analyzing…" : "Get Judgment Impact"}
              </button>
            </CardContent>
          </Card>

          {impactResult.length > 0 && (
            <div className="space-y-4">
              {impactResult.map((impact: any, i: number) => (
                <Card key={i}>
                  <CardContent className="py-5">
                    <div className="space-y-4">
                      {/* Chain visualization */}
                      <div className="flex items-start gap-0 overflow-x-auto pb-2">
                        {[
                          { label: "Scenario", value: impact.scenario?.slice(0, 60) + "…", icon: "👤" },
                          { label: "Applicable Law", value: `${impact.applicable_law?.section} ${impact.applicable_law?.act}`, icon: "📖" },
                          { label: "Judgment", value: impact.relevant_judgment?.case_name, icon: "⚖️" },
                          { label: "Requirement", value: impact.compliance_requirement?.slice(0, 80) + "…", icon: "✅" },
                        ].map((step, si) => (
                          <React.Fragment key={si}>
                            <div className="flex-1 min-w-[140px] text-center">
                              <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-lg mx-auto mb-2">
                                {step.icon}
                              </div>
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                                {step.label}
                              </p>
                              <p className="text-xs text-gray-700">{step.value || "—"}</p>
                            </div>
                            {si < 3 && (
                              <div className="flex items-center justify-center w-8 mt-4 flex-shrink-0">
                                <span className="text-gray-300 text-xl">→</span>
                              </div>
                            )}
                          </React.Fragment>
                        ))}
                      </div>

                      {/* Full compliance requirement */}
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <p className="text-xs font-semibold text-blue-900 mb-1">Compliance Requirement</p>
                        <p className="text-sm text-blue-800">{impact.compliance_requirement}</p>
                      </div>

                      {/* Recommended action */}
                      {impact.recommended_action && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                          <p className="text-xs font-semibold text-green-900 mb-1">💡 Recommended Action</p>
                          <p className="text-sm text-green-800">{impact.recommended_action}</p>
                        </div>
                      )}

                      {/* Judgment box */}
                      {impact.relevant_judgment && (
                        <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                          <p className="text-xs font-semibold text-purple-900">
                            ⚖️ {impact.relevant_judgment.case_name}
                          </p>
                          {impact.relevant_judgment.citation && (
                            <p className="text-xs text-purple-600 mt-0.5">{impact.relevant_judgment.citation} · {impact.relevant_judgment.year}</p>
                          )}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
