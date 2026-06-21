"use client";
import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import { Card, CardHeader, CardTitle, CardContent, Alert, LoadingCenter, EmptyState } from "@/components/ui/index";
import { affidavitApi, candidatesApi, electionsApi } from "@/lib/api";
import toast from "react-hot-toast";

export default function AffidavitPage() {
  const [candidateId, setCandidateId] = useState("");
  const [electionId, setElectionId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const { data: candidates } = useQuery({ queryKey: ["candidates"], queryFn: () => candidatesApi.list().then(r => r.data) });
  const { data: elections } = useQuery({ queryKey: ["elections"], queryFn: () => electionsApi.list().then(r => r.data) });

  async function handleUpload(file: File) {
    if (!candidateId || !electionId) { toast.error("Select candidate and election first"); return; }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const resp = await affidavitApi.upload(candidateId, electionId, fd);
      setResult(resp.data);
      toast.success("Affidavit validated by AI");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Validation failed");
    } finally { setUploading(false); }
  }

  const STATUS_STYLE: Record<string, string> = {
    complete: "bg-green-50 border-green-300 text-green-800",
    incomplete: "bg-yellow-50 border-yellow-300 text-yellow-800",
    inconsistent: "bg-orange-50 border-orange-300 text-orange-800",
    incomplete_and_inconsistent: "bg-red-50 border-red-300 text-red-800",
  };

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Affidavit Validator</h1>
          <p className="text-sm text-gray-500 mt-0.5">Module 4 — AI-powered Form 26 validation · Section 33A RPA 1951</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Panel */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader><CardTitle>Upload Form 26</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="form-group">
                <label className="label">Candidate</label>
                <select className="select" value={candidateId} onChange={e => setCandidateId(e.target.value)}>
                  <option value="">Select candidate…</option>
                  {candidates?.map((c: any) => <option key={c.id} value={c.id}>{c.full_name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="label">Election</label>
                <select className="select" value={electionId} onChange={e => setElectionId(e.target.value)}>
                  <option value="">Select election…</option>
                  {elections?.map((e: any) => <option key={e.id} value={e.id}>{e.name}</option>)}
                </select>
              </div>

              <label className={`block w-full ${!candidateId || !electionId || uploading ? "opacity-40 cursor-not-allowed" : "cursor-pointer"}`}>
                <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png"
                  disabled={!candidateId || !electionId || uploading}
                  onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); }} />
                <div className="border-2 border-dashed border-blue-300 rounded-xl p-6 text-center hover:bg-blue-50 transition-colors">
                  <p className="text-2xl mb-2">📋</p>
                  <p className="text-sm font-medium text-blue-700">{uploading ? "Validating with AI…" : "Click to upload Form 26"}</p>
                  <p className="text-xs text-gray-400 mt-1">PDF, JPG, PNG — Max 10MB</p>
                </div>
              </label>

              {uploading && <LoadingCenter message="AI extracting and validating affidavit fields…" />}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>What Gets Validated</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {[
                "All movable assets (cash, deposits, vehicles, jewelry)",
                "Immovable assets (land, buildings)",
                "Liabilities (bank loans, other debts)",
                "All criminal cases (pending or convicted)",
                "PAN number presence",
                "Educational qualifications",
                "Spouse and dependent assets",
                "Consistency across disclosures",
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-gray-600">
                  <span className="text-blue-500 flex-shrink-0 mt-0.5">•</span>
                  {item}
                </div>
              ))}
              <p className="text-xs text-gray-400 pt-2 border-t border-gray-100">
                Legal basis: Section 33A RPA 1951 · ADR v. Union of India (2002)
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2">
          {result ? (
            <div className="space-y-4">
              {/* Status */}
              <div className={`rounded-xl border p-4 ${STATUS_STYLE[result.validation_status] ?? "bg-gray-50 border-gray-200 text-gray-700"}`}>
                <div className="flex items-center gap-3">
                  <span className="text-2xl">
                    {result.validation_status === "complete" ? "✅" : result.validation_status === "incomplete" ? "⚠️" : "❌"}
                  </span>
                  <div>
                    <p className="font-semibold capitalize">{result.validation_status?.replace(/_/g, " ")}</p>
                    {result.ai_analysis_notes && <p className="text-sm mt-0.5">{result.ai_analysis_notes}</p>}
                  </div>
                </div>
              </div>

              {/* Missing fields */}
              {result.missing_fields?.length > 0 && (
                <Card>
                  <CardHeader><CardTitle>⚠️ Missing Fields ({result.missing_fields.length})</CardTitle></CardHeader>
                  <CardContent className="space-y-1">
                    {result.missing_fields.map((f: string, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-sm text-orange-700 bg-orange-50 rounded px-3 py-1.5">
                        <span>⚠️</span> {f}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Legal risks */}
              {result.potential_legal_risks?.length > 0 && (
                <Card>
                  <CardHeader><CardTitle>⚖️ Potential Legal Risks</CardTitle></CardHeader>
                  <CardContent className="space-y-2">
                    {result.potential_legal_risks.map((r: any, i: number) => (
                      <div key={i} className="bg-red-50 border border-red-200 rounded-lg p-3">
                        <p className="text-sm font-medium text-red-900">{r.risk}</p>
                        {r.legal_basis && <p className="text-xs text-red-700 mt-0.5">Legal basis: {r.legal_basis}</p>}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Extracted data */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader><CardTitle>Movable Assets</CardTitle></CardHeader>
                  <CardContent>
                    {Object.keys(result.assets_movable ?? {}).length > 0 ? (
                      Object.entries(result.assets_movable).map(([k, v]: [string, any]) => (
                        <div key={k} className="flex justify-between text-sm py-1 border-b border-gray-50 last:border-0">
                          <span className="text-gray-500 capitalize">{k.replace(/_/g, " ")}</span>
                          <span className="font-medium">{typeof v === "number" ? `₹${v.toLocaleString("en-IN")}` : String(v)}</span>
                        </div>
                      ))
                    ) : <p className="text-sm text-gray-400">Not extracted</p>}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader><CardTitle>Liabilities</CardTitle></CardHeader>
                  <CardContent>
                    {Object.keys(result.liabilities ?? {}).length > 0 ? (
                      Object.entries(result.liabilities).map(([k, v]: [string, any]) => (
                        <div key={k} className="flex justify-between text-sm py-1 border-b border-gray-50 last:border-0">
                          <span className="text-gray-500 capitalize">{k.replace(/_/g, " ")}</span>
                          <span className="font-medium text-red-600">{typeof v === "number" ? `₹${v.toLocaleString("en-IN")}` : String(v)}</span>
                        </div>
                      ))
                    ) : <p className="text-sm text-gray-400">Not extracted</p>}
                  </CardContent>
                </Card>
              </div>

              {/* Criminal cases */}
              <Card>
                <CardHeader><CardTitle>Criminal Cases Extracted</CardTitle></CardHeader>
                <CardContent>
                  {result.criminal_cases?.length > 0 ? (
                    <div className="space-y-2">
                      {result.criminal_cases.map((c: any, i: number) => (
                        <div key={i} className="bg-red-50 border border-red-200 rounded-lg p-3">
                          <p className="text-sm font-medium text-red-900">{c.case_number ?? `Case ${i + 1}`}</p>
                          <p className="text-xs text-red-700">{c.court} · {c.section} · {c.status}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-green-600">✅ No criminal cases declared in affidavit</p>
                  )}
                </CardContent>
              </Card>

              <p className="text-xs text-gray-400 text-center">
                AI extraction may not be 100% accurate. Review extracted data carefully before filing nomination.
              </p>
            </div>
          ) : (
            <EmptyState
              icon="📋"
              title="Upload Form 26 to validate"
              description="AI will extract assets, liabilities, criminal cases and flag missing fields, inconsistencies, and legal risks."
            />
          )}
        </div>
      </div>
    </AppShell>
  );
}
