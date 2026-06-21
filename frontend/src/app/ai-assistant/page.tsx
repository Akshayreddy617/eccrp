"use client";

import React, { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import {
  Card, CardContent, LegalCitationCard, JudgmentCard, Alert,
} from "@/components/ui/index";
import { aiApi, AIQueryResponse, ElectionType } from "@/lib/api";
import { ELECTION_TYPE_LABELS } from "@/lib/utils";
import toast from "react-hot-toast";

interface Message {
  role: "user" | "assistant";
  content: string;
  response?: AIQueryResponse;
  timestamp: Date;
}

const EXAMPLE_QUESTIONS = [
  "Can I contest elections if a criminal case is pending against me?",
  "Do I need to disclose my spouse's assets in Form 26?",
  "What is the election expenditure limit for a Lok Sabha constituency?",
  "What activities are prohibited after MCC comes into force?",
  "Can I use a government vehicle for campaigning?",
  "What happens if I don't file my expenditure account on time?",
  "Is distributing sarees to voters allowed before elections?",
  "When does the 48-hour campaign silence period start?",
];

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState("");
  const [electionType, setElectionType] = useState<string>("");
  const [sessionId] = useState(() => crypto.randomUUID());
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const askMutation = useMutation({
    mutationFn: (q: string) =>
      aiApi
        .query(q, electionType ? { election_type: electionType } : undefined, sessionId)
        .then((r) => r.data),
    onSuccess: (data, variables) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, response: data, timestamp: new Date() },
      ]);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "AI query failed. Check API configuration.");
      setMessages((prev) => prev.slice(0, -1)); // Remove the pending user message
    },
  });

  function handleSend() {
    if (!query.trim()) return;
    const userMsg: Message = { role: "user", content: query, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    askMutation.mutate(query);
    setQuery("");
    inputRef.current?.focus();
  }

  function handleExample(q: string) {
    setQuery(q);
    inputRef.current?.focus();
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>🤖 AI Governance Assistant</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Module 12 — Ask anything about Indian election law
          </p>
        </div>
        <select
          className="select w-56"
          value={electionType}
          onChange={(e) => setElectionType(e.target.value)}
        >
          <option value="">All election types</option>
          {Object.entries(ELECTION_TYPE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      <div className="flex gap-6 h-[calc(100vh-10rem)]">
        {/* Chat Panel */}
        <div className="flex-1 flex flex-col">
          <Card className="flex-1 flex flex-col overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full gap-4 py-8">
                  <p className="text-4xl">⚖️</p>
                  <p className="text-gray-600 font-medium text-center">
                    Your AI-powered election law advisor
                  </p>
                  <p className="text-sm text-gray-400 text-center max-w-md">
                    Powered by RAG over the Constitution of India, RPA 1950/1951,
                    Conduct of Election Rules 1961, ECI guidelines, and landmark Supreme Court judgments.
                  </p>
                </div>
              )}

              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  {msg.role === "user" ? (
                    <div className="max-w-[75%] bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm">
                      {msg.content}
                    </div>
                  ) : (
                    <div className="max-w-[85%] space-y-3">
                      {/* Answer bubble */}
                      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm">🤖</span>
                          <span className="text-xs font-medium text-gray-500">AI Governance Assistant</span>
                          {msg.response && (
                            <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${
                              msg.response.confidence_score >= 0.8
                                ? "bg-green-100 text-green-700"
                                : msg.response.confidence_score >= 0.6
                                ? "bg-yellow-100 text-yellow-700"
                                : "bg-red-100 text-red-700"
                            }`}>
                              {(msg.response.confidence_score * 100).toFixed(0)}% confidence
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                          {msg.content}
                        </p>

                        {/* Recommended action */}
                        {msg.response?.recommended_action && (
                          <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-2.5">
                            <p className="text-xs font-semibold text-blue-800">💡 Recommended Action</p>
                            <p className="text-xs text-blue-700 mt-0.5">
                              {msg.response.recommended_action}
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Citations */}
                      {msg.response?.legal_basis && msg.response.legal_basis.length > 0 && (
                        <div className="space-y-1.5">
                          <p className="text-xs text-gray-400 pl-1">Legal Citations</p>
                          {msg.response.legal_basis.slice(0, 3).map((c, ci) => (
                            <LegalCitationCard key={ci} citation={c} />
                          ))}
                        </div>
                      )}

                      {/* Judgments */}
                      {msg.response?.relevant_judgments && msg.response.relevant_judgments.length > 0 && (
                        <div className="space-y-1.5">
                          <p className="text-xs text-gray-400 pl-1">Relevant Judgments</p>
                          {msg.response.relevant_judgments.slice(0, 2).map((j, ji) => (
                            <JudgmentCard key={ji} judgment={j} />
                          ))}
                        </div>
                      )}

                      {/* Disclaimer */}
                      {msg.response?.disclaimer && (
                        <p className="text-[10px] text-gray-400 pl-1 italic">
                          ⚠️ {msg.response.disclaimer}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {askMutation.isPending && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        {[0, 1, 2].map((i) => (
                          <div
                            key={i}
                            className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                            style={{ animationDelay: `${i * 0.15}s` }}
                          />
                        ))}
                      </div>
                      <span className="text-xs text-gray-400">Searching legal corpus…</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="border-t border-gray-100 p-4">
              <div className="flex gap-2 items-end">
                <textarea
                  ref={inputRef}
                  className="input flex-1 resize-none min-h-[44px] max-h-32"
                  placeholder="Ask any election law question… (Enter to send, Shift+Enter for newline)"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={1}
                />
                <button
                  className="btn-primary flex-shrink-0 h-11"
                  onClick={handleSend}
                  disabled={!query.trim() || askMutation.isPending}
                >
                  Send
                </button>
              </div>
            </div>
          </Card>
        </div>

        {/* Example Questions Panel */}
        <div className="w-64 flex-shrink-0">
          <Card className="h-full overflow-auto">
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="text-sm font-semibold text-gray-900">Example Questions</p>
            </div>
            <div className="p-3 space-y-2">
              {EXAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  className="w-full text-left text-xs text-gray-600 bg-gray-50 hover:bg-blue-50 hover:text-blue-700 rounded-lg px-3 py-2 border border-transparent hover:border-blue-200 transition-colors"
                  onClick={() => handleExample(q)}
                >
                  {q}
                </button>
              ))}
            </div>

            <div className="px-4 py-3 border-t border-gray-100 mt-auto">
              <p className="text-[10px] text-gray-400 leading-relaxed">
                Powered by RAG over Constitution of India, RPA 1950/51,
                Conduct of Election Rules 1961, ECI Circulars, and landmark SC judgments.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
