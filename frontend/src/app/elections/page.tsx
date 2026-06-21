"use client";
import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import { Card, CardHeader, CardTitle, CardContent, Badge, LoadingCenter, EmptyState } from "@/components/ui/index";
import { electionsApi, ElectionType } from "@/lib/api";
import { ELECTION_TYPE_LABELS, formatDate, formatCurrency } from "@/lib/utils";
import Link from "next/link";
import toast from "react-hot-toast";

export default function ElectionsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [selection, setSelection] = useState<any>(null);
  const [selForm, setSelForm] = useState({ election_type: "lok_sabha" as ElectionType, state_code: "AP" });

  const { data: elections, isLoading } = useQuery({
    queryKey: ["elections"],
    queryFn: () => electionsApi.list().then(r => r.data),
  });

  const selectMutation = useMutation({
    mutationFn: () => electionsApi.select(selForm).then(r => r.data),
    onSuccess: data => setSelection(data),
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Selection failed"),
  });

  const STATES = ["AP", "TN", "MH", "KA", "DL", "UP", "WB", "RJ", "GJ", "MP", "HR", "PB", "KL", "OR", "AS", "BR", "JH", "CG", "UK", "HP", "GA"];

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Elections</h1>
          <p className="text-sm text-gray-500 mt-0.5">Module 1 — Election Selection Engine + Election Management</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Module 1 — Election Selection */}
        <Card>
          <CardHeader><CardTitle>Module 1: Election Selection Engine</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs text-gray-500">Select an election type and state to auto-load all applicable constitutional provisions, laws, SEC rules, and landmark judgments.</p>
            <div className="form-group">
              <label className="label">Election Type</label>
              <select className="select" value={selForm.election_type} onChange={e => setSelForm(f => ({ ...f, election_type: e.target.value as ElectionType }))}>
                {Object.entries(ELECTION_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="label">State</label>
              <select className="select" value={selForm.state_code} onChange={e => setSelForm(f => ({ ...f, state_code: e.target.value }))}>
                {STATES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <button className="btn-primary w-full" onClick={() => selectMutation.mutate()} disabled={selectMutation.isPending}>
              {selectMutation.isPending ? "Loading provisions…" : "Load Applicable Provisions"}
            </button>
          </CardContent>
        </Card>

        {/* Provisions Result */}
        {selection && (
          <Card>
            <CardHeader>
              <CardTitle>{ELECTION_TYPE_LABELS[selection.election_type as ElectionType]} — {selection.state}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 max-h-80 overflow-y-auto">
              {selection.applicable_provisions?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Constitutional Articles</p>
                  {selection.applicable_provisions.map((p: any, i: number) => (
                    <div key={i} className="bg-amber-50 border border-amber-200 rounded-lg p-2 mb-1">
                      <p className="text-xs font-semibold text-amber-900">Article {p.article} — {p.title}</p>
                    </div>
                  ))}
                </div>
              )}
              {selection.applicable_laws?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-2">RPA Sections</p>
                  {selection.applicable_laws.map((l: any, i: number) => (
                    <div key={i} className="bg-blue-50 border border-blue-200 rounded-lg p-2 mb-1">
                      <p className="text-xs font-semibold text-blue-900">Sec. {l.section} — {l.title}</p>
                    </div>
                  ))}
                </div>
              )}
              {selection.applicable_judgments?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Landmark Judgments</p>
                  {selection.applicable_judgments.map((j: any, i: number) => (
                    <div key={i} className="bg-purple-50 border border-purple-200 rounded-lg p-2 mb-1">
                      <p className="text-xs font-semibold text-purple-900">{j.case}</p>
                      <p className="text-xs text-purple-700">{j.citation}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Elections List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Registered Elections</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? <LoadingCenter /> : !elections?.length ? (
            <EmptyState icon="🗳️" title="No elections registered" description="Elections are added by administrators." />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-left">
                  <th className="px-4 py-3 text-xs font-medium text-gray-500">Election</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-500">Type</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-500">Year</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-500">Polling Date</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-500">Exp. Limit</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {elections.map((e: any) => (
                  <tr key={e.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{e.name}</td>
                    <td className="px-4 py-3">
                      <Badge className="bg-blue-50 text-blue-700 border-blue-200 text-xs">
                        {ELECTION_TYPE_LABELS[e.election_type as ElectionType] ?? e.election_type}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{e.year}</td>
                    <td className="px-4 py-3 text-gray-500">{formatDate(e.polling_date)}</td>
                    <td className="px-4 py-3 text-gray-500">{formatCurrency(e.expenditure_limit)}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <Link href={`/timeline?election=${e.id}`} className="text-xs text-blue-600 hover:underline">Timeline</Link>
                        <Link href={`/expenditure?election=${e.id}`} className="text-xs text-green-600 hover:underline">Expenses</Link>
                        <Link href={`/mcc?election=${e.id}`} className="text-xs text-orange-600 hover:underline">MCC</Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </AppShell>
  );
}
