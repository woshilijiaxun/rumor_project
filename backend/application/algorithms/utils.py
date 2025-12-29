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
    # 创建一个动态扩展的多层网络列表
    G = []
    with open(path, 'r') as text:
        for line in text:
            vertices = line.strip().split(' ')
            if len(vertices) != 4:
                raise ValueError(f"Invalid line format: {line}")

            layer = int(vertices[0])  # 网络层
            source = int(vertices[1])  # 源节点
            target = int(vertices[2])  # 目标节点
            weight = int(vertices[3])  # 权重

            # 动态扩展图列表
            while len(G) < layer:
                G.append(nx.Graph())

            # 添加边并存储权重
            G[layer - 1].add_edge(source, target, weight=weight)

    # 移除自环
    for graph in G:
        graph.remove_edges_from(nx.selfloop_edges(graph))

    # 返回多层网络和实际的层数
    return G, len(G)