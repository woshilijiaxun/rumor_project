#!/usr/bin/env python3
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

EDGE_RE = re.compile(
    r"\['(?P<uid>[^']+)'\s*,\s*'(?P<tid>[^']+)'\s*,\s*'(?P<delay>[^']+)'\]\s*->\s*\['(?P<uid2>[^']+)'\s*,\s*'(?P<tid2>[^']+)'\s*,\s*'(?P<delay2>[^']+)'\]"
)


def parse_user_edge(line: str) -> Optional[Tuple[int, int]]:
    s = line.strip()
    if not s:
        return None
    m = EDGE_RE.search(s)
    if not m:
        return None
    try:
        u1 = int(m.group("uid"))
        u2 = int(m.group("uid2"))
    except (ValueError, TypeError):
        return None
    if u1 == u2:
        return None
    return (u1, u2) if u1 < u2 else (u2, u1)


def iter_tree_files(dataset_dir: Path):
    tree_dir = dataset_dir / "tree"
    if not tree_dir.is_dir():
        return
    for p in sorted(tree_dir.iterdir()):
        if p.is_file() and p.suffix == ".txt":
            yield p


def read_undirected_edges(dataset_dir: Path, progress_every: int = 0, debug_samples: int = 0) -> Set[Tuple[int, int]]:
    edges: Set[Tuple[int, int]] = set()

    tree_dir = dataset_dir / "tree"
    if not dataset_dir.is_dir():
        raise SystemExit(f"dataset_dir 不存在或不是目录: {dataset_dir}")
    if not tree_dir.is_dir():
        raise SystemExit(f"tree 目录不存在: {tree_dir}")

    tree_files = sorted([p for p in tree_dir.iterdir() if p.is_file() and p.suffix == ".txt"])
    if not tree_files:
        raise SystemExit(f"tree 目录下没有 .txt 文件: {tree_dir}")

    print(f"[info] dataset_dir={dataset_dir.resolve()}", flush=True)
    print(f"[info] tree_dir={tree_dir.resolve()}", flush=True)
    print(f"[info] tree_files={len(tree_files)}", flush=True)

    sample_seen = 0
    for idx, tree_file in enumerate(tree_files, 1):
        with tree_file.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                if debug_samples > 0 and sample_seen < debug_samples:
                    sample_seen += 1
                    ok = bool(EDGE_RE.search(line.strip()))
                    print(
                        f"[debug] sample from {tree_file.name}: matched={ok} line={line.strip()[:200]}",
                        flush=True,
                    )

                edge = parse_user_edge(line)
                if edge:
                    edges.add(edge)

        if progress_every > 0 and (idx % progress_every == 0 or idx == len(tree_files)):
            print(f"[progress] {idx}/{len(tree_files)} files processed, edges={len(edges)}", flush=True)

    return edges


def build_adjacency_list(edges: Set[Tuple[int, int]]) -> Dict[int, List[int]]:
    adj: Dict[int, List[int]] = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    return adj


def find_largest_connected_component(adj: Dict[int, List[int]]) -> Set[int]:
    visited: Set[int] = set()
    largest_component: Set[int] = set()

    for node in adj:
        if node in visited:
            continue

        component: Set[int] = set()
        queue: deque[int] = deque([node])
        visited.add(node)

        while queue:
            current = queue.popleft()
            component.add(current)
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        if len(component) > len(largest_component):
            largest_component = component

    return largest_component


def filter_edges_by_nodes(edges: Set[Tuple[int, int]], nodes: Set[int]) -> List[Tuple[int, int]]:
    return [(u, v) for u, v in edges if u in nodes and v in nodes]


def write_edge_list(output_path: Path, edges: List[Tuple[int, int]]):
    with output_path.open("w", encoding="utf-8") as f:
        for u, v in sorted(edges):
            f.write(f"{u} {v}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert rumor_detection_acl2017 trees into an undirected user graph (LCC only)."
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default="rumor_detection_acl2017/twitter15",
        help="Path to dataset directory (e.g., rumor_detection_acl2017/twitter15)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default="twitter15_LCC_edgelist.txt",
        help="Output file path for the edge list",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=20,
        help="Print progress every N tree files (0 to disable)",
    )
    parser.add_argument(
        "--debug-samples",
        type=int,
        default=0,
        help="Print first N raw lines with regex match result (for debugging)",
    )

    args = parser.parse_args()

    print("[info] script started", flush=True)

    edges = read_undirected_edges(
        args.dataset_dir, progress_every=args.progress_every, debug_samples=args.debug_samples
    )
    print(f"[info] unique undirected edges={len(edges)}", flush=True)

    adj = build_adjacency_list(edges)
    print(f"[info] unique nodes(with degree>0)={len(adj)}", flush=True)

    lcc_nodes = find_largest_connected_component(adj)
    print(f"[info] LCC nodes={len(lcc_nodes)}", flush=True)

    lcc_edges = filter_edges_by_nodes(edges, lcc_nodes)
    print(f"[info] LCC edges={len(lcc_edges)}", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_edge_list(args.output, lcc_edges)
    print(f"[info] wrote: {args.output.resolve()}", flush=True)
    print("[info] Done!", flush=True)


if __name__ == "__main__":
    main()
