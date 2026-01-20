# -*- coding: utf-8 -*-
"""
这是一个独立的脚本，用于运行 MGNN_AL 算法。
它整合了所有必要的函数，对外只暴露 MGNN_AL 函数。
"""

import networkx as nx
import dgl
from dgl import add_self_loop
import torch
import torch.nn as nn
import numpy as np
import time
import copy
import os


# ==============================================================================
# Section 1: 来自 Utils.py 的核心函数
# ==============================================================================

def load_multilayer_graph(path):
    """加载多层网络图"""
    G = []
    with open(path, 'r') as text:
        for line in text:
            vertices = line.strip().split(' ')
            if len(vertices) != 4:
                raise ValueError(f"Invalid line format: {line}")

            layer = int(vertices[0])
            source = int(vertices[1])
            target = int(vertices[2])
            weight = int(vertices[3])

            while len(G) < layer:
                G.append(nx.Graph())

            G[layer - 1].add_edge(source, target, weight=weight)

    for graph in G:
        graph.remove_edges_from(nx.selfloop_edges(graph))

    return G, len(G)

def get_dgl_g_input_test(G0):
    """为DGL图生成节点特征"""
    G = copy.deepcopy(G0)
    input_features = torch.ones(len(G), 5)
    for i in G.nodes():
        neighbors = list(G.neighbors(i))
        input_features[i, 0] = G.degree[i]
        if neighbors:
            input_features[i, 1] = sum(G.degree[j] for j in neighbors) / len(neighbors)
            input_features[i, 2] = sum(nx.clustering(G, j) for j in neighbors) / len(neighbors)
        else:
            input_features[i, 1] = 0
            input_features[i, 2] = 0

    try:
        e = nx.eigenvector_centrality(G, max_iter=10000)
    except nx.PowerIterationFailedConvergence:
        e = {node: 1.0 / len(G) for node in G.nodes()}
        
    k = nx.core_number(G)
    for i in G.nodes():
        input_features[i, 3] = e.get(i, 0)
        input_features[i, 4] = k.get(i, 0)

    for i in range(input_features.shape[1]):
        max_val = torch.max(input_features[:, i])
        if max_val > 0:
            input_features[:, i] = input_features[:, i] / max_val
    return input_features


# ==============================================================================
# Section 2: MGNN-AL（推理版，无SIR/无主动学习）
# ==============================================================================

def MGNN_AL(Gs):
    """\
    MGNN-AL 推理版：仅输入图对象，不需要 nodes_num、也不需要 SIR 标签。

    Args:
        Gs: networkx.Graph 或 list[networkx.Graph]
            - 单层网络：传入一个 nx.Graph
            - 多层网络：传入一个由多个 nx.Graph 组成的列表
        model_path: str, optional
            - 预训练模型路径，默认使用同目录下 'mgnn-al_model.pth'

    Returns:
        tuple: (pre_avg_influence_dict, total_time)
            - pre_avg_influence_dict: dict，键为原始节点ID，值为预测影响力分数（已按分数降序排序）
            - total_time: float，总耗时（秒）
    """
    # 加载预训练模型
   
    # 使用基于当前文件目录的绝对路径，避免因启动目录(cwd)不同导致找不到模型文件
    _base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(_base_dir, "mgnn-al_model.pth")
    # 模型配置（与保存的 state_dict 匹配）
    num_heads = 8  # 每层的 head 数
    num_layer = 3  # GAT 层数
    heads = [num_heads] * (num_layer - 1) + [1]  # 最后一层 1 个 head

    gat_para = {
        "in_dim": 5,         # 输入特征维度
        "out_dim": 32,       # 输出特征维度
        "embed_dim": 32,     # 嵌入维度
        "heads": heads,      # 每层的 head 数
        "num_layer": num_layer,
        "activation": "elu", # 激活函数
        "bias": True,        # 是否使用偏置
        "dropout": 0.1       # Dropout 概率
    }

    gatnet_para = {
        "out_dim": 1,        # 输出维度
        "hidden_dim": 32,    # 隐藏层维度
        "activation": nn.LeakyReLU()  # 激活函数
    }
    
    #gatv2 = GATv3Net(gatnet_para, gat_para)
    #gatv2 = GraphSAGE()
    from application.algorithms.my_algo_module.MGNN_AL.Model import CombinedModel
   
    model = CombinedModel(gatnet_para,gat_para)
    
    
    # 加载 state_dict
    state_dict = torch.load(model_path)
    model.load_state_dict(state_dict)
    

    if isinstance(Gs, nx.Graph):
        Gs = [Gs]
    if not isinstance(Gs, (list, tuple)) or len(Gs) == 0:
        raise ValueError("Gs 必须是 nx.Graph 或非空的 list[nx.Graph]")

    total_layers = len(Gs)
    stime = time.time()

    # 统一节点ID空间：用“并集节点集”作为全局节点集合
    all_nodes = set()
    for g in Gs:
        all_nodes.update(list(g.nodes()))
    all_nodes = sorted(all_nodes)
    nodes_num = len(all_nodes)

    global_id = {node: idx for idx, node in enumerate(all_nodes)}
    global_rev = {idx: node for node, idx in global_id.items()}

    # 逐层转换为 0..N-1 的一致编号，并提取特征
    relabeled_layers = []
    node_features_list = []
    dgl_graphs = []

    for layer_g in Gs:
        g_copy = layer_g.copy()
        g_copy.remove_edges_from(nx.selfloop_edges(g_copy))

        # 将该层节点映射到全局ID；缺失节点不加入图
        mapping = {n: global_id[n] for n in g_copy.nodes() if n in global_id}
        g_int = nx.relabel_nodes(g_copy, mapping)

        # 构造一个包含全局所有节点的图：补齐缺失节点为孤立点
        g_full = nx.Graph()
        g_full.add_nodes_from(range(nodes_num))
        g_full.add_edges_from(g_int.edges(data=True))

        relabeled_layers.append(g_full)
        node_features_list.append(get_dgl_g_input_test(g_full))
        dg = dgl.from_networkx(g_full)
        # DGL 的 GAT 系列对 0-in-degree 节点会报错；加 self-loop 可保证每个节点至少有 1 条入边
        dg = add_self_loop(dg)
        dgl_graphs.append(dg)

    

    model.eval()
    layer_scores = {}

    with torch.no_grad():
        for i in range(total_layers):
            pred = model(dgl_graphs[i], node_features_list[i])  # shape: [N, 1]
            pred = pred.flatten().detach().cpu().numpy().tolist()
            layer_scores[i + 1] = {node_id: float(pred[node_id]) for node_id in range(nodes_num)}

    # 多层平均
    avg_scores = {node_id: 0.0 for node_id in range(nodes_num)}
    for _, scores in layer_scores.items():
        for node_id, v in scores.items():
            avg_scores[node_id] += v
    for node_id in avg_scores:
        avg_scores[node_id] /= total_layers

    # 映射回原始节点ID，并排序
    pre_avg_influence_dict = {global_rev[node_id]: score for node_id, score in avg_scores.items()}
    pre_avg_influence_dict = dict(sorted(pre_avg_influence_dict.items(), key=lambda x: x[1], reverse=True))

    total_time = time.time() - stime
    return pre_avg_influence_dict


