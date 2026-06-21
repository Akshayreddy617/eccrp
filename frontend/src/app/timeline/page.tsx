"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import {
  Card, CardHeader, CardTitle, CardContent,
  CountdownBadge, Alert, LoadingCenter,
} from "@/components/ui/index";
import { timelineApi, electionsApi } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import toast from "react-hot-toast";

export default function TimelinePage() {
  const [selectedElection, setSelectedElection] = useState("");

  const { data: elections } = useQuery({
    queryKey: ["elections"],
    queryFn: () => electionsApi.list().then((r) => r.data),
  });

  const { data: timeline, isLoading } = useQuery({
    queryKey: ["timeline", selectedElection],
    queryFn: () => timelineApi.get(selectedElection).then((r) => r.data),
    enabled: !!selectedElection,
  });

  async function downloadICS() {
    try {
      const resp = await timelineApi.exportIcs(selectedElection);
      const url = URL.createObjectURL(resp.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "election-timeline.ics";
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Calendar file downloaded");
    } catch {
      toast.error("Download failed");
    }
  }

  const CATEGORY_STYLES: Record<string, string> = {
    deadline:  "border-red-300 bg-red-50",
    milestone: "border-blue-300 bg-blue-50",
    nomination:"border-purple-300 bg-purple-50",
    action:    "border-yellow-300 bg-yellow-50",
    campaign:  "border-green-300 bg-green-50",
  };

  const CATEGORY_DOT: Record<string, string> = {
    deadline:  "bg-red-500",
    milestone: "bg-blue-500",
    nomination:"bg-purple-500",
    action:    "bg-yellow-500",
    campaign:  "bg-green-500",
  };

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Election Timeline Planner</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Module 6 — Nomination, MCC, polling, counting & expenditure deadlines
          </p>
        </div>
        <button className="btn-secondary" onClick={downloadICS} disabled={!timeline}>
          📅 Export to Calendar (.ics)
        </button>
      </div>

      {/* Election selector */}
      <div className="mb-6">
        <label className="label">Select Election</label>
        <select
          className="select max-w-sm"
          value={selectedElection}
          onChange={(e) => setSelectedElection(e.target.value)}
        >
          <option value="">Choose an election…</option>
          {elections?.map((e: any) => (
            <option key={e.id} value={e.id}>{e.name} ({e.year})</option>
          ))}
        </select>
      </div>

      {!selectedElection && (
        <div className="flex items-center justify-center h-48 text-center">
          <div>
            <p className="text-3xl mb-2">📅</p>
            <p className="text-gray-500">Select an election to view the compliance timeline</p>
          </div>
        </div>
      )}

      {selectedElection && isLoading && <LoadingCenter message="Building timeline…" />}

      {timeline && !isLoading && (
        <div className="space-y-6">
          {/* Election Info */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white border border-gray-200 rounded-xl p-4 col-span-2">
              <p className="text-xs text-gray-500">Election</p>
              <p className="font-semibold text-gray-900">{timeline.election.name}</p>
              <p className="text-sm text-gray-500 capitalize">
                {timeline.election.election_type?.replace(/_/g, " ")} · {timeline.election.year}
              </p>
              {timeline.election.expenditure_limit && (
                <p className="text-xs text-gray-400 mt-1">
                  Expenditure Limit: {formatCurrency(timeline.election.expenditure_limit)}
                </p>
              )}
            </div>
            <CountdownBadge
              days={timeline.countdown.days_to_polling}
              label="Days to Polling"
            />
            <CountdownBadge
              days={timeline.countdown.days_to_nomination_deadline}
              label="Days to Nomination"
            />
          </div>

          {/* Key Dates Grid */}
          <Card>
            <CardHeader><CardTitle>Key Dates</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(timeline.key_dates).map(([key, val]) => (
                  <div key={key} className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-400 mb-1 capitalize">{key.replace(/_/g, " ")}</p>
                    <p className="text-sm font-semibold text-gray-900">{val as string ?? "—"}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Critical Deadlines */}
          {timeline.deadlines.length > 0 && (
            <div>
              <h2 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <span className="text-red-500">⚠️</span> Critical Deadlines
              </h2>
              <div className="space-y-2">
                {timeline.deadlines.map((action: any, i: number) => (
                  <div
                    key={i}
                    className={`border rounded-xl p-4 ${CATEGORY_STYLES[action.category] ?? "bg-gray-50 border-gray-200"}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${CATEGORY_DOT[action.category] ?? "bg-gray-400"}`} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono bg-white border rounded px-2 py-0.5 text-gray-600">
                            {action.date}
                          </span>
                          <span className="text-sm font-semibold text-gray-900">{action.title}</span>
                        </div>
                        <p className="text-xs text-gray-600 mt-1 leading-relaxed">{action.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Full Timeline */}
          <div>
            <h2 className="text-base font-semibold text-gray-900 mb-3">Complete Timeline</h2>
            <div className="relative">
              {/* Vertical line */}
              <div className="absolute left-[18px] top-0 bottom-0 w-0.5 bg-gray-200" />

              <div className="space-y-3">
                {timeline.timeline.map((action: any, i: number) => (
                  <div key={i} className="flex items-start gap-4 relative">
                    {/* Dot */}
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs flex-shrink-0 z-10 border-2 border-white shadow-sm ${
                      action.category === "deadline" ? "bg-red-500 text-white" :
                      action.category === "milestone" ? "bg-blue-500 text-white" :
                      action.category === "nomination" ? "bg-purple-500 text-white" :
                      action.category === "action" ? "bg-yellow-400 text-gray-800" :
                      "bg-green-500 text-white"
                    }`}>
                      {action.category === "deadline" ? "⏰" :
                       action.category === "milestone" ? "🏁" :
                       action.category === "nomination" ? "📄" :
                       action.category === "action" ? "✅" : "📣"}
                    </div>

                    <div className="flex-1 bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between gap-2 flex-wrap">
                        <div>
                          <span className="text-xs font-mono text-gray-400">{action.date}</span>
                          <p className="text-sm font-semibold text-gray-900 mt-0.5">{action.title}</p>
                        </div>
                        {action.is_deadline && (
                          <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
                            Deadline
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">{action.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Legal Notes */}
          {timeline.legal_notes.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-xs font-semibold text-amber-900 mb-2">⚖️ Legal Notes</p>
              <ul className="space-y-1">
                {timeline.legal_notes.map((note: string, i: number) => (
                  <li key={i} className="text-xs text-amber-800 flex items-start gap-1.5">
                    <span className="flex-shrink-0 mt-0.5">•</span>
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
