"use client";

import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import {
  Card, CardHeader, CardTitle, CardContent,
  MCCBadge, Alert, LoadingCenter, EmptyState,
} from "@/components/ui/index";
import { mccApi, electionsApi } from "@/lib/api";
import toast from "react-hot-toast";

const ACTIVITY_TYPES = [
  "rally", "public_meeting", "door_to_door", "advertisement_print",
  "advertisement_digital", "advertisement_electronic", "social_media_post",
  "gift_distribution", "vehicle_procession", "press_conference",
  "government_event", "religious_event", "other",
];

export default function MCCCheckerPage() {
  const [electionId, setElectionId] = useState("");
  const [description, setDescription] = useState("");
  const [activityType, setActivityType] = useState("");
  const [location, setLocation] = useState("");
  const [result, setResult] = useState<any>(null);

  const { data: elections } = useQuery({
    queryKey: ["elections"],
    queryFn: () => electionsApi.list().then((r) => r.data),
  });

  const checkMutation = useMutation({
    mutationFn: () =>
      mccApi.check({
        election_id: electionId,
        activity_description: description,
        activity_type: activityType || undefined,
        activity_location: location || undefined,
      }).then((r) => r.data),
    onSuccess: (data) => {
      setResult(data);
      toast.success("MCC check completed");
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Check failed");
    },
  });

  const { data: rulesData } = useQuery({
    queryKey: ["mcc", "rules"],
    queryFn: () => mccApi.rules().then((r) => r.data),
  });

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>MCC Compliance Checker</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Module 8 — Model Code of Conduct · ECI Guidelines · State Rules
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader><CardTitle>Describe Activity</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="form-group">
                <label className="label">Election</label>
                <select
                  className="select"
                  value={electionId}
                  onChange={(e) => setElectionId(e.target.value)}
                >
                  <option value="">Select election…</option>
                  {elections?.map((e: any) => (
                    <option key={e.id} value={e.id}>
                      {e.name} ({e.year})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="label">Activity Type</label>
                <select
                  className="select"
                  value={activityType}
                  onChange={(e) => setActivityType(e.target.value)}
                >
                  <option value="">Select type…</option>
                  {ACTIVITY_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="label">Location</label>
                <input
                  className="input"
                  placeholder="e.g., Anantapur, Andhra Pradesh"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="label">Activity Description *</label>
                <textarea
                  className="input min-h-[120px] resize-none"
                  placeholder="Describe the campaign activity in detail. E.g., 'Distributing sarees to voters in the constituency two days before polling day'…"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                />
                <p className="text-xs text-gray-400 mt-1">
                  Be specific — the AI checks against ECI MCC guidelines.
                </p>
              </div>

              <button
                className="btn-primary w-full"
                onClick={() => checkMutation.mutate()}
                disabled={!electionId || description.length < 10 || checkMutation.isPending}
              >
                {checkMutation.isPending ? "Checking…" : "Check MCC Compliance"}
              </button>
            </CardContent>
          </Card>

          {/* Quick Examples */}
          <Card>
            <CardHeader><CardTitle>Try These Examples</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {[
                "Distributing sarees to voters one day before polling",
                "Using a government bus for campaign rally",
                "Publishing TV advertisement without MCMC pre-certification",
                "Organizing biryani distribution at a rally",
                "Conducting exit poll on counting day",
                "Campaign rally within 48 hours of polling",
              ].map((ex, i) => (
                <button
                  key={i}
                  className="w-full text-left text-xs bg-gray-50 hover:bg-red-50 hover:text-red-700 rounded-lg px-3 py-2 border border-transparent hover:border-red-200 transition-colors text-gray-600"
                  onClick={() => setDescription(ex)}
                >
                  {ex}
                </button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Result + Rules */}
        <div className="lg:col-span-2 space-y-4">
          {checkMutation.isPending && <LoadingCenter message="Checking against MCC guidelines…" />}

          {result && !checkMutation.isPending && (
            <>
              {/* Status Banner */}
              <Card>
                <CardContent className="py-5">
                  <div className="flex items-start gap-4">
                    <div className="text-4xl">
                      {result.mcc_status === "compliant"
                        ? "✅"
                        : result.mcc_status === "potential_violation"
                        ? "⚠️"
                        : "❌"}
                    </div>
                    <div className="flex-1">
                      <MCCBadge status={result.mcc_status} className="text-sm mb-2" />
                      {result.violation_category && (
                        <p className="text-sm font-medium text-gray-900 mt-1">
                          Category: {result.violation_category.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase())}
                        </p>
                      )}
                      {result.violation_details && (
                        <p className="text-sm text-gray-700 mt-1 leading-relaxed">
                          {result.violation_details}
                        </p>
                      )}
                      {result.ai_confidence_score != null && (
                        <p className="text-xs text-gray-400 mt-2">
                          AI Confidence: {(result.ai_confidence_score * 100).toFixed(0)}%
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recommended Action */}
              {result.recommended_action && (
                <Alert
                  variant={
                    result.mcc_status === "violation"
                      ? "error"
                      : result.mcc_status === "potential_violation"
                      ? "warning"
                      : "success"
                  }
                  title="Recommended Action"
                >
                  {result.recommended_action}
                </Alert>
              )}

              {/* Triggered MCC Rules */}
              {result.applicable_mcc_rules?.length > 0 && (
                <Card>
                  <CardHeader><CardTitle>Triggered MCC Rules</CardTitle></CardHeader>
                  <CardContent className="space-y-3">
                    {result.applicable_mcc_rules.map((rule: any, i: number) => (
                      <div
                        key={i}
                        className={`rounded-lg p-3 border ${
                          rule.severity === "critical"
                            ? "bg-red-50 border-red-200"
                            : rule.severity === "high"
                            ? "bg-orange-50 border-orange-200"
                            : "bg-yellow-50 border-yellow-200"
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-mono bg-white border rounded px-1.5 py-0.5">
                            {rule.id}
                          </span>
                          <span className="text-xs font-semibold text-gray-700">{rule.category}</span>
                          {rule.severity && (
                            <span className="text-xs font-medium text-red-600 ml-auto uppercase">
                              {rule.severity}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-700 leading-relaxed">{rule.rule}</p>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* ECI Citations */}
              {result.eci_circular_refs?.length > 0 && (
                <Card>
                  <CardHeader><CardTitle>Legal Citations</CardTitle></CardHeader>
                  <CardContent className="space-y-2">
                    {result.eci_circular_refs.map((ref: any, i: number) => (
                      <div key={i} className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                        <p className="text-xs font-semibold text-amber-900">⚖️ {ref.source}</p>
                        {ref.description && (
                          <p className="text-xs text-amber-700 mt-0.5">{ref.description}</p>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {!result && !checkMutation.isPending && (
            <>
              {/* MCC Rules Reference */}
              <Card>
                <CardHeader><CardTitle>MCC Rules Reference</CardTitle></CardHeader>
                <CardContent>
                  {rulesData?.rules ? (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {rulesData.rules.map((rule: any) => (
                        <div key={rule.id} className="border border-gray-200 rounded-lg p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded">
                              {rule.id}
                            </span>
                            <span className="text-xs font-semibold text-gray-700">{rule.category}</span>
                          </div>
                          <p className="text-xs text-gray-600 leading-relaxed">{rule.rule}</p>
                          <p className="text-[10px] text-gray-400 mt-1">Source: {rule.source}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState icon="📢" title="Describe an activity to check MCC compliance" />
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </AppShell>
  );
}
