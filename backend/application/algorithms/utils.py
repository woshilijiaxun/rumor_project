import networkx as nx



def load_graph(path):    #加载单层网络
    G = nx.Graph()
    with open(path, 'r') as text:
        for line in text:
            vertices = line.strip().split(' ')
            source = int(vertices[0])
            target = int(vertices[-1])
            G.add_edge(source, target)
    return G



def load_multilayer_graph(path):
    # 兼容两种输入：
    # 1) 单层网络：node1 node2
    # 2) 多层网络：layer node1 node2 weight

    with open(path, 'r') as text:
        first_tokens = None
        for line in text:
            s = line.strip()
            if not s:
                continue
            first_tokens = s.split()
            break

        if first_tokens is None:
            return []

        text.seek(0)
        cols = len(first_tokens)

        # --- 单层网络（2列）---
        if cols == 2:
            G0 = nx.Graph()
            for line in text:
                s = line.strip()
                if not s:
                    continue
                parts = s.split()
                if len(parts) != 2:
                    raise ValueError(f"文件格式不一致，应为2列: {s}")
                source = int(parts[0])
                target = int(parts[1])
                G0.add_edge(source, target)

            G0.remove_edges_from(nx.selfloop_edges(G0))
            return [G0]

        # --- 多层网络（4列）---
        if cols == 4:
            G = []
            for line in text:
                s = line.strip()
                if not s:
                    continue
                parts = s.split()
                if len(parts) != 4:
                    raise ValueError(f"文件格式不一致，应为4列: {s}")

                layer = int(parts[0])  # 网络层（从1开始）
                source = int(parts[1])
                target = int(parts[2])
                weight = int(parts[3])

                while len(G) < layer:
                    G.append(nx.Graph())

                G[layer - 1].add_edge(source, target, weight=weight)

            for graph in G:
                graph.remove_edges_from(nx.selfloop_edges(graph))

            return G

        raise ValueError(f"不支持的文件格式：期望2列或4列，但首行是{cols}列: {' '.join(first_tokens)}")
