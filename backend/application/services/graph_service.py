import csv
import os
import re
from typing import Dict, List, Tuple, Optional


def _safe_float(x: str) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None


def _parse_csv(abs_path: str, max_edges: Optional[int]) -> Tuple[List[Dict], List[Dict], bool]:
    nodes_set = set()
    edges: List[Dict] = []
    truncated = False

    with open(abs_path, 'r', encoding='utf-8', newline='') as f:
        # 优先尝试按表头解析
        reader = csv.DictReader(f)
        fieldnames = [fn.lower().strip() for fn in (reader.fieldnames or [])]
        has_header = 'source' in fieldnames and 'target' in fieldnames

        if has_header:
            for row in reader:
                if max_edges is not None and len(edges) >= max_edges:
                    truncated = True
                    break
                s = str(row.get('source', '')).strip()
                t = str(row.get('target', '')).strip()
                if not s or not t:
                    continue
                w = row.get('weight')
                weight = _safe_float(w) if w is not None else None
                nodes_set.add(s)
                nodes_set.add(t)
                edge = {"source": s, "target": t}
                if weight is not None:
                    edge["weight"] = weight
                edges.append(edge)
        else:
            # 无表头时，回退为普通行解析
            f.seek(0)
            raw_reader = csv.reader(f)
            for row in raw_reader:
                if max_edges is not None and len(edges) >= max_edges:
                    truncated = True
                    break
                if not row:
                    continue
                # 取前两列为 source/target，第三列可选 weight
                s = str(row[0]).strip() if len(row) > 0 else ''
                t = str(row[1]).strip() if len(row) > 1 else ''
                if not s or not t:
                    continue
                weight = _safe_float(row[2]) if len(row) > 2 else None
                nodes_set.add(s)
                nodes_set.add(t)
                edge = {"source": s, "target": t}
                if weight is not None:
                    edge["weight"] = weight
                edges.append(edge)

    nodes = [{"id": nid, "label": nid} for nid in nodes_set]
    return nodes, edges, truncated


def _parse_txt(abs_path: str, max_edges: Optional[int]) -> Tuple[List[Dict], List[Dict], bool]:
    nodes_set = set()
    edges: List[Dict] = []
    truncated = False

    splitter = re.compile(r"[\s,\t;]+")

    with open(abs_path, 'r', encoding='utf-8') as f:
        for line in f:
            if max_edges is not None and len(edges) >= max_edges:
                truncated = True
                break
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p for p in splitter.split(line) if p]
            if len(parts) < 2:
                continue
            s, t = parts[0].strip(), parts[1].strip()
            if not s or not t:
                continue
            weight = _safe_float(parts[2]) if len(parts) > 2 else None
            nodes_set.add(s)
            nodes_set.add(t)
            edge = {"source": s, "target": t}
            if weight is not None:
                edge["weight"] = weight
            edges.append(edge)

    nodes = [{"id": nid, "label": nid} for nid in nodes_set]
    return nodes, edges, truncated


def _parse_multilayer_txt(abs_path: str, max_edges: Optional[int]) -> Tuple[List[Dict], bool]:
    layers = {}
    total_edges = 0
    truncated = False
    splitter = re.compile(r"[\s,\t;]+")

    with open(abs_path, 'r', encoding='utf-8') as f:
        for line in f:
            if max_edges is not None and total_edges >= max_edges:
                truncated = True
                break
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p for p in splitter.split(line) if p]
            if len(parts) < 3:  # layer, source, target
                continue

            layer_id, s, t = parts[0].strip(), parts[1].strip(), parts[2].strip()
            if not layer_id or not s or not t:
                continue

            if layer_id not in layers:
                layers[layer_id] = {'nodes_set': set(), 'edges': []}

            weight = _safe_float(parts[3]) if len(parts) > 3 else None
            layers[layer_id]['nodes_set'].add(s)
            layers[layer_id]['nodes_set'].add(t)
            edge = {"source": s, "target": t}
            if weight is not None:
                edge["weight"] = weight
            layers[layer_id]['edges'].append(edge)
            total_edges += 1

    result_layers = []
    for layer_id, data in sorted(layers.items()):
        nodes = [{"id": nid, "label": nid} for nid in data['nodes_set']]
        result_layers.append({
            "layer_id": layer_id,
            "nodes": nodes,
            "edges": data['edges'],
            "meta": {
                "nodes": len(nodes),
                "edges": len(data['edges'])
            }
        })

    return result_layers, truncated


def parse_graph_from_file(abs_path: str, ext: str, max_edges: Optional[int] = None, force_multilayer: bool = False) -> Dict:
    ext = (ext or '').lower().lstrip('.')
    if not os.path.exists(abs_path):
        raise FileNotFoundError("文件不存在")

    if force_multilayer:
        layers, truncated = _parse_multilayer_txt(abs_path, max_edges)
        # For overall metrics, we can aggregate node and edge counts
        total_nodes = len(set(n['id'] for layer in layers for n in layer['nodes']))
        total_edges = sum(len(layer['edges']) for layer in layers)
        return {
            "type": "multilayer",
            "layers": layers,
            "meta": {
                "nodes": total_nodes,
                "edges": total_edges,
                "layers_count": len(layers),
                "truncated": truncated,
                "max_edges": max_edges
            }
        }

    if ext == 'csv':
        nodes, edges, truncated = _parse_csv(abs_path, max_edges)
    elif ext in ('txt',):
        nodes, edges, truncated = _parse_txt(abs_path, max_edges)
    else:
        raise ValueError('暂不支持的文件类型: ' + ext)

    # 构建返回结构
    return {
        "type": "singlelayer",
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "nodes": len(nodes),
            "edges": len(edges),
            "truncated": truncated,
            "max_edges": max_edges
        }
    }
