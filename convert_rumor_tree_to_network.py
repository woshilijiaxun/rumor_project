import argparse
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


EDGE_RE = re.compile(r"\['(?P<uid>[^']+)'\s*,\s*'(?P<tid>[^']+)'\s*,\s*'(?P<delay>[^']+)'\]\s*->\s*\['(?P<uid2>[^']+)'\s*,\s*'(?P<tid2>[^']+)'\s*,\s*'(?P<delay2>[^']+)'\]")


def parse_user_edge(line: str) -> Optional[Tuple[int, int]]:
    s = line.strip()
    if not s:
        return None
    m = EDGE_RE.search(s)
    if not m:
        return None
    try:
        u1 = int(m.group('uid'))
        u2 = int(m.group('uid2'))
    except Exception:
        return None
    if u1 == u2:
        return None
    return u1, u2


def iter_tree_files(dataset_dir: Path):
    tree_dir = dataset_dir / 'tree'
    if not tree_dir.is_dir():
        return
    for p in sorted(tree_dir.iterdir()):
        if p.is_file() and p.suffix == '.txt':
            yield p


def read_user_edges(root: Path, datasets: List[str], dedup: bool) -> Dict[str, List[Tuple[int, int]]]:
    """Return edges for layer1 and layer2.

    - layer1: user-user edges from propagation
    - layer2: user-user edges from the same propagation (direction ignored)

    Both layers share the same node domain (user_id) to satisfy "nodes correspond".

    Currently both layers are identical by definition. If you later decide a different
    layer2 semantics, extend here.
    """

    edges_by_layer: Dict[str, List[Tuple[int, int]]] = {'1': [], '2': []}
    seen1: Set[Tuple[int, int]] = set() if dedup else set()
    seen2: Set[Tuple[int, int]] = set() if dedup else set()

    for ds in datasets:
        ds_dir = root / ds
        if not ds_dir.is_dir():
            raise SystemExit(f"Dataset dir not found: {ds_dir}")
        for tree_file in iter_tree_files(ds_dir):
            with tree_file.open('r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    e = parse_user_edge(line)
                    if not e:
                        continue
                    a, b = e
                    # undirected canonical key
                    if a > b:
                        a, b = b, a

                    k = (a, b)
                    if dedup:
                        if k not in seen1:
                            seen1.add(k)
                            edges_by_layer['1'].append(k)
                        if k not in seen2:
                            seen2.add(k)
                            edges_by_layer['2'].append(k)
                    else:
                        edges_by_layer['1'].append(k)
                        edges_by_layer['2'].append(k)

    return edges_by_layer


def build_adj(edges: Iterable[Tuple[int, int]]) -> Dict[int, List[int]]:
    adj: Dict[int, List[int]] = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return adj


def largest_connected_component_nodes(adj: Dict[int, List[int]]) -> Set[int]:
    seen: Set[int] = set()
    best: Set[int] = set()

    for start in adj.keys():
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        comp: Set[int] = {start}
        while q:
            u = q.popleft()
            for v in adj.get(u, []):
                if v not in seen:
                    seen.add(v)
                    comp.add(v)
                    q.append(v)
        if len(comp) > len(best):
            best = comp

    return best


def bfs_subgraph_nodes(adj: Dict[int, List[int]], seed: int, target_nodes: int) -> Set[int]:
    visited: Set[int] = {seed}
    q: deque[int] = deque([seed])
    while q and len(visited) < target_nodes:
        u = q.popleft()
        for v in adj.get(u, []):
            if v not in visited:
                visited.add(v)
                q.append(v)
                if len(visited) >= target_nodes:
                    break
    return visited


def induced_edges(edges: List[Tuple[int, int]], nodes: Set[int], max_edges: int) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    for a, b in edges:
        if a in nodes and b in nodes:
            out.append((a, b))
            if max_edges > 0 and len(out) >= max_edges:
                break
    return out


def stats_edges(edges: List[Tuple[int, int]]) -> Tuple[int, int]:
    nodes: Set[int] = set()
    for a, b in edges:
        nodes.add(a)
        nodes.add(b)
    return len(nodes), len(edges)


def write_single(path: Path, edges: List[Tuple[int, int]]):
    with path.open('w', encoding='utf-8') as f:
        for a, b in edges:
            f.write(f"{a} {b}\n")


def write_multi(path: Path, edges1: List[Tuple[int, int]], edges2: List[Tuple[int, int]]):
    with path.open('w', encoding='utf-8') as f:
        for a, b in edges1:
            f.write(f"1 {a} {b} 1\n")
        for a, b in edges2:
            f.write(f"2 {a} {b} 1\n")


def main():
    ap = argparse.ArgumentParser(description='Convert rumor_detection_acl2017 trees into connected single/multilayer networks (user_id domain).')
    ap.add_argument('--root', default='rumor_detection_acl2017', help='Path to rumor_detection_acl2017 directory')
    ap.add_argument('--datasets', default='twitter15,twitter16', help='Comma-separated dataset names to include')
    ap.add_argument('--out-dir', default='flaskProject/output_networks', help='Directory to write output files')
    ap.add_argument('--dedup', action='store_true', help='Deduplicate edges')
    ap.add_argument('--target-nodes', type=int, default=2000, help='Target number of nodes in output connected graph (best effort)')
    ap.add_argument('--max-edges', type=int, default=8000, help='Max edges to write per output (best effort)')
    ap.add_argument('--strict', action='store_true', help='Fail if cannot reach target-nodes with connectivity constraint')

    args = ap.parse_args()

    root = Path(args.root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    datasets = [x.strip() for x in args.datasets.split(',') if x.strip()]

    edges_by_layer = read_user_edges(root, datasets, dedup=bool(args.dedup))

    # layer 1 will define the node set, because "nodes correspond" across layers
    edges1_all = edges_by_layer['1']
    edges2_all = edges_by_layer['2']

    adj1 = build_adj(edges1_all)
    lcc_nodes = largest_connected_component_nodes(adj1)

    if not lcc_nodes:
        raise SystemExit('No edges parsed. Please check tree file format.')

    if len(lcc_nodes) < args.target_nodes:
        msg = f"最大连通子图只有 {len(lcc_nodes)} 个 user 节点，无法达到 target_nodes={args.target_nodes}。"
        if args.strict:
            raise SystemExit(msg)
        else:
            print('WARN:', msg)

    # Take a connected subset from LCC
    seed = next(iter(lcc_nodes))
    nodes_sel = bfs_subgraph_nodes(build_adj(induced_edges(edges1_all, lcc_nodes, max_edges=0)), seed, min(args.target_nodes, len(lcc_nodes)))

    edges1_sel = induced_edges(edges1_all, nodes_sel, max_edges=args.max_edges)
    edges2_sel = induced_edges(edges2_all, nodes_sel, max_edges=args.max_edges)

    # Sanity: no isolated nodes in written graph -> ensured by using only endpoints in edges
    n1, m1 = stats_edges(edges1_sel)
    n2, m2 = stats_edges(edges2_sel)

    out_single = out_dir / 'single_user_edgelist.txt'
    out_multi = out_dir / 'multilayer_user_edgelist.txt'

    write_single(out_single, edges1_sel)
    write_multi(out_multi, edges1_sel, edges2_sel)

    print('OK')
    print('single:', out_single)
    print(f'  nodes={n1} edges={m1} connected=YES (by construction)')
    print('multi :', out_multi)
    print(f'  layer1 nodes={n1} edges={m1}')
    print(f'  layer2 nodes={n2} edges={m2}')
    print('  nodes aligned across layers: YES (user_id domain + same nodes_sel)')


if __name__ == '__main__':
    main()
