"use client";
import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { publicApi } from "@/lib/api";

export default function PublicPortalPage() {
  const [name, setName] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<any>(null);
  const [disclosures, setDisclosures] = useState<any>(null);

  const searchMutation = useMutation({
    mutationFn: () => publicApi.searchCandidates({ name: name || undefined }).then(r => r.data),
    onSuccess: data => { setResults(data.results ?? []); setSelectedCandidate(null); setDisclosures(null); },
  });

  const disclosureMutation = useMutation({
    mutationFn: (id: string) => publicApi.getCandidateDisclosures(id).then(r => r.data),
    onSuccess: (data, id) => {
      setDisclosures(data);
      setSelectedCandidate(results.find(r => r.id === id));
    },
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-blue-900 text-white px-6 py-10 text-center">
        <p className="text-3xl font-bold mb-2">🌐 Public Transparency Portal</p>
        <p className="text-blue-200 text-sm max-w-lg mx-auto">
          Search for candidate disclosures, assets, liabilities, and criminal case information
          as mandated by Section 33A, RPA 1951 and the ADR Supreme Court judgment (2002).
        </p>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Search */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Search Candidate Disclosures</h2>
          <div className="flex gap-3">
            <input className="input flex-1" placeholder="Enter candidate name…" value={name} onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === "Enter" && searchMutation.mutate()} />
            <button className="btn-primary" onClick={() => searchMutation.mutate()} disabled={searchMutation.isPending}>
              {searchMutation.isPending ? "Searching…" : "Search"}
            </button>
          </div>
        </div>

        {/* Results */}
        {results.length > 0 && !selectedCandidate && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <p className="font-semibold text-gray-900">{results.length} candidate(s) found</p>
            </div>
            <div className="divide-y divide-gray-50">
              {results.map((c: any) => (
                <div key={c.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                  <div>
                    <p className="font-medium text-gray-900">{c.full_name}</p>
                    <p className="text-sm text-gray-500">{c.party_affiliation ?? "Independent"}</p>
                    <div className="flex gap-3 mt-1">
                      {c.has_criminal_cases && (
                        <span className="text-xs text-red-600">⚠️ Criminal cases declared</span>
                      )}
                      {c.has_pending_criminal_cases && (
                        <span className="text-xs text-orange-600">⚠️ Pending cases</span>
                      )}
                    </div>
                  </div>
                  <button className="btn-secondary text-sm" onClick={() => disclosureMutation.mutate(c.id)}
                    disabled={disclosureMutation.isPending}>
                    View Disclosures
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Disclosure Detail */}
        {disclosures && selectedCandidate && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <button className="btn-secondary text-sm" onClick={() => { setSelectedCandidate(null); setDisclosures(null); }}>
                ← Back to Results
              </button>
            </div>

            {/* Candidate Header */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900">{disclosures.candidate.full_name}</h2>
              <p className="text-gray-500">{disclosures.candidate.party_affiliation ?? "Independent"}</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
                <div><p className="text-xs text-gray-400">Education</p><p className="text-sm font-medium">{disclosures.candidate.education ?? "—"}</p></div>
                <div><p className="text-xs text-gray-400">Occupation</p><p className="text-sm font-medium">{disclosures.candidate.occupation ?? "—"}</p></div>
              </div>
            </div>

            {/* Criminal Cases */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h3 className="font-semibold text-gray-900 mb-3">Criminal Case Disclosures</h3>
              {disclosures.disclosures.criminal_cases?.length > 0 ? (
                <div className="space-y-2">
                  {disclosures.disclosures.criminal_cases.map((c: any, i: number) => (
                    <div key={i} className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <p className="text-sm font-medium text-red-900">{c.case_number ?? `Case ${i + 1}`}</p>
                      <p className="text-xs text-red-700">{c.court} · {c.section} · Status: {c.status}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-green-600">✅ No criminal cases declared</p>
              )}
            </div>

            {/* Assets */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                <h3 className="font-semibold text-gray-900 mb-3">Movable Assets</h3>
                {disclosures.disclosures.assets_movable && Object.keys(disclosures.disclosures.assets_movable).length > 0 ? (
                  <div className="space-y-1">
                    {Object.entries(disclosures.disclosures.assets_movable).map(([k, v]: [string, any]) => (
                      <div key={k} className="flex justify-between text-sm">
                        <span className="text-gray-500 capitalize">{k.replace(/_/g, " ")}</span>
                        <span className="font-medium">{typeof v === "number" ? `₹${v.toLocaleString("en-IN")}` : String(v)}</span>
                      </div>
                    ))}
                  </div>
                ) : <p className="text-sm text-gray-400">Not disclosed</p>}
              </div>

              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                <h3 className="font-semibold text-gray-900 mb-3">Liabilities</h3>
                {disclosures.disclosures.liabilities && Object.keys(disclosures.disclosures.liabilities).length > 0 ? (
                  <div className="space-y-1">
                    {Object.entries(disclosures.disclosures.liabilities).map(([k, v]: [string, any]) => (
                      <div key={k} className="flex justify-between text-sm">
                        <span className="text-gray-500 capitalize">{k.replace(/_/g, " ")}</span>
                        <span className="font-medium text-red-600">{typeof v === "number" ? `₹${v.toLocaleString("en-IN")}` : String(v)}</span>
                      </div>
                    ))}
                  </div>
                ) : <p className="text-sm text-gray-400">Not disclosed</p>}
              </div>
            </div>

            {/* Source note */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-xs text-amber-800"><strong>Data Source:</strong> {disclosures.data_source}</p>
              <p className="text-xs text-amber-700 mt-1">{disclosures.disclaimer}</p>
              {disclosures.disclosures.affidavit_date && (
                <p className="text-xs text-amber-600 mt-1">Affidavit filed: {disclosures.disclosures.affidavit_date}</p>
              )}
            </div>
          </div>
        )}

        {!results.length && !searchMutation.isPending && (
          <div className="text-center py-12 text-gray-400">
            <p className="text-4xl mb-3">🔍</p>
            <p className="font-medium text-gray-600">Search for any candidate to view their public disclosures</p>
            <p className="text-sm mt-1">Data sourced from Form 26 affidavits as required by Indian election law</p>
          </div>
        )}
      </div>
    </div>
  );
}
