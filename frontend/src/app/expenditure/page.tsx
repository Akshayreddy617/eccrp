"use client";

import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import {
  Card, CardHeader, CardTitle, CardContent,
  RiskBadge, Alert, StatCard, LoadingCenter,
} from "@/components/ui/index";
import { expenditureApi, candidatesApi, electionsApi } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend,
} from "recharts";
import toast from "react-hot-toast";

const CATEGORIES = [
  "vehicle", "advertising_print", "advertising_digital", "advertising_outdoor",
  "meetings_rallies", "travel", "volunteers", "campaign_materials",
  "sound_equipment", "other",
];

export default function ExpenditurePage() {
  const [selectedCandidate, setSelectedCandidate] = useState("");
  const [selectedElection, setSelectedElection] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);
  const [form, setForm] = useState({
    category: "vehicle",
    description: "",
    amount: "",
    expense_date: new Date().toISOString().split("T")[0],
    vendor_name: "",
    receipt_number: "",
  });

  const { data: candidates } = useQuery({
    queryKey: ["candidates"],
    queryFn: () => candidatesApi.list().then((r) => r.data),
  });

  const { data: elections } = useQuery({
    queryKey: ["elections"],
    queryFn: () => electionsApi.list().then((r) => r.data),
  });

  const { data: dashboard, refetch } = useQuery({
    queryKey: ["expenditure", "dashboard", selectedCandidate, selectedElection],
    queryFn: () =>
      expenditureApi.dashboard(selectedCandidate, selectedElection).then((r) => r.data),
    enabled: !!(selectedCandidate && selectedElection),
  });

  const addMutation = useMutation({
    mutationFn: () =>
      expenditureApi.add({
        candidate_id: selectedCandidate,
        election_id: selectedElection,
        ...form,
        amount: parseFloat(form.amount),
        expense_date: new Date(form.expense_date).toISOString(),
      }).then((r) => r.data),
    onSuccess: () => {
      toast.success("Expenditure recorded");
      setShowAddForm(false);
      setForm({ category: "vehicle", description: "", amount: "", expense_date: new Date().toISOString().split("T")[0], vendor_name: "", receipt_number: "" });
      refetch();
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail ?? "Failed to add expenditure"),
  });

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Election Expenditure Tracker</h1>
          <p className="text-sm text-gray-500 mt-0.5">Module 7 — Section 77 & 78 RPA 1951</p>
        </div>
        <button className="btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
          + Add Expenditure
        </button>
      </div>

      {/* Selectors */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <label className="label">Candidate</label>
          <select className="select" value={selectedCandidate} onChange={(e) => setSelectedCandidate(e.target.value)}>
            <option value="">Select candidate…</option>
            {candidates?.map((c: any) => <option key={c.id} value={c.id}>{c.full_name}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Election</label>
          <select className="select" value={selectedElection} onChange={(e) => setSelectedElection(e.target.value)}>
            <option value="">Select election…</option>
            {elections?.map((e: any) => <option key={e.id} value={e.id}>{e.name} ({e.year})</option>)}
          </select>
        </div>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <Card className="mb-6">
          <CardHeader><CardTitle>Add Expenditure Entry</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="form-group">
                <label className="label">Category</label>
                <select className="select" value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}>
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c.replace(/_/g, " ").replace(/\b\w/g, (x) => x.toUpperCase())}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="label">Amount (₹)</label>
                <input className="input" type="number" min="0" placeholder="0" value={form.amount} onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="label">Date</label>
                <input className="input" type="date" value={form.expense_date} onChange={(e) => setForm((f) => ({ ...f, expense_date: e.target.value }))} />
              </div>
              <div className="form-group col-span-2">
                <label className="label">Description</label>
                <input className="input" placeholder="What was this expense for?" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="label">Vendor Name</label>
                <input className="input" placeholder="Vendor / Supplier" value={form.vendor_name} onChange={(e) => setForm((f) => ({ ...f, vendor_name: e.target.value }))} />
              </div>
            </div>
            <div className="flex gap-3 mt-2">
              <button className="btn-primary" onClick={() => addMutation.mutate()} disabled={!form.description || !form.amount || addMutation.isPending}>
                {addMutation.isPending ? "Saving…" : "Save Entry"}
              </button>
              <button className="btn-secondary" onClick={() => setShowAddForm(false)}>Cancel</button>
            </div>
          </CardContent>
        </Card>
      )}

      {!(selectedCandidate && selectedElection) && (
        <div className="flex items-center justify-center h-48 text-center">
          <div>
            <p className="text-3xl mb-2">💰</p>
            <p className="text-gray-500">Select a candidate and election to view expenditure dashboard</p>
          </div>
        </div>
      )}

      {selectedCandidate && selectedElection && (
        <>
          {!dashboard ? (
            <LoadingCenter message="Loading expenditure data…" />
          ) : (
            <div className="space-y-6">
              {/* Risk Alerts */}
              {dashboard.risk_alerts?.length > 0 && (
                <div className="space-y-2">
                  {dashboard.risk_alerts.map((alert: string, i: number) => (
                    <Alert
                      key={i}
                      variant={alert.includes("🔴") ? "error" : alert.includes("🟠") ? "warning" : "info"}
                    >
                      {alert}
                    </Alert>
                  ))}
                </div>
              )}

              {/* Stats */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard label="Total Spent" value={formatCurrency(dashboard.total_spent)} color="blue" />
                <StatCard label="Expenditure Limit" value={formatCurrency(dashboard.expenditure_limit)} color="gray" />
                <StatCard
                  label="Limit Utilised"
                  value={formatPercent(dashboard.limit_utilization_pct)}
                  color={
                    (dashboard.limit_utilization_pct ?? 0) >= 85
                      ? "red"
                      : (dashboard.limit_utilization_pct ?? 0) >= 70
                      ? "orange"
                      : "green"
                  }
                />
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Risk Level</p>
                  <div className="mt-2">
                    <RiskBadge level={dashboard.risk_level} />
                  </div>
                </div>
              </div>

              {/* Limit Bar */}
              {dashboard.expenditure_limit && (
                <Card>
                  <CardContent className="py-4">
                    <div className="flex justify-between text-xs text-gray-500 mb-2">
                      <span>₹0</span>
                      <span className="font-semibold text-gray-900">
                        {formatCurrency(dashboard.total_spent)} spent of {formatCurrency(dashboard.expenditure_limit)} limit
                      </span>
                      <span>{formatCurrency(dashboard.expenditure_limit)}</span>
                    </div>
                    <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          (dashboard.limit_utilization_pct ?? 0) >= 95
                            ? "bg-red-500"
                            : (dashboard.limit_utilization_pct ?? 0) >= 80
                            ? "bg-orange-500"
                            : "bg-green-500"
                        }`}
                        style={{ width: `${Math.min(100, dashboard.limit_utilization_pct ?? 0)}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      Section 10A RPA 1951: Exceeding limit = disqualification for 3 years
                    </p>
                  </CardContent>
                </Card>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Category breakdown */}
                <Card>
                  <CardHeader><CardTitle>Expenditure by Category</CardTitle></CardHeader>
                  <CardContent>
                    {dashboard.by_category.length > 0 ? (
                      <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={dashboard.by_category} layout="vertical">
                          <XAxis type="number" tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} fontSize={11} />
                          <YAxis type="category" dataKey="category" width={110} fontSize={10}
                            tickFormatter={(v) => v.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()).slice(0, 14)} />
                          <Tooltip formatter={(v: any) => formatCurrency(v)} />
                          <Bar dataKey="total" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-sm text-gray-400 text-center py-8">No expenditure recorded yet</p>
                    )}
                  </CardContent>
                </Card>

                {/* Daily trend */}
                <Card>
                  <CardHeader><CardTitle>Daily Spending Trend</CardTitle></CardHeader>
                  <CardContent>
                    {dashboard.daily_trend.length > 0 ? (
                      <ResponsiveContainer width="100%" height={220}>
                        <LineChart data={dashboard.daily_trend}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                          <XAxis dataKey="date" fontSize={10} tickFormatter={(d) => d.slice(5)} />
                          <YAxis fontSize={10} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                          <Tooltip formatter={(v: any) => formatCurrency(v)} />
                          <Line type="monotone" dataKey="amount" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-sm text-gray-400 text-center py-8">No trend data yet</p>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Recent Entries */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Recent Entries</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 text-left">
                        <th className="px-4 py-3 text-xs font-medium text-gray-500">Date</th>
                        <th className="px-4 py-3 text-xs font-medium text-gray-500">Category</th>
                        <th className="px-4 py-3 text-xs font-medium text-gray-500">Description</th>
                        <th className="px-4 py-3 text-xs font-medium text-gray-500 text-right">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {dashboard.recent_entries.map((entry: any) => (
                        <tr key={entry.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-xs text-gray-500">{entry.expense_date}</td>
                          <td className="px-4 py-3 text-xs text-gray-600 capitalize">
                            {entry.category?.replace(/_/g, " ")}
                          </td>
                          <td className="px-4 py-3 text-xs text-gray-700">{entry.description}</td>
                          <td className="px-4 py-3 text-xs font-medium text-gray-900 text-right">
                            {formatCurrency(entry.amount)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {dashboard.recent_entries.length === 0 && (
                    <p className="text-sm text-gray-400 text-center py-8">No expenditure entries yet</p>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}
