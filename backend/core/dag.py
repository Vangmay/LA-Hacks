from collections import defaultdict, deque
from typing import Set, List, Dict


class DAG:
    """
    Edge convention: an edge from A -> B means A REQUIRES B
    (i.e. B must be established before A).

    - get_roots() returns nodes with no dependencies (no outgoing edges) —
      process these first.
    - topological_sort() returns nodes in processing order (dependencies first).
    - get_descendants(n) returns all nodes that would be affected if n is
      refuted (i.e. nodes that transitively depend on n).
    """

    def __init__(self) -> None:
        self.nodes: Set[str] = set()
        # edges[A] = {B, ...}  means A depends on each of B, ...
        self.edges: Dict[str, Set[str]] = defaultdict(set)
        # reverse[B] = {A, ...}  means each A depends on B
        self.reverse: Dict[str, Set[str]] = defaultdict(set)

    def add_node(self, node_id: str) -> None:
        self.nodes.add(node_id)
        _ = self.edges[node_id]
        _ = self.reverse[node_id]

    def add_edge(self, from_id: str, to_id: str) -> None:
        self.add_node(from_id)
        self.add_node(to_id)
        self.edges[from_id].add(to_id)
        self.reverse[to_id].add(from_id)

    def has_cycle(self) -> bool:
        # Kahn's, peeling from the "no remaining dependencies" side.
        out_degree = {n: len(self.edges[n]) for n in self.nodes}
        queue = deque([n for n, d in out_degree.items() if d == 0])
        visited = 0
        while queue:
            n = queue.popleft()
            visited += 1
            for m in self.reverse[n]:
                out_degree[m] -= 1
                if out_degree[m] == 0:
                    queue.append(m)
        return visited != len(self.nodes)

    def topological_sort(self) -> List[str]:
        out_degree = {n: len(self.edges[n]) for n in self.nodes}
        queue = deque(sorted([n for n, d in out_degree.items() if d == 0]))
        order: List[str] = []
        while queue:
            n = queue.popleft()
            order.append(n)
            for m in sorted(self.reverse[n]):
                out_degree[m] -= 1
                if out_degree[m] == 0:
                    queue.append(m)
        if len(order) != len(self.nodes):
            raise ValueError("DAG contains a cycle")
        return order

    def get_descendants(self, node_id: str) -> Set[str]:
        if node_id not in self.nodes:
            return set()
        seen: Set[str] = set()
        stack = [node_id]
        while stack:
            n = stack.pop()
            for m in self.reverse[n]:
                if m not in seen:
                    seen.add(m)
                    stack.append(m)
        return seen

    def get_roots(self) -> List[str]:
        return sorted([n for n in self.nodes if not self.edges[n]])

    def to_dict(self) -> dict:
        return {
            "nodes": sorted(self.nodes),
            "edges": [
                {"from": f, "to": t}
                for f in sorted(self.edges)
                for t in sorted(self.edges[f])
            ],
        }
