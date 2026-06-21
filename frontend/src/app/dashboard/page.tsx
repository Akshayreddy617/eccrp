"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import {
  Card, CardHeader, CardTitle, CardContent,
  StatCard, RiskBadge, EligibilityBadge, ScoreBar,
  LoadingCenter, EmptyState,
} from "@/components/ui/index";
import { dashboardApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { formatDate, formatPercent } from "@/lib/utils";
import Link from "next/link";

export default function DashboardPage() {
  const { user } = useAuthStore();

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["dashboard", "consultant"],
    queryFn: () => dashboardApi.consultant().then((r) => r.data),
  });

  const { data: notifications } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => dashboardApi.notifications({ is_read: false, page_size: 5 }).then((r) => r.data),
  });

  return (
    <AppShell>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            Welcome, {user?.full_name?.split(" ")[0]} 👋
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Election Compliance & Candidate Readiness Platform
          </p>
        </div>
        <Link href="/candidates/new" className="btn-primary">
          + Add Candidate
        </Link>
      </div>

      {/* Stats Row */}
      {isLoading ? (
        <LoadingCenter />
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard
              label="Total Candidates"
              value={dashboard?.total_candidates ?? 0}
              color="blue"
            />
            <StatCard
              label="Active Elections"
              value={dashboard?.active_elections ?? 0}
              color="green"
            />
            <StatCard
              label="Pending Actions"
              value={dashboard?.pending_actions_count ?? 0}
              color="orange"
            />
            <StatCard
              label="Unread Alerts"
              value={Array.isArray(notifications) ? notifications.length : 0}
              color="red"
            />
          </div>

          {/* Candidates Table */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>Candidate Overview</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  {!dashboard?.candidates?.length ? (
                    <EmptyState
                      icon="👤"
                      title="No candidates yet"
                      description="Add your first candidate to start compliance tracking."
                      action={
                        <Link href="/candidates/new" className="btn-primary">
                          Add Candidate
                        </Link>
                      }
                    />
                  ) : (
                    <div className="divide-y divide-gray-100">
                      {dashboard.candidates.map((c: any) => (
                        <Link
                          key={c.candidate_id}
                          href={`/candidates/${c.candidate_id}`}
                          className="flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors"
                        >
                          {/* Avatar */}
                          <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold text-sm flex-shrink-0">
                            {c.candidate_name?.[0]?.toUpperCase()}
                          </div>

                          {/* Info */}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {c.candidate_name}
                            </p>
                            <p className="text-xs text-gray-400 truncate">
                              {c.party_affiliation ?? "Independent"}
                            </p>

                            {/* Readiness bar */}
                            {c.readiness_score != null && (
                              <div className="mt-1.5 w-40">
                                <ScoreBar
                                  score={c.readiness_score}
                                  size="sm"
                                  showValue={false}
                                />
                              </div>
                            )}
                          </div>

                          {/* Badges */}
                          <div className="flex flex-col items-end gap-1">
                            {c.eligibility_status && (
                              <EligibilityBadge status={c.eligibility_status} />
                            )}
                            {c.overall_risk && (
                              <RiskBadge level={c.overall_risk} />
                            )}
                          </div>

                          {/* Pending count */}
                          {c.pending_actions_count > 0 && (
                            <div className="w-6 h-6 rounded-full bg-orange-100 text-orange-700 text-xs font-bold flex items-center justify-center flex-shrink-0">
                              {c.pending_actions_count}
                            </div>
                          )}
                        </Link>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Right column */}
            <div className="space-y-4">
              {/* Quick Actions */}
              <Card>
                <CardHeader><CardTitle>Quick Actions</CardTitle></CardHeader>
                <CardContent className="grid grid-cols-1 gap-2">
                  {[
                    { href: "/eligibility/check", icon: "✅", label: "Run Eligibility Check" },
                    { href: "/mcc/check", icon: "📢", label: "Check MCC Compliance" },
                    { href: "/affidavit/upload", icon: "📋", label: "Validate Affidavit" },
                    { href: "/ai-assistant", icon: "🤖", label: "Ask AI Assistant" },
                    { href: "/judgments/impact", icon: "⚖️", label: "Judgment Impact" },
                  ].map((action) => (
                    <Link
                      key={action.href}
                      href={action.href}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-lg border border-gray-200 text-sm text-gray-700 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-colors"
                    >
                      <span>{action.icon}</span>
                      <span>{action.label}</span>
                    </Link>
                  ))}
                </CardContent>
              </Card>

              {/* Notifications */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Recent Alerts</CardTitle>
                    <Link href="/dashboard/notifications" className="text-xs text-blue-600 hover:underline">
                      View all
                    </Link>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  {!Array.isArray(notifications) || notifications.length === 0 ? (
                    <p className="text-xs text-gray-400 text-center py-6">No unread alerts</p>
                  ) : (
                    <div className="divide-y divide-gray-100">
                      {notifications.slice(0, 5).map((n: any) => (
                        <div key={n.id} className="px-4 py-3">
                          <p className="text-xs font-medium text-gray-900">{n.title}</p>
                          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.message}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Legal Footer Note */}
          <div className="mt-6 bg-amber-50 border border-amber-200 rounded-xl p-4">
            <p className="text-xs text-amber-800">
              <strong>⚖️ Legal Disclaimer:</strong> ECCRP provides AI-assisted compliance guidance based on Indian
              election law. All outputs are for informational purposes only and do not constitute legal advice.
              Always consult a qualified election lawyer for specific legal matters.
            </p>
          </div>
        </>
      )}
    </AppShell>
  );
}
