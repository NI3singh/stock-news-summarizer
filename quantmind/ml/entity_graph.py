"""QuantMind ML — entity relationship graph analytics (Phase D, NetworkX).

Builds a directed graph from the persisted entities/relationships and computes
simple, explainable analytics: which entities are most connected (degree
centrality), which act as bridges between clusters (betweenness), and the
entity-/relationship-type breakdowns.
"""
from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from quantmind.memory import DatabaseManager


class EntityGraph:
    """Loads the entity graph from the DB and exposes NetworkX analytics."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    async def build(self, ticker: str | None = None) -> nx.DiGraph:
        """Build a directed NetworkX graph from the stored entities/relationships."""
        data = await self.db.get_entity_graph(ticker)
        graph = nx.DiGraph()
        for node in data["nodes"]:
            graph.add_node(
                node["id"],
                type=node["type"],
                ticker=node["ticker"],
                mentions=node["weight"],
            )
        for edge in data["edges"]:
            graph.add_edge(
                edge["source"],
                edge["target"],
                relationship=edge["relationship"],
                weight=edge["weight"],
                confidence=edge["confidence"],
            )
        return graph

    async def analytics(self, ticker: str | None = None) -> dict:
        """Return graph stats + centrality insights (or an empty-graph note)."""
        graph = await self.build(ticker)
        n = graph.number_of_nodes()
        if n == 0:
            return {
                "ticker": ticker or "all",
                "node_count": 0,
                "edge_count": 0,
                "message": "Entity graph is empty — run analyses first.",
            }

        degree = nx.degree_centrality(graph)
        most_connected = sorted(degree.items(), key=lambda kv: kv[1], reverse=True)[:5]

        # Betweenness highlights entities that bridge otherwise-separate clusters.
        between = nx.betweenness_centrality(graph)
        key_connectors = sorted(between.items(), key=lambda kv: kv[1], reverse=True)[:5]

        entity_types = Counter(d["type"] for _, d in graph.nodes(data=True))
        rel_types = Counter(d["relationship"] for _u, _v, d in graph.edges(data=True))

        return {
            "ticker": ticker or "all",
            "node_count": n,
            "edge_count": graph.number_of_edges(),
            "density": round(nx.density(graph), 4),
            "most_connected": [
                {"entity": e, "centrality": round(c, 4)} for e, c in most_connected
            ],
            "key_connectors": [
                {"entity": e, "betweenness": round(b, 4)}
                for e, b in key_connectors
                if b > 0
            ],
            "entity_types": dict(entity_types),
            "relationship_types": dict(rel_types),
            "relationships": [
                f"{u} --[{d['relationship']}]--> {v}"
                for u, v, d in list(graph.edges(data=True))[:20]
            ],
        }
