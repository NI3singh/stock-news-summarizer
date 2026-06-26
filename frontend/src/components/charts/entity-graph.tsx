"use client";
import { useEffect } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { GraphEdge, GraphNode } from "@/lib/types";

const TYPE_STYLE: Record<string, { bg: string; border: string }> = {
  company: { bg: "#1e3a8a", border: "#3b82f6" },
  person: { bg: "#581c87", border: "#a855f7" },
  product: { bg: "#14532d", border: "#22c55e" },
  regulatory_body: { bg: "#78350f", border: "#f59e0b" },
  event: { bg: "#164e63", border: "#06b6d4" },
};

function nodeStyle(type: string) {
  return TYPE_STYLE[type] ?? { bg: "#1f2937", border: "#64748b" };
}

function edgeColor(type: string): { stroke: string; animated: boolean } {
  const t = type.toLowerCase();
  if (t.includes("compet")) return { stroke: "#ef4444", animated: true };
  if (t.includes("partner")) return { stroke: "#22c55e", animated: false };
  if (t.includes("acqui")) return { stroke: "#3b82f6", animated: false };
  if (t.includes("sue")) return { stroke: "#ef4444", animated: false };
  if (t.includes("suppl")) return { stroke: "#eab308", animated: false };
  if (t.includes("employ") || t.includes("work")) return { stroke: "#94a3b8", animated: false };
  if (t.includes("invest")) return { stroke: "#a855f7", animated: false };
  return { stroke: "#475569", animated: false };
}

export function EntityGraphFlow({
  nodes,
  edges,
  onNodeClick,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (name: string) => void;
}) {
  const [rfNodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [rfEdges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    const ids = new Set(nodes.map((x) => x.name));
    const total = nodes.length || 1;

    const built: Node[] = nodes.map((node, i) => {
      const angle = (i / total) * 2 * Math.PI;
      const { bg, border } = nodeStyle(node.type);
      const scale = Math.min(1 + node.mention_count * 0.05, 1.4);
      return {
        id: node.name,
        data: { label: node.name, type: node.type },
        position: { x: 420 + 320 * Math.cos(angle), y: 320 + 240 * Math.sin(angle) },
        style: {
          background: bg,
          border: `2px solid ${border}`,
          color: "#f1f5f9",
          borderRadius: node.type === "person" ? 9999 : 8,
          padding: "6px 12px",
          fontSize: Math.round(12 * scale),
          fontWeight: 600,
        },
      };
    });

    const builtEdges: Edge[] = edges
      .filter((e) => ids.has(e.source) && ids.has(e.target))
      .map((e, i) => {
        const { stroke, animated } = edgeColor(e.type);
        return {
          id: `e${i}`,
          source: e.source,
          target: e.target,
          label: e.type.replace(/_/g, " "),
          animated,
          style: { stroke, strokeDasharray: animated ? "6 4" : undefined },
          labelStyle: { fill: "#94a3b8", fontSize: 10 },
          labelBgStyle: { fill: "#0d1117", fillOpacity: 0.85 },
        };
      });

    setNodes(built);
    setEdges(builtEdges);
  }, [nodes, edges, setNodes, setEdges]);

  return (
    <ReactFlow
      nodes={rfNodes}
      edges={rfEdges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={(_, node) => onNodeClick?.(node.id)}
      colorMode="dark"
      fitView
      proOptions={{ hideAttribution: true }}
      style={{ background: "#0d1117" }}
    >
      <Background color="#1e293b" gap={20} />
      <Controls />
      <MiniMap
        pannable
        zoomable
        maskColor="rgba(13,17,23,0.7)"
        nodeColor={(n) => nodeStyle(String((n.data as { type?: string })?.type ?? "")).border}
        style={{ background: "#161b2e", border: "1px solid #2d3748" }}
      />
    </ReactFlow>
  );
}
