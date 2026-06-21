"use client";
import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import { Card, CardHeader, CardTitle, CardContent, EligibilityBadge, RiskBadge, LoadingCenter, EmptyState } from "@/components/ui/index";
import { candidatesApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import Link from "next/link";
import toast from "react-hot-toast";

export default function CandidatesPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    full_name: "", date_of_birth: "", gender: "", pan_number: "",
    party_affiliation: "", is_independent: false,
    electoral_roll_number: "", electoral_roll_state: "", electoral_roll_constituency: "",
    has_criminal_cases: false, has_pending_criminal_cases: false,
    holds_office_of_profit: false, has_government_contracts: false, is_bankrupt_or_insolvent: false,
    education_qualification: "", occupation: "", phone_primary: "", email: "",
  });

  const { data: candidates, isLoading } = useQuery({
    queryKey: ["candidates", search],
    queryFn: () => candidatesApi.list({ search: search || undefined }).then(r => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () => candidatesApi.create({
      ...form,
      date_of_birth: form.date_of_birth ? new Date(form.date_of_birth).toISOString() : undefined,
    }).then(r => r.data),
    onSuccess: () => {
      toast.success("Candidate created successfully");
      qc.invalidateQueries({ queryKey: ["candidates"] });
      setShowForm(false);
      setForm({ full_name: "", date_of_birth: "", gender: "", pan_number: "", party_affiliation: "", is_independent: false, electoral_roll_number: "", electoral_roll_state: "", electoral_roll_constituency: "", has_criminal_cases: false, has_pending_criminal_cases: false, holds_office_of_profit: false, has_government_contracts: false, is_bankrupt_or_insolvent: false, education_qualification: "", occupation: "", phone_primary: "", email: "" });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed to create candidate"),
  });

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Candidates</h1>
          <p className="text-sm text-gray-500 mt-0.5">Manage candidate profiles and track compliance</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>+ New Candidate</button>
      </div>

      {/* Create Form */}
      {showForm && (
        <Card className="mb-6">
          <CardHeader><CardTitle>New Candidate Profile</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="form-group">
                <label className="label">Full Name *</label>
                <input className="input" placeholder="As per official documents" value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="label">Date of Birth</label>
                <input className="input" type="date" value={form.date_of_birth} onChange={e => setForm(f => ({ ...f, date_of_birth: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="label">Gender</label>
                <select className="select" value={form.gender} onChange={e => setForm(f => ({ ...f, gender: e.target.value }))}>
                  <option value="">Select…</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label className="label">PAN Number</label>
                <input className="input" placeholder="ABCDE1234F" value={form.pan_number} onChange={e => setForm(f => ({ ...f, pan_number: e.target.value.toUpperCase() }))} />
              </div>
              <div className="form-group">
                <label className="label">Party Affiliation</label>
                <input className="input" placeholder="Party name" value={form.party_affiliation} onChange={e => setForm(f => ({ ...f, party_affiliation: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="label">Phone</label>
                <input className="input" type="tel" placeholder="+91 XXXXX XXXXX" value={form.phone_primary} onChange={e => setForm(f => ({ ...f, phone_primary: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="label">Electoral Roll Number</label>
                <input className="input" placeholder="Voter ID number" value={form.electoral_roll_number} onChange={e => setForm(f => ({ ...f, electoral_roll_number: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="label">Electoral Roll State</label>
                <input className="input" placeholder="State of registration" value={form.electoral_roll_state} onChange={e => setForm(f => ({ ...f, electoral_roll_state: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="label">Education Qualification</label>
                <input className="input" placeholder="Highest degree" value={form.education_qualification} onChange={e => setForm(f => ({ ...f, education_qualification: e.target.value }))} />
              </div>
            </div>
            {/* Boolean flags */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4">
              {[
                { key: "is_independent", label: "Independent Candidate" },
                { key: "has_criminal_cases", label: "Has Criminal Cases" },
                { key: "has_pending_criminal_cases", label: "Has Pending Criminal Cases" },
                { key: "holds_office_of_profit", label: "Holds Office of Profit" },
                { key: "has_government_contracts", label: "Has Government Contracts" },
                { key: "is_bankrupt_or_insolvent", label: "Bankrupt / Insolvent" },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded text-blue-600"
                    checked={(form as any)[key]}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.checked }))}
                  />
                  <span className="text-sm text-gray-700">{label}</span>
                </label>
              ))}
            </div>
            <div className="flex gap-3 mt-4">
              <button className="btn-primary" onClick={() => createMutation.mutate()} disabled={!form.full_name || createMutation.isPending}>
                {createMutation.isPending ? "Creating…" : "Create Candidate"}
              </button>
              <button className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <div className="mb-4">
        <input className="input max-w-sm" placeholder="Search candidates…" value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {/* Table */}
      {isLoading ? <LoadingCenter /> : (
        <Card>
          <CardContent className="p-0">
            {!candidates?.length ? (
              <EmptyState icon="👤" title="No candidates found" description="Create your first candidate profile to get started." action={<button className="btn-primary" onClick={() => setShowForm(true)}>Add Candidate</button>} />
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-left">
                    <th className="px-4 py-3 text-xs font-medium text-gray-500">Candidate</th>
                    <th className="px-4 py-3 text-xs font-medium text-gray-500">Party</th>
                    <th className="px-4 py-3 text-xs font-medium text-gray-500">Criminal</th>
                    <th className="px-4 py-3 text-xs font-medium text-gray-500">Added</th>
                    <th className="px-4 py-3 text-xs font-medium text-gray-500">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {candidates.map((c: any) => (
                    <tr key={c.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold text-xs">
                            {c.full_name?.[0]?.toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{c.full_name}</p>
                            {c.pan_number && <p className="text-xs text-gray-400">{c.pan_number}</p>}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{c.party_affiliation ?? <span className="text-gray-300">Independent</span>}</td>
                      <td className="px-4 py-3">
                        {c.has_criminal_cases
                          ? <span className="text-xs text-red-600 font-medium">{c.has_pending_criminal_cases ? "⚠️ Pending" : "✅ No Pending"}</span>
                          : <span className="text-xs text-green-600">✅ None</span>}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{formatDate(c.created_at)}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <Link href={`/candidates/${c.id}`} className="text-xs text-blue-600 hover:underline">View</Link>
                          <Link href={`/eligibility?candidate=${c.id}`} className="text-xs text-green-600 hover:underline">Check</Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      )}
    </AppShell>
  );
}
