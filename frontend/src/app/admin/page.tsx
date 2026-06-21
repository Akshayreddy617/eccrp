"use client";
import React from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import { Card, CardHeader, CardTitle, CardContent, StatCard, LoadingCenter } from "@/components/ui/index";
import { apiClient } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import toast from "react-hot-toast";

export default function AdminPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["admin", "stats"],
    queryFn: () => apiClient.get("/admin/stats").then(r => r.data),
  });

  const { data: users, refetch: refetchUsers } = useQuery({
    queryKey: ["admin", "users"],
    queryFn: () => apiClient.get("/admin/users?page_size=20").then(r => r.data),
  });

  const { data: logs } = useQuery({
    queryKey: ["admin", "audit-logs"],
    queryFn: () => apiClient.get("/admin/audit-logs?page_size=20").then(r => r.data),
  });

  const seedMutation = useMutation({
    mutationFn: () => apiClient.post("/admin/seed/judgments").then(r => r.data),
    onSuccess: d => toast.success(d.message),
    onError: () => toast.error("Seeding failed"),
  });

  const ingestMutation = useMutation({
    mutationFn: () => apiClient.post("/admin/ingest/legal-corpus").then(r => r.data),
    onSuccess: d => toast.success(d.message),
    onError: () => toast.error("Ingest failed"),
  });

  const toggleUser = useMutation({
    mutationFn: (userId: string) => apiClient.patch(`/admin/users/${userId}/toggle-active`).then(r => r.data),
    onSuccess: () => { toast.success("User status updated"); refetchUsers(); },
  });

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Admin Panel</h1>
          <p className="text-sm text-gray-500 mt-0.5">Platform administration — super_admin and admin only</p>
        </div>
      </div>

      {/* Platform Stats */}
      {isLoading ? <LoadingCenter /> : stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard label="Total Users" value={stats.total_users} color="blue" />
          <StatCard label="Candidates" value={stats.total_candidates} color="green" />
          <StatCard label="Elections" value={stats.total_elections} color="purple" />
          <StatCard label="Eligibility Checks" value={stats.total_eligibility_checks} color="orange" />
          <StatCard label="MCC Checks" value={stats.total_mcc_checks} color="red" />
          <StatCard label="Legal Rules" value={stats.total_legal_rules} color="gray" />
          <StatCard label="Judgments" value={stats.total_judgments} color="purple" />
          <StatCard label="AI Queries" value={stats.total_ai_queries} color="blue" />
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader><CardTitle>Data Management</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">Seed Landmark Judgments</p>
                <p className="text-xs text-gray-500">Load 6 pre-configured landmark SC judgments into DB</p>
              </div>
              <button className="btn-primary text-sm" onClick={() => seedMutation.mutate()} disabled={seedMutation.isPending}>
                {seedMutation.isPending ? "Seeding…" : "Seed Now"}
              </button>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">Ingest Legal Corpus</p>
                <p className="text-xs text-gray-500">Index legal rules into OpenSearch for AI RAG queries</p>
              </div>
              <button className="btn-secondary text-sm" onClick={() => ingestMutation.mutate()} disabled={ingestMutation.isPending}>
                {ingestMutation.isPending ? "Queuing…" : "Trigger Ingest"}
              </button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>System Status</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {[
              { label: "Backend API", url: "/health" },
              { label: "Database", url: "/readiness" },
            ].map(({ label, url }) => (
              <div key={label} className="flex items-center justify-between p-2 bg-green-50 border border-green-200 rounded">
                <span className="text-sm text-green-800">{label}</span>
                <span className="text-xs text-green-600 font-medium">✅ Operational</span>
              </div>
            ))}
            <p className="text-xs text-gray-400 pt-1">
              Check <a href="/api/v1/docs" target="_blank" className="text-blue-600 hover:underline">API Docs</a> for full OpenAPI spec
            </p>
          </CardContent>
        </Card>
      </div>

      {/* User Management */}
      <Card className="mb-6">
        <CardHeader><CardTitle>User Management</CardTitle></CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left">
                <th className="px-4 py-3 text-xs font-medium text-gray-500">Email</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500">Name</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500">Role</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500">Status</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500">Joined</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {users?.map((u: any) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-700">{u.email}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{u.full_name}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full capitalize">
                      {u.role?.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium ${u.is_active ? "text-green-600" : "text-red-500"}`}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{formatDateTime(u.created_at)}</td>
                  <td className="px-4 py-3">
                    <button className="text-xs text-orange-600 hover:underline"
                      onClick={() => toggleUser.mutate(u.id)}>
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Audit Logs */}
      <Card>
        <CardHeader><CardTitle>Recent Audit Logs</CardTitle></CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left">
                <th className="px-4 py-3 text-xs font-medium text-gray-500">Action</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500">Resource</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500">IP</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500">Status</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {logs?.map((l: any) => (
                <tr key={l.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">{l.action}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">{l.resource_type}</td>
                  <td className="px-4 py-3 text-xs text-gray-400">{l.ip_address}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium ${l.status === "success" ? "text-green-600" : "text-red-500"}`}>
                      {l.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">{formatDateTime(l.created_at)}</td>
                </tr>
              ))}
              {!logs?.length && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">No audit logs yet</td></tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </AppShell>
  );
}
