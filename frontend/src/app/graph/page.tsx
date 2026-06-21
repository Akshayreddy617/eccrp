"use client";
import React, { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/ui/AppShell";
import { Card, CardHeader, CardTitle, CardContent, LoadingCenter } from "@/components/ui/index";
import { apiClient } from "@/lib/api";

export default function GraphPage() {
  const svgRef = useRef<SVGSVGElement>(null);

  const { data: graphData, isLoading } = useQuery({
    queryKey: ["graph", "full"],
    queryFn: () => apiClient.get("/graph/visualization/full?limit=80").then(r => r.data),
  });

  useEffect(() => {
    if (!graphData || !svgRef.current) return;

    const width = svgRef.current.clientWidth || 900;
    const height = 600;

    // Clear
    while (svgRef.current.firstChild) svgRef.current.removeChild(svgRef.current.firstChild);

    // Simple force-directed layout using D3
    import("d3").then(d3 => {
      const svg = d3.select(svgRef.current);
      const nodes = (graphData.nodes ?? []).map((n: any) => ({ ...n }));
      const links = (graphData.links ?? []).map((l: any) => ({
        source: l.source,
        target: l.target,
        type: l.type,
      }));

      const NODE_COLORS: Record<string, string> = {
        Article: "#3b82f6",
        Section: "#10b981",
        Rule: "#f59e0b",
        Judgment: "#8b5cf6",
        Requirement: "#ef4444",
        default: "#6b7280",
      };

      const simulation = d3.forceSimulation(nodes as any)
        .force("link", d3.forceLink(links).id((d: any) => d.id).distance(80))
        .force("charge", d3.forceManyBody().strength(-200))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide(30));

      const g = svg.append("g");

      // Zoom
      svg.call(d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.3, 3]).on("zoom", (event) => {
        g.attr("transform", event.transform);
      }) as any);

      // Links
      const link = g.append("g").selectAll("line").data(links).enter().append("line")
        .attr("stroke", "#d1d5db").attr("stroke-width", 1.5).attr("stroke-opacity", 0.6);

      // Nodes
      const node = g.append("g").selectAll("g").data(nodes).enter().append("g")
        .call(d3.drag<SVGGElement, any>()
          .on("start", (event, d: any) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on("drag", (event, d: any) => { d.fx = event.x; d.fy = event.y; })
          .on("end", (event, d: any) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
        );

      node.append("circle")
        .attr("r", 16)
        .attr("fill", (d: any) => NODE_COLORS[d.type] ?? NODE_COLORS.default)
        .attr("stroke", "#fff")
        .attr("stroke-width", 2)
        .attr("opacity", 0.9);

      node.append("text")
        .text((d: any) => d.label?.slice(0, 12) ?? "")
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .attr("font-size", 8)
        .attr("fill", "#fff")
        .attr("pointer-events", "none");

      node.append("title").text((d: any) => `${d.type}: ${d.label}`);

      simulation.on("tick", () => {
        link
          .attr("x1", (d: any) => d.source.x).attr("y1", (d: any) => d.source.y)
          .attr("x2", (d: any) => d.target.x).attr("y2", (d: any) => d.target.y);
        node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
      });
    });
  }, [graphData]);

  const NODE_COLORS_CSS: Record<string, string> = {
    Article: "bg-blue-500", Section: "bg-emerald-500", Rule: "bg-amber-500",
    Judgment: "bg-purple-500", Requirement: "bg-red-500",
  };

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Knowledge Graph</h1>
          <p className="text-sm text-gray-500 mt-0.5">Module 13 — Legal provision relationships visualised</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-4">
        {Object.entries(NODE_COLORS_CSS).map(([type, cls]) => (
          <div key={type} className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2">
            <div className={`w-3 h-3 rounded-full ${cls}`} />
            <span className="text-xs text-gray-600">{type}</span>
          </div>
        ))}
        <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2">
          <div className="w-3 h-3 rounded-full bg-gray-400" />
          <span className="text-xs text-gray-600">Other</span>
        </div>
      </div>

      <Card>
        <CardContent className="p-2">
          {isLoading ? <LoadingCenter message="Loading knowledge graph…" /> : (
            !graphData?.nodes?.length ? (
              <div className="flex flex-col items-center justify-center h-64 gap-3">
                <p className="text-3xl">🕸️</p>
                <p className="text-gray-500 font-medium">No graph data yet</p>
                <p className="text-sm text-gray-400">Populate via Admin → Seed Judgments, then ingest legal corpus</p>
              </div>
            ) : (
              <div className="relative">
                <p className="absolute top-2 right-2 text-xs text-gray-400 z-10">
                  {graphData.nodes.length} nodes · {graphData.links.length} edges · Scroll to zoom, drag to pan
                </p>
                <svg ref={svgRef} width="100%" height="600" className="bg-gray-50 rounded-lg" />
              </div>
            )
          )}
        </CardContent>
      </Card>
    </AppShell>
  );
}
