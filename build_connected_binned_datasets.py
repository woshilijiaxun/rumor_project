#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from statistics import mean, median
from typing import Dict, List, Optional, Set, Tuple

# 事件传播树行格式：['uid','tid','delay']->['uid2','tid2','delay2']
EDGE_RE = re.compile(
    r"\['(?P<uid>[^']+)'\s*,\s*'[^']+'\s*,\s*'(?P<delay>[^']+)'\]\s*->\s*"
    r"\['(?P<uid2>[^']+)'\s*,\s*'[^']+'\s*,\s*'(?P<delay2>[^']+)'\]"
)


def parse_delay(x: str) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None


def iter_true_event_ids(dataset_dir: Path) -> List[str]:
    ids: List[str] = []
    with (dataset_dir / "label.txt").open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = (line or "").strip()
            if s.startswith("true:"):
                ids.append(s.split(":", 1)[1])
    return ids


def read_tree_event(
    dataset_dir: Path, event_id: str
) -> Tuple[Set[Tuple[int, int]], Dict[int, float], Dict[int, Set[int]]]:
    tree_path = dataset_dir / "tree" / f"{event_id}.txt"
    base_edges: Set[Tuple[int, int]] = set()
    min_delay: Dict[int, float] = {}
    children_by_parent: Dict[int, Set[int]] = defaultdict(set)

    with tree_path.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            m = EDGE_RE.search((raw or "").strip())
            if not m:
                continue
            u1 = m.group("uid")
            u2 = m.group("uid2")
            d1 = parse_delay(m.group("delay"))
            d2 = parse_delay(m.group("delay2"))

            if u1 != "ROOT":
                try:
                    ui = int(u1)
                    if d1 is not None:
                        prev = min_delay.get(ui, float("inf"))
                        if d1 < prev:
                            min_delay[ui] = d1
                except Exception:
                    pass
            if u2 != "ROOT":
                try:
                    vi = int(u2)
                    if d2 is not None:
                        prev = min_delay.get(vi, float("inf"))
                        if d2 < prev:
                            min_delay[vi] = d2
                except Exception:
                    pass

            if u1 != "ROOT" and u2 != "ROOT":
                try:
                    ui = int(u1)
                    vi = int(u2)
                    if ui != vi:
                        children_by_parent[ui].add(vi)
                except Exception:
                    pass

            if u1 == "ROOT" or u2 == "ROOT":
                continue
            try:
                ui = int(u1)
                vi = int(u2)
            except Exception:
                continue
            if ui == vi:
                continue
            if ui > vi:
                ui, vi = vi, ui
            base_edges.add((ui, vi))

    return base_edges, min_delay, children_by_parent


def build_adjacency(edges: Set[Tuple[int, int]]) -> Dict[int, Set[int]]:
    adj: Dict[int, Set[int]] = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return adj


def degrees_from_adj(adj: Dict[int, Set[int]]) -> Dict[int, int]:
    return {n: len(nb) for n, nb in adj.items()}


def connected_components(adj: Dict[int, Set[int]]) -> List[Set[int]]:
    visited: Set[int] = set()
    comps: List[Set[int]] = []
    for node in adj.keys():
        if node in visited:
            continue
        comp: Set[int] = set()
        q = deque([node])
        visited.add(node)
        while q:
            cur = q.popleft()
            comp.add(cur)
            for nb in adj.get(cur, set()):
                if nb not in visited:
                    visited.add(nb)
                    q.append(nb)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    return comps


def bin_name(lo: int, hi: int) -> str:
    return f"bin_{lo}_{hi}"


def brother_window_enhance(
    edges: Set[Tuple[int, int]],
    children_by_parent: Dict[int, Set[int]],
    min_delay: Dict[int, float],
    window_k: int,
    max_children_for_parent: int = 0,
) -> Set[Tuple[int, int]]:
    out = set(edges)
    if window_k <= 0:
        return out
    for _, children in children_by_parent.items():
        ch = list(children)
        if len(ch) < 2:
            continue
        if max_children_for_parent and len(ch) > max_children_for_parent:
            continue
        ch.sort(key=lambda cid: min_delay.get(cid, float("inf")))
        L = len(ch)
        for i in range(L):
            for j in range(i + 1, min(L, i + 1 + window_k)):
                a, b = ch[i], ch[j]
                if a == b:
                    continue
                if a > b:
                    a, b = b, a
                out.add((a, b))
    return out


def connect_components_with_bridges(
    edges: Set[Tuple[int, int]],
    min_delay: Dict[int, float],
    rng: random.Random,
    extra_bridges_per_merge: int,
) -> Set[Tuple[int, int]]:
    out = set(edges)
    adj = build_adjacency(out)
    comps = connected_components(adj)
    if len(comps) <= 1:
        return out

    deg = degrees_from_adj(adj)

    def pick_rep(comp: Set[int]) -> int:
        return sorted(
            comp,
            key=lambda nid: (-deg.get(nid, 0), min_delay.get(nid, float("inf")), nid),
        )[0]

    reps = [pick_rep(c) for c in comps]
    for i in range(len(reps) - 1):
        u, v = reps[i], reps[i + 1]
        if u > v:
            u, v = v, u
        out.add((u, v))
        for _ in range(max(0, extra_bridges_per_merge)):
            a = rng.choice(tuple(comps[i]))
            b = rng.choice(tuple(comps[i + 1]))
            if a == b:
                continue
            if a > b:
                a, b = b, a
            out.add((a, b))
    return out


def truncate_to_max_nodes_connected(
    edges: Set[Tuple[int, int]],
    min_delay: Dict[int, float],
    target_max_nodes: int,
) -> Tuple[Set[Tuple[int, int]], Set[int]]:
    adj = build_adjacency(edges)
    nodes = list(adj.keys())
    if len(nodes) <= target_max_nodes:
        return edges, set(nodes)

    deg = degrees_from_adj(adj)
    seed = sorted(nodes, key=lambda nid: (-deg.get(nid, 0), min_delay.get(nid, float("inf")), nid))[0]

    picked: Set[int] = {seed}
    q = deque([seed])
    while q and len(picked) < target_max_nodes:
        cur = q.popleft()
        for nb in adj.get(cur, set()):
            if nb in picked:
                continue
            picked.add(nb)
            q.append(nb)
            if len(picked) >= target_max_nodes:
                break

    out_edges = {(u, v) for (u, v) in edges if u in picked and v in picked}
    return out_edges, picked


def rebalance_root_hub_degree(
    edges: Set[Tuple[int, int]],
    min_delay: Dict[int, float],
    max_root_degree: int,
) -> Set[Tuple[int, int]]:
    if max_root_degree <= 0:
        return edges

    out = set(edges)
    adj = build_adjacency(out)
    if not adj:
        return out

    deg = degrees_from_adj(adj)
    root = sorted(adj.keys(), key=lambda nid: (min_delay.get(nid, float("inf")), -deg.get(nid, 0), nid))[0]
    neighbors = list(adj.get(root, set()))
    if len(neighbors) <= max_root_degree:
        return out

    neighbors_sorted = sorted(
        neighbors,
        key=lambda nid: (min_delay.get(nid, float("inf")), -deg.get(nid, 0), nid),
    )
    kept_neighbors = set(neighbors_sorted[:max_root_degree])
    overflow_neighbors = neighbors_sorted[max_root_degree:]

    added_load: Dict[int, int] = defaultdict(int)

    for nb in overflow_neighbors:
        u, v = (root, nb) if root < nb else (nb, root)
        out.discard((u, v))

        anchors = sorted(
            kept_neighbors,
            key=lambda a: (
                deg.get(a, 0) + added_load[a],
                abs(min_delay.get(a, float("inf")) - min_delay.get(nb, float("inf"))),
                a,
            ),
        )
        for anchor in anchors:
            if anchor == nb:
                continue
            x, y = (anchor, nb) if anchor < nb else (nb, anchor)
            if (x, y) in out:
                continue
            out.add((x, y))
            added_load[anchor] += 1
            break

    return out


def label_propagation_communities(
    adj: Dict[int, Set[int]],
    rng: random.Random,
    max_iter: int = 15,
) -> Dict[int, int]:
    labels: Dict[int, int] = {n: n for n in adj}
    nodes = list(adj.keys())
    if not nodes:
        return labels

    for _ in range(max_iter):
        changed = 0
        rng.shuffle(nodes)
        for n in nodes:
            nbs = adj.get(n, set())
            if not nbs:
                continue
            cnt = Counter(labels[x] for x in nbs)
            top = max(cnt.values())
            candidates = [lab for lab, c in cnt.items() if c == top]
            new_lab = rng.choice(candidates)
            if new_lab != labels[n]:
                labels[n] = new_lab
                changed += 1
        if changed == 0:
            break
    return labels


def try_add_edge(out: Set[Tuple[int, int]], u: int, v: int) -> bool:
    if u == v:
        return False
    if u > v:
        u, v = v, u
    if (u, v) in out:
        return False
    out.add((u, v))
    return True


def weighted_choice(nodes: List[int], weights: List[float], rng: random.Random) -> Optional[int]:
    if not nodes:
        return None
    s = sum(weights)
    if s <= 0:
        return rng.choice(nodes)
    r = rng.random() * s
    acc = 0.0
    for n, w in zip(nodes, weights):
        acc += w
        if acc >= r:
            return n
    return nodes[-1]


def augment_complex_network(
    edges: Set[Tuple[int, int]],
    min_delay: Dict[int, float],
    rng: random.Random,
    intra_prob: float,
    shortcut_prob: float,
    triadic_prob: float,
    pref_alpha: float,
    pref_beta: float,
    extra_edge_ratio: float,
) -> Set[Tuple[int, int]]:
    out = set(edges)
    if not out:
        return out

    adj = build_adjacency(out)
    deg = degrees_from_adj(adj)
    labels = label_propagation_communities(adj, rng)

    comm_nodes: Dict[int, List[int]] = defaultdict(list)
    for n, c in labels.items():
        comm_nodes[c].append(n)

    nodes = list(adj.keys())
    target_add = int(max(1, len(out) * max(0.0, extra_edge_ratio)))
    added = 0
    attempts = 0
    max_attempts = max(5000, target_add * 30)

    delays = [d for d in min_delay.values() if math.isfinite(d)]
    tau = (median(delays) - min(delays)) if delays else 1.0
    if tau <= 0:
        tau = 1.0

    while added < target_add and attempts < max_attempts:
        attempts += 1
        u = rng.choice(nodes)

        if rng.random() < triadic_prob:
            nbs = list(adj.get(u, []))
            if nbs:
                mid = rng.choice(nbs)
                nbs2 = [x for x in adj.get(mid, []) if x != u]
                if nbs2:
                    v = rng.choice(nbs2)
                    if try_add_edge(out, u, v):
                        adj[u].add(v)
                        adj[v].add(u)
                        deg[u] += 1
                        deg[v] += 1
                        added += 1
                    continue

        same = comm_nodes.get(labels.get(u, u), [])
        diff = [x for x in nodes if labels.get(x, x) != labels.get(u, u)]

        use_shortcut = rng.random() < shortcut_prob
        if (not use_shortcut and rng.random() < intra_prob) or not diff:
            cand = [x for x in same if x != u and x not in adj[u]]
        else:
            cand = [x for x in diff if x != u and x not in adj[u]]

        if not cand:
            continue

        ud = min_delay.get(u, 0.0)
        weights: List[float] = []
        for v in cand:
            vd = min_delay.get(v, 0.0)
            sim = math.exp(-abs(ud - vd) / tau)
            if use_shortcut:
                sim = max(0.1, 1.0 - sim)
            w = ((deg.get(v, 0) + pref_alpha) ** pref_beta) * sim
            weights.append(max(w, 1e-8))

        v = weighted_choice(cand, weights, rng)
        if v is None:
            continue

        if try_add_edge(out, u, v):
            adj[u].add(v)
            adj[v].add(u)
            deg[u] += 1
            deg[v] += 1
            added += 1

    return out


def local_clustering(adj: Dict[int, Set[int]], u: int) -> float:
    nbs = list(adj.get(u, set()))
    k = len(nbs)
    if k < 2:
        return 0.0
    triangles = 0
    nbset = set(nbs)
    for i in range(k):
        a = nbs[i]
        for j in range(i + 1, k):
            b = nbs[j]
            if b in adj.get(a, set()):
                triangles += 1
    return (2.0 * triangles) / (k * (k - 1))


def average_clustering(adj: Dict[int, Set[int]]) -> float:
    if not adj:
        return 0.0
    return mean(local_clustering(adj, n) for n in adj)


def bfs_avg_path_length(adj: Dict[int, Set[int]], sample_nodes: int = 80) -> float:
    nodes = list(adj.keys())
    n = len(nodes)
    if n <= 1:
        return 0.0
    if n > sample_nodes:
        rng = random.Random(0)
        rng.shuffle(nodes)
        nodes = nodes[:sample_nodes]

    dsum = 0
    pairs = 0
    for s in nodes:
        dist = {s: 0}
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj.get(u, set()):
                if v not in dist:
                    dist[v] = dist[u] + 1
                    q.append(v)
        for t, d in dist.items():
            if t != s:
                dsum += d
                pairs += 1
    return (dsum / pairs) if pairs else 0.0


def modularity(edges: Set[Tuple[int, int]], labels: Dict[int, int], deg: Dict[int, int]) -> float:
    m = len(edges)
    if m == 0:
        return 0.0
    two_m = 2.0 * m
    q = 0.0
    for u, v in edges:
        if labels.get(u) == labels.get(v):
            q += 1.0 - (deg.get(u, 0) * deg.get(v, 0) / two_m)
    return q / m


def estimate_gamma_mle(degrees: List[int], kmin: int = 2) -> float:
    vals = [k for k in degrees if k >= kmin]
    if len(vals) < 5:
        return float("nan")
    denom = sum(math.log(k / (kmin - 0.5)) for k in vals if k > 0)
    if denom <= 0:
        return float("nan")
    return 1.0 + len(vals) / denom


def graph_metrics(edges: Set[Tuple[int, int]], min_delay: Dict[int, float], rng: random.Random) -> Dict[str, float]:
    adj = build_adjacency(edges)
    deg = degrees_from_adj(adj)
    n = len(adj)
    m = len(edges)
    if n == 0:
        return {}

    comps = connected_components(adj)
    lcc = comps[0] if comps else set()
    lcc_ratio = len(lcc) / n if n else 0.0

    c = average_clustering(adj)
    l = bfs_avg_path_length(adj)
    avg_k = (2.0 * m / n) if n else 0.0
    p = (2.0 * m) / (n * (n - 1)) if n > 1 else 0.0

    c_rand = p
    l_rand = (math.log(n) / math.log(avg_k)) if avg_k > 1.01 and n > 2 else 0.0
    sigma = (c / c_rand) / (l / l_rand) if c_rand > 0 and l > 0 and l_rand > 0 else float("nan")

    labels = label_propagation_communities(adj, rng)
    q = modularity(edges, labels, deg)

    gamma = estimate_gamma_mle(list(deg.values()), kmin=2)

    root = sorted(adj.keys(), key=lambda nid: (min_delay.get(nid, float("inf")), -deg.get(nid, 0), nid))[0]
    root_deg_share = deg.get(root, 0) / max(1, n - 1)

    return {
        "nodes": n,
        "edges": m,
        "avg_degree": avg_k,
        "lcc_ratio": lcc_ratio,
        "clustering": c,
        "path_length": l,
        "small_world_sigma": sigma,
        "modularity": q,
        "gamma_mle_kmin2": gamma,
        "max_degree": max(deg.values()) if deg else 0,
        "root_degree_share": root_deg_share,
    }


def write_edgelist(path: Path, edges: Set[Tuple[int, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for u, v in sorted(edges):
            f.write(f"{u} {v}\n")


def write_importance(path: Path, edges: Set[Tuple[int, int]], min_delay: Dict[int, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    adj = build_adjacency(edges)
    deg = degrees_from_adj(adj)
    nodes = list(adj.keys())
    nodes.sort(key=lambda nid: (-deg.get(nid, 0), min_delay.get(nid, float("inf")), nid))
    with path.open("w", encoding="utf-8") as f:
        for rank, nid in enumerate(nodes, start=1):
            f.write(f"{rank} {nid} {min_delay.get(nid, float('inf'))} {deg.get(nid, 0)}\n")


def pick_root_degree_cap(node_count: int, default_cap: int) -> int:
    if node_count <= 200:
        return min(default_cap, 50)
    if node_count <= 600:
        return min(default_cap, 90)
    if node_count <= 1000:
        return min(default_cap, 120)
    return min(default_cap, 160)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", type=Path, default=Path("rumor_detection_acl2017/binned_complex_k6"))
    parser.add_argument("--datasets", type=str, default="twitter15")
    parser.add_argument("--window-k", type=int, default=6)
    parser.add_argument("--max-children-for-parent", type=int, default=0)
    parser.add_argument("--extra-bridges", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--truncate-max", type=int, default=2000)
    parser.add_argument("--max-root-degree", type=int, default=140)

    parser.add_argument("--intra-prob", type=float, default=0.85)
    parser.add_argument("--shortcut-prob", type=float, default=0.06)
    parser.add_argument("--triadic-prob", type=float, default=0.35)
    parser.add_argument("--pref-alpha", type=float, default=1.0)
    parser.add_argument("--pref-beta", type=float, default=1.0)
    parser.add_argument("--extra-edge-ratio", type=float, default=0.18)
    args = parser.parse_args()

    bins = [(100, 200), (200, 600), (600, 1000), (1000, 2000)]
    rng = random.Random(args.seed)

    for lo, hi in bins:
        (args.out_root / bin_name(lo, hi) / "edgelist").mkdir(parents=True, exist_ok=True)
        (args.out_root / bin_name(lo, hi) / "importance").mkdir(parents=True, exist_ok=True)

    kept = Counter()
    total = 0
    metric_records: List[Dict[str, object]] = []

    base_root = Path("rumor_detection_acl2017")
    dataset_names = [x.strip() for x in (args.datasets or "").split(",") if x.strip()]
    for dname in dataset_names:
        ddir = base_root / dname
        if not ddir.is_dir():
            continue
        for event_id in iter_true_event_ids(ddir):
            total += 1
            base_edges, min_delay, children_by_parent = read_tree_event(ddir, event_id)
            if not base_edges:
                continue

            edges = brother_window_enhance(
                edges=base_edges,
                children_by_parent=children_by_parent,
                min_delay=min_delay,
                window_k=args.window_k,
                max_children_for_parent=args.max_children_for_parent,
            )
            edges = connect_components_with_bridges(
                edges=edges,
                min_delay=min_delay,
                rng=rng,
                extra_bridges_per_merge=args.extra_bridges,
            )
            edges, node_set = truncate_to_max_nodes_connected(edges, min_delay, args.truncate_max)
            vnum = len(node_set)
            if vnum < 2:
                continue

            root_cap = pick_root_degree_cap(vnum, args.max_root_degree)
            edges = rebalance_root_hub_degree(
                edges=edges,
                min_delay=min_delay,
                max_root_degree=root_cap,
            )

            edges = augment_complex_network(
                edges=edges,
                min_delay=min_delay,
                rng=rng,
                intra_prob=args.intra_prob,
                shortcut_prob=args.shortcut_prob,
                triadic_prob=args.triadic_prob,
                pref_alpha=args.pref_alpha,
                pref_beta=args.pref_beta,
                extra_edge_ratio=args.extra_edge_ratio,
            )

            chosen = None
            for lo, hi in bins:
                if lo <= vnum <= hi:
                    chosen = (lo, hi)
                    break
            if not chosen:
                continue

            lo, hi = chosen
            tag = f"{dname}_{event_id}"
            write_edgelist(args.out_root / bin_name(lo, hi) / "edgelist" / f"{tag}.edgelist.txt", edges)
            write_importance(args.out_root / bin_name(lo, hi) / "importance" / f"{tag}.importance.txt", edges, min_delay)
            kept[bin_name(lo, hi)] += 1

            rec = graph_metrics(edges, min_delay=min_delay, rng=rng)
            rec["event"] = tag
            rec["bin"] = bin_name(lo, hi)
            metric_records.append(rec)

    metrics_path = args.out_root / "metrics_summary.json"
    aggregate_path = args.out_root / "metrics_aggregate.txt"

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metric_records, f, ensure_ascii=False, indent=2)

    by_bin: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for r in metric_records:
        by_bin[str(r.get("bin", "unknown"))].append(r)

    with aggregate_path.open("w", encoding="utf-8") as f:
        f.write(f"processed={total}\n")
        f.write(f"kept={dict(kept)}\n\n")
        for b in sorted(by_bin.keys()):
            rows = by_bin[b]
            if not rows:
                continue
            f.write(f"[{b}] n_events={len(rows)}\n")
            for key in [
                "nodes",
                "edges",
                "avg_degree",
                "lcc_ratio",
                "clustering",
                "path_length",
                "small_world_sigma",
                "modularity",
                "gamma_mle_kmin2",
                "max_degree",
                "root_degree_share",
            ]:
                vals = [float(x[key]) for x in rows if isinstance(x.get(key), (int, float)) and math.isfinite(float(x[key]))]
                if vals:
                    f.write(f"  {key}: mean={mean(vals):.4f}, median={median(vals):.4f}\n")
                else:
                    f.write(f"  {key}: NA\n")
            f.write("\n")

    print("[info] processed:", total)
    print("[info] kept:", dict(kept))
    print("[info] metrics json:", metrics_path)
    print("[info] aggregate:", aggregate_path)


if __name__ == "__main__":
    main()
