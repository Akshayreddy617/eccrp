"use client";
import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import { Card, CardHeader, CardTitle, CardContent, ScoreBar, LoadingCenter, EmptyState } from "@/components/ui/index";
import { nominationApi, candidatesApi, electionsApi } from "@/lib/api";
import toast from "react-hot-toast";

const DOCUMENT_TYPES = [
  { value: "form_26", label: "Form 26 (Affidavit)", weight: 25 },
  { value: "electoral_roll_proof", label: "Electoral Roll Proof", weight: 20 },
  { value: "assets_declaration", label: "Assets Declaration", weight: 15 },
  { value: "criminal_disclosure", label: "Criminal Disclosure", weight: 15 },
  { value: "identity_proof", label: "Identity / Photograph", weight: 15 },
  { value: "liabilities_declaration", label: "Liabilities Declaration", weight: 10 },
];

export default function NominationPage() {
  const [candidateId, setCandidateId] = useState("");
  const [electionId, setElectionId] = useState("");
  const [uploading, setUploading] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<any>(null);

  const { data: candidates } = useQuery({ queryKey: ["candidates"], queryFn: () => candidatesApi.list().then(r => r.data) });
  const { data: elections } = useQuery({ queryKey: ["elections"], queryFn: () => electionsApi.list().then(r => r.data) });

  async function loadReadiness() {
    if (!candidateId || !electionId) return;
    try {
      const resp = await nominationApi.getReadiness(candidateId, electionId);
      setReadiness(resp.data);
    } catch { setReadiness(null); }
  }

  async function handleUpload(docType: string, file: File) {
    if (!candidateId || !electionId) { toast.error("Select candidate and election first"); return; }
    setUploading(docType);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("document_type", docType);
      await nominationApi.upload(candidateId, electionId, fd);
      toast.success("Document uploaded successfully");
      await loadReadiness();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "Upload failed");
    } finally { setUploading(null); }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Nomination Readiness</h1>
          <p className="text-sm text-gray-500 mt-0.5">Module 3 — Document checklist and readiness scoring</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <label className="label">Candidate</label>
          <select className="select" value={candidateId} onChange={e => { setCandidateId(e.target.value); setReadiness(null); }}>
            <option value="">Select candidate…</option>
            {candidates?.map((c: any) => <option key={c.id} value={c.id}>{c.full_name}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Election</label>
          <select className="select" value={electionId} onChange={e => { setElectionId(e.target.value); setReadiness(null); }}>
            <option value="">Select election…</option>
            {elections?.map((e: any) => <option key={e.id} value={e.id}>{e.name} ({e.year})</option>)}
          </select>
        </div>
      </div>

      {candidateId && electionId && !readiness && (
        <div className="mb-4">
          <button className="btn-secondary" onClick={loadReadiness}>Load Readiness Status</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Readiness Score */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader><CardTitle>Overall Readiness</CardTitle></CardHeader>
            <CardContent>
              {readiness ? (
                <div className="space-y-4">
                  <div className="text-center py-4">
                    <p className="text-5xl font-bold text-gray-900">
                      {readiness.overall_readiness_score?.toFixed(0)}<span className="text-xl text-gray-400">%</span>
                    </p>
                    <p className="text-sm text-gray-500 mt-1">Nomination Ready</p>
                  </div>
                  <ScoreBar score={readiness.overall_readiness_score} size="lg" showValue={false} />
                  <div className="space-y-2 pt-2">
                    {[
                      { label: "Affidavit (Form 26)", score: readiness.affidavit_score },
                      { label: "Electoral Roll", score: readiness.electoral_roll_score },
                      { label: "Assets", score: readiness.assets_score },
                      { label: "Criminal Disclosure", score: readiness.criminal_disclosure_score },
                      { label: "Photograph / ID", score: readiness.photograph_score },
                      { label: "Liabilities", score: readiness.liabilities_score },
                    ].map(item => (
                      <div key={item.label}>
                        <div className="flex justify-between text-xs mb-0.5">
                          <span className="text-gray-500">{item.label}</span>
                          <span className={item.score === 100 ? "text-green-600 font-medium" : "text-gray-400"}>
                            {item.score === 100 ? "✅" : "⏳"}
                          </span>
                        </div>
                        <ScoreBar score={item.score} size="sm" showValue={false} />
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <EmptyState icon="📄" title="Select candidate & election" description="Then load readiness to see your score" />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Document Upload */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader><CardTitle>Document Checklist</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {DOCUMENT_TYPES.map(doc => {
                const isComplete = readiness?.completed_items?.some((c: any) => c.item === doc.value);
                return (
                  <div key={doc.value} className={`flex items-center justify-between p-3 rounded-lg border ${
                    isComplete ? "bg-green-50 border-green-200" : "bg-gray-50 border-gray-200"
                  }`}>
                    <div className="flex items-center gap-3">
                      <span className="text-lg">{isComplete ? "✅" : "⏳"}</span>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{doc.label}</p>
                        <p className="text-xs text-gray-400">{doc.weight} points</p>
                      </div>
                    </div>
                    <label className={`cursor-pointer ${!candidateId || !electionId ? "opacity-40 cursor-not-allowed" : ""}`}>
                      <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                        disabled={!candidateId || !electionId || uploading === doc.value}
                        onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(doc.value, f); }} />
                      <span className={`btn-secondary text-xs py-1.5 px-3 ${uploading === doc.value ? "opacity-50" : ""}`}>
                        {uploading === doc.value ? "Uploading…" : isComplete ? "Re-upload" : "Upload"}
                      </span>
                    </label>
                  </div>
                );
              })}
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mt-2">
                <p className="text-xs text-amber-800">
                  <strong>⚖️ Legal Note:</strong> All documents must be filed with the Returning Officer within the nomination window.
                  Section 33 RPA 1951 — nomination is liable to rejection if mandatory documents are missing.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
