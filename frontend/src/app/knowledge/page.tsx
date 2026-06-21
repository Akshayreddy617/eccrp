"use client";
import React, { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import { Card, CardHeader, CardTitle, CardContent, LoadingCenter, EmptyState } from "@/components/ui/index";
import { knowledgeApi } from "@/lib/api";

const SOURCE_TYPES = [
  { value: "", label: "All Sources" },
  { value: "constitution_article", label: "Constitution of India" },
  { value: "rp_act_1950", label: "RPA 1950" },
  { value: "rp_act_1951", label: "RPA 1951" },
  { value: "conduct_of_election_rules", label: "Conduct of Election Rules 1961" },
  { value: "eci_circular", label: "ECI Circulars" },
  { value: "sec_circular", label: "SEC Circulars" },
  { value: "pci_guideline", label: "Press Council Guidelines" },
  { value: "rni_rule", label: "RNI Rules" },
  { value: "mcc_guideline", label: "MCC Guidelines" },
];

export default function KnowledgePage() {
  const [query, setQuery] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [searchResults, setSearchResults] = useState<any>(null);

  const searchMutation = useMutation({
    mutationFn: () => knowledgeApi.search({ query, source_type: sourceType || undefined, limit: 20 }).then(r => r.data),
    onSuccess: data => setSearchResults(data),
  });

  const { data: rulesData, isLoading } = useQuery({
    queryKey: ["knowledge", "rules", sourceType],
    queryFn: () => knowledgeApi.listRules({ source_type: sourceType || undefined, page_size: 30 }).then(r => r.data),
  });

  const { data: articlesData } = useQuery({
    queryKey: ["knowledge", "articles"],
    queryFn: () => knowledgeApi.listArticles().then(r => r.data),
  });

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Legal Knowledge Repository</h1>
          <p className="text-sm text-gray-500 mt-0.5">Module 9 — Constitution, RPA Acts, ECI Circulars, Rules</p>
        </div>
      </div>

      {/* Search bar */}
      <div className="flex gap-3 mb-6">
        <input
          className="input flex-1"
          placeholder="Search legal provisions… e.g. 'office of profit', 'criminal conviction', 'expenditure limit'"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === "Enter" && query.length >= 3 && searchMutation.mutate()}
        />
        <select className="select w-56" value={sourceType} onChange={e => setSourceType(e.target.value)}>
          {SOURCE_TYPES.map(st => <option key={st.value} value={st.value}>{st.label}</option>)}
        </select>
        <button className="btn-primary" onClick={() => searchMutation.mutate()} disabled={query.length < 3 || searchMutation.isPending}>
          {searchMutation.isPending ? "Searching…" : "Search"}
        </button>
      </div>

      {/* Search Results */}
      {searchResults && (
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Search Results for "{searchResults.query}"</CardTitle>
              <span className="text-xs text-gray-400">{searchResults.total} results · {searchResults.search_time_ms?.toFixed(0)}ms</span>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {searchResults.results.length === 0 ? (
              <EmptyState icon="🔍" title="No results found" description="Try different keywords or a broader search term." />
            ) : (
              searchResults.results.map((r: any, i: number) => (
                <div key={i} className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50">
                  <div className="flex items-start gap-2">
                    <span className="text-xs font-mono bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-200 flex-shrink-0">
                      {r.section ?? "—"}
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{r.title}</p>
                      <p className="text-xs text-gray-400 mt-0.5 capitalize">{r.source_type?.replace(/_/g, " ")}</p>
                      {r.summary && <p className="text-xs text-gray-600 mt-1 leading-relaxed">{r.summary}</p>}
                    </div>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rules browser */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Legal Provisions</CardTitle>
                <span className="text-xs text-gray-400">{rulesData?.length ?? 0} provisions</span>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {isLoading ? <LoadingCenter /> : (
                <div className="divide-y divide-gray-50 max-h-[600px] overflow-y-auto">
                  {rulesData?.length === 0 ? (
                    <EmptyState icon="📚" title="No legal rules loaded" description="Run the admin seed command to populate the knowledge base." />
                  ) : (
                    rulesData?.map((rule: any) => (
                      <div key={rule.id} className="px-4 py-3 hover:bg-gray-50">
                        <div className="flex items-start gap-2">
                          <span className="text-xs font-mono bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded border border-amber-200 flex-shrink-0 mt-0.5">
                            {rule.section_number ?? "—"}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{rule.title}</p>
                            <p className="text-xs text-gray-400 capitalize">{rule.source_type?.replace(/_/g, " ")}</p>
                            {rule.summary && <p className="text-xs text-gray-500 mt-1 leading-relaxed line-clamp-2">{rule.summary}</p>}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Articles sidebar */}
        <div>
          <Card>
            <CardHeader><CardTitle>Knowledge Articles</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-gray-50 max-h-[600px] overflow-y-auto">
                {articlesData?.length === 0 || !articlesData ? (
                  <EmptyState icon="📄" title="No articles yet" description="Published guides appear here." />
                ) : (
                  articlesData.map((a: any) => (
                    <div key={a.id} className="px-4 py-3 hover:bg-gray-50 cursor-pointer">
                      <p className="text-sm font-medium text-gray-900 line-clamp-2">{a.title}</p>
                      <p className="text-xs text-gray-400 mt-0.5 capitalize">{a.article_type?.replace(/_/g, " ")}</p>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* Quick reference */}
          <Card className="mt-4">
            <CardHeader><CardTitle>Quick Reference</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {[
                { ref: "Art. 84", desc: "Qualifications for Parliament" },
                { ref: "Art. 102", desc: "Disqualifications for Parliament" },
                { ref: "Art. 173", desc: "Qualifications for State Legislature" },
                { ref: "Art. 191", desc: "Disqualifications for State Legislature" },
                { ref: "Sec. 8", desc: "Conviction disqualification" },
                { ref: "Sec. 8A", desc: "Corrupt practices disqualification" },
                { ref: "Sec. 9A", desc: "Government contracts" },
                { ref: "Sec. 10A", desc: "Expenditure account failure" },
                { ref: "Sec. 33A", desc: "Mandatory affidavit disclosure" },
                { ref: "Sec. 77", desc: "Account of election expenses" },
                { ref: "Sec. 78", desc: "Lodge account within 30 days" },
                { ref: "Sec. 123", desc: "Corrupt practices definition" },
                { ref: "Sec. 126", desc: "48-hour silence period" },
              ].map(item => (
                <div key={item.ref} className="flex items-start gap-2">
                  <span className="text-xs font-mono bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded flex-shrink-0">{item.ref}</span>
                  <span className="text-xs text-gray-500">{item.desc}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
