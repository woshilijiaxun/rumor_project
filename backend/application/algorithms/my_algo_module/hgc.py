
__author__ = 'jiaxun Li'
import numpy as np
import time
import networkx as nx
import itertools
import random
import math
import statistics
import pandas as pd

from application.algorithms.my_algo_module import cr

from typing import Any, Dict



def cal_hgc(G: nx.Graph) -> Dict[int, float]:
    """
    HGC主算法封装函数
    保持原有代码逻辑不变，将所有计算步骤封装，返回最终的hgc分数字典
    """
    # ============ 原代码中的依赖函数定义（这里直接使用，保持原样）============
    def each_order_neighbor(G, node, n):
        neighbors = []
        for i in range(1, n + 1):
            neighbors.append(find_n_order_neighbor(G, node, i))
            if i != 1:
                neighbors[i - 1] -= neighbors[i - 2]
        return neighbors

    def find_n_order_neighbor(G, node, n):
        source_node = node
        all_order_edges = nx.bfs_edges(G, source_node, depth_limit=n)
        all_order_neighbors = {source_node} | set(v for u, v in all_order_edges)
        all_order_neighbors.discard(node)
        return all_order_neighbors

    def middle_node(G, node1, node2):
        start_neighbors = list(G.neighbors(node1))
        end_neighbors = list(G.neighbors(node2))
        middle_nodes = list(set(start_neighbors) & set(end_neighbors))
        if len(middle_nodes) == 1:
            return middle_nodes[0]
        else:
            degrees = {node: G.degree(node) for node in middle_nodes}
            min_degree_node = min(degrees, key=degrees.get)
            return min_degree_node

    def ED(G):
        ED_dict = {}
        for node in G.nodes():
            all_neighbors = each_order_neighbor(G, node, 2)
            ed1 = {}
            for nei1 in all_neighbors[0]:
                D = 1 - math.log(1 / G.degree(node), 10)
                ed1[nei1] = round(D, 4)
            ED_dict[node] = ed1

        for node in G.nodes():
            all_neighbors = each_order_neighbor(G, node, 2)
            ed2 = {}
            for nei2 in all_neighbors[1]:
                middle_nodes = middle_node(G, node, nei2)
                D = ED_dict[node][middle_nodes] + 1 - math.log(1 / G.degree(middle_nodes), 10)
                ed2[nei2] = round(D, 4)
            ED_dict[node].update(ed2)
        return ED_dict

    def SH(G):
        # 重要：网络节点标签可能不是 0..n-1 连续整数（例如你的 uid 是大整数）。
        # 因此必须使用真实的节点列表作为 nodelist，并且返回的键也要是真实节点 id，
        # 否则会触发：Node 0 in nodelist is not in G，且后续 sh[node] 会取不到。
        nodelist = list(G.nodes())
        num = len(nodelist)

        A = np.array(nx.adjacency_matrix(G, nodelist=nodelist).todense(), dtype=float)

        # 归一化：按列求和；如果某列全为 0（理论上孤立点），避免除以 0
        col_sums = A.sum(axis=0)
        col_sums[col_sums == 0] = 1.0
        A = A / col_sums.reshape(-1, 1)

        out: Dict[int, float] = {}
        for i in range(num):
            node_i = nodelist[i]
            n_idx = np.where(A[i] > 0)[0]
            c_i = 0.0
            for j in n_idx:
                com_n_idx = np.where(np.logical_and(A[i] > 0, A[j] > 0))[0]
                # 共享邻居上的路径项 + 直接连接项
                tmp = sum([A[i][k] * A[k][j] for k in com_n_idx]) + A[i][j]
                c_i += tmp * tmp
            out[node_i] = round(c_i, 4)
        return out

    # ============ 计算流程（复制原代码逻辑，但移除所有print）============
    
    # 1. 计算必要的中间指标
    degrees = dict(G.degree())
    ks = nx.core_number(G)
    s_ks = dict(sorted(ks.items(), key=lambda x: x[1], reverse=True))
    ED_dict = ED(G)
    sh = SH(G)
    
    # 2. 计算CR
    
    cr_list = cr.compute_cycle_ratio(G)
    
    ks = nx.core_number(G)

    s_ks = dict(sorted(ks.items(),key=lambda x:x[1],reverse=True))
    # 3. 计算DK（原代码逻辑）
    def bigger_ks_nodes(node, neighbors):
        return [nei for nei in neighbors if s_ks[nei] > s_ks[node]]
    
    DK = {}
    for node in G.nodes():
        neighbors = find_n_order_neighbor(G, node, 2)
        length1 = len(neighbors)
        new_neighbors = bigger_ks_nodes(node, neighbors)
        length2 = len(new_neighbors)
        if length2 == 0:
            length2 = 1
        Y = length2 / length1
        s = 0
        for nei in neighbors:
            s += degrees[nei]
            
        DK[node] = degrees[node]  # 注意：原代码中Y和s计算了但未使用
    
    # 4. 计算LCGM（原代码逻辑）
    LCGM = {}
    for node in G.nodes():
        neighbors = each_order_neighbor(G, node, 2)
        s = 0
        d = 1
        for nei in neighbors:
            for n in nei:
                if n in ED_dict[node]:
                    s += DK[node] * DK[n] / (ED_dict[node][n] ** 2)
            d += 1
            s *= math.exp(-sh[node])
        LCGM[node] = round(s, 4)
    
    average_lcgm = sum(LCGM.values()) / len(LCGM)
    
    # 5. 计算RCP（原代码逻辑）
    I0 = {node: cr_list[node] for node in G.nodes()}
    I1, I2, I3 = {}, {}, {}
    
    for node in G.nodes():
        nei = list(G.neighbors(node))
        I1[node] = sum(I0[n] for n in nei) / (1 ** 2) if nei else 0
    
    for node in G.nodes():
        nei = list(G.neighbors(node))
        I2[node] = sum(I1[n] for n in nei) / (2 ** 2) if nei else 0
    
    for node in G.nodes():
        nei = list(G.neighbors(node))
        I3[node] = sum(I2[n] for n in nei) / (3 ** 2) if nei else 0
    
    RCP = {}
    for node in G.nodes():
        RCP[node] = I1[node] + I2[node] + I3[node]
        RCP[node] *= math.exp(-sh[node])
    
    average_rcp = sum(RCP.values()) / len(RCP)
    
    # 6. 计算最终HGC
    gama = average_lcgm / average_rcp
    hgc_result = {}
    for node in G.nodes():
        hgc_result[node] = LCGM[node] + gama * RCP[node]
    
    return dict(sorted(hgc_result.items(), key=lambda x: x[1], reverse=True))
