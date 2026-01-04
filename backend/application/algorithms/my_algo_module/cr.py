import networkx as nx
import itertools
from typing import Dict, Set, Tuple, List

def compute_cycle_ratio(G: nx.Graph) -> Dict[int, float]:
    """
    计算网络中每个节点的CycleRatio（循环比率）
    
    参数:
        G: networkx.Graph 图对象
        
    返回:
        {节点ID: CycleRatio值} 字典，值越大表示节点的环结构越重要
    """
    
    # ---------- 1. 初始化 ----------
    Mygraph = G.copy()
    NodeNum = Mygraph.number_of_nodes()
    
    # 不可能的长度常量
    DEF_IMPOSSLEN = NodeNum + 1
    
    # 存储结构初始化
    SmallestCycles: Set[Tuple] = set()
    NodeGirth: Dict[int, int] = {}
    CycLenDict: Dict[int, int] = {}
    CycleRatio: Dict[int, float] = {}
    SmallestCyclesOfNodes: Dict[int, Set[Tuple]] = {}
    
    # ---------- 2. 辅助函数 ----------
    def my_all_shortest_paths(G, source, target):
        """获取两点间所有最短路径"""
        pred = nx.predecessor(G, source)
        if target not in pred:
            raise nx.NetworkXNoPath(f"Target {target} cannot be reached")
        sources = {source}
        seen = {target}
        stack = [[target, 0]]
        top = 0
        while top >= 0:
            node, i = stack[top]
            if node in sources:
                yield [p for p, n in reversed(stack[:top + 1])]
            if len(pred[node]) > i:
                stack[top][1] = i + 1
                next_node = pred[node][i]
                if next_node in seen:
                    continue
                seen.add(next_node)
                top += 1
                if top == len(stack):
                    stack.append([next_node, 0])
                else:
                    stack[top][:] = [next_node, 0]
            else:
                seen.discard(node)
                top -= 1
    
    # ---------- 3. 核心算法：获取最小环 ----------
    Coreness = nx.core_number(Mygraph)
    removeNodes = set()
    
    for i in Mygraph.nodes():
        SmallestCyclesOfNodes[i] = set()
        CycleRatio[i] = 0
        if Mygraph.degree(i) <= 1 or Coreness[i] <= 1:
            NodeGirth[i] = 0
            removeNodes.add(i)
        else:
            NodeGirth[i] = DEF_IMPOSSLEN
    
    # 移除度≤1或核数≤1的节点
    Mygraph.remove_nodes_from(removeNodes)
    
    # 初始化环长度字典
    for i in range(3, Mygraph.number_of_nodes() + 2):
        CycLenDict[i] = 0
    
    # 第一步：查找3环（三角形）
    NodeList = list(Mygraph.nodes())
    NodeList.sort()
    
    curCyc = []
    for ix in NodeList[:-2]:  # v1
        if NodeGirth[ix] == 0:
            continue
        curCyc.append(ix)
        for jx in NodeList[NodeList.index(ix) + 1: -1]:  # v2
            if NodeGirth[jx] == 0:
                continue
            curCyc.append(jx)
            if Mygraph.has_edge(ix, jx):
                for kx in NodeList[NodeList.index(jx) + 1:]:  # v3
                    if NodeGirth[kx] == 0:
                        continue
                    if Mygraph.has_edge(kx, ix):
                        curCyc.append(kx)
                        if Mygraph.has_edge(kx, jx):
                            SmallestCycles.add(tuple(curCyc))
                            for node in curCyc:
                                NodeGirth[node] = 3
                        curCyc.pop()
            curCyc.pop()
        curCyc.pop()
    
    # 第二步：查找更大环（≥4）
    ResiNodeList = [nod for nod in NodeList if NodeGirth[nod] == DEF_IMPOSSLEN]
    
    if ResiNodeList:
        visitedNodes = dict.fromkeys(ResiNodeList, set())
        for nod in ResiNodeList:
            if Coreness[nod] == 2 and NodeGirth[nod] < DEF_IMPOSSLEN:
                continue
            for nei in list(Mygraph.neighbors(nod)):
                if Coreness[nei] == 2 and NodeGirth[nei] < DEF_IMPOSSLEN:
                    continue
                if nei not in visitedNodes or nod not in visitedNodes[nei]:
                    visitedNodes[nod].add(nei)
                    if nei not in visitedNodes:
                        visitedNodes[nei] = {nod}
                    else:
                        visitedNodes[nei].add(nod)
                    
                    if Coreness[nei] == 2 and NodeGirth[nei] < DEF_IMPOSSLEN:
                        continue
                    
                    # 临时移除边以查找环
                    Mygraph.remove_edge(nod, nei)
                    if nx.has_path(Mygraph, nod, nei):
                        for path in my_all_shortest_paths(Mygraph, nod, nei):
                            lenPath = len(path)
                            path.sort()
                            SmallestCycles.add(tuple(path))
                            for node in path:
                                if NodeGirth[node] > lenPath:
                                    NodeGirth[node] = lenPath
                    Mygraph.add_edge(nod, nei)
    
    # ---------- 4. 计算CycleRatio ----------
    NumSmallCycles = len(SmallestCycles)
    
    # 记录每个节点参与的最小环
    for cyc in SmallestCycles:
        lenCyc = len(cyc)
        CycLenDict[lenCyc] = CycLenDict.get(lenCyc, 0) + 1
        for nod in cyc:
            SmallestCyclesOfNodes[nod].add(cyc)
    
    # 计算每个节点的CycleRatio
    for objNode, SmaCycs in SmallestCyclesOfNodes.items():
        if not SmaCycs:
            continue
        
        cycleNeighbors = set()
        NeiOccurTimes = {}
        
        for cyc in SmaCycs:
            for n in cyc:
                NeiOccurTimes[n] = NeiOccurTimes.get(n, 0) + 1
            cycleNeighbors.update(cyc)
        
        cycleNeighbors.discard(objNode)
        if objNode in NeiOccurTimes:
            del NeiOccurTimes[objNode]
        
        sum_ratio = 0
        for nei in cycleNeighbors:
            if nei in SmallestCyclesOfNodes and SmallestCyclesOfNodes[nei]:
                sum_ratio += float(NeiOccurTimes.get(nei, 0)) / len(SmallestCyclesOfNodes[nei])
        
        CycleRatio[objNode] = sum_ratio 
    
    result = CycleRatio
    sorted_result = dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
    return sorted_result

