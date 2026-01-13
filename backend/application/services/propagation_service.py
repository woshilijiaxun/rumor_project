import random
from collections import defaultdict
import networkx as nx
from typing import List, Dict, Any, Union, Set, Tuple

def threshhold(G: nx.Graph) -> float:
    """计算无向网络的传播阈值 beta。"""
    if not G or G.number_of_nodes() == 0:
        return 0.1

    degrees = [d for n, d in G.degree()]
    if not degrees:
        return 0.1
        
    avg_degree = sum(degrees) / len(degrees)
    
    squared_degree_sum = sum(d**2 for d in degrees)
    average_squared_degree = squared_degree_sum / len(degrees)
    
    denominator = average_squared_degree - avg_degree
    if denominator <= 0:
        # 避免除以零或负数，返回一个合理的默认值
        return 0.1
        
    beta = avg_degree / denominator
    return round(beta, 4)

class PropagationSimulator:
    def __init__(self, G: nx.Graph):
        if not isinstance(G, nx.Graph):
            raise TypeError("Input must be a networkx.Graph object.")
        self.G = G

    def _run_single_sir(self, beta: float, source_nodes: List[Any]) -> Set[Tuple[Any, Any]]:
        """执行单次 SIR 仿真，返回本次传播中的所有有向边。"""
        if not source_nodes:
            return set()

        infected = set(source_nodes)
        susceptible = set(self.G.nodes()) - infected
        recovered = set()

        newly_infected_edges = set()

        # 使用队列处理当前轮次的感染者
        q = list(source_nodes)

        while q:
            # 获取当前轮次需要处理的感染节点
            current_infected = q
            q = []

            for u in current_infected:
                # 遍历其所有易感的邻居
                for v in self.G.neighbors(u):
                    if v in susceptible:
                        if random.random() < beta:
                            susceptible.remove(v)
                            infected.add(v)
                            q.append(v)
                            newly_infected_edges.add((u, v))

            # 将处理完的节点移入恢复集合
            for u in current_infected:
                recovered.add(u)

        return newly_infected_edges

    def _run_single_sir_steps(self, beta: float, source_nodes: List[Any], max_steps: int) -> List[Set[Tuple[Any, Any]]]:
        """执行单次 SIR 仿真，并按时间步返回每一步新增感染的有向边集合。

        约定：
        - steps[0] 为 t=1 时刻由种子传播产生的新增感染边（因为 t=0 只有种子节点本身，没有“新增感染边”）
        - 最多返回 max_steps 步（max_steps<=0 时返回空）
        """
        if not source_nodes or max_steps <= 0:
            return []

        infected = set(source_nodes)
        susceptible = set(self.G.nodes()) - infected
        recovered = set()

        steps_edges: List[Set[Tuple[Any, Any]]] = []

        q = list(source_nodes)
        step = 0
        while q and step < max_steps:
            current_infected = q
            q = []

            newly_infected_edges: Set[Tuple[Any, Any]] = set()

            for u in current_infected:
                for v in self.G.neighbors(u):
                    if v in susceptible:
                        if random.random() < beta:
                            susceptible.remove(v)
                            infected.add(v)
                            q.append(v)
                            newly_infected_edges.add((u, v))

            steps_edges.append(newly_infected_edges)

            for u in current_infected:
                recovered.add(u)

            step += 1

        return steps_edges

    def calculate_propagation(self, beta: float, source_nodes: Union[Any, List[Any]], num_simulations: int) -> Dict[str, float]:
        """多次仿真计算概率传播图。"""
        if not isinstance(source_nodes, list):
            source_nodes = [source_nodes]

        # 过滤掉不存在于图中的源节点
        valid_source_nodes = [node for node in source_nodes if self.G.has_node(node)]
        if not valid_source_nodes:
            return {}

        edge_counts = defaultdict(int)
        for _ in range(num_simulations):
            transmission_edges = self._run_single_sir(beta, valid_source_nodes)
            for u, v in transmission_edges:
                edge_counts[(u, v)] += 1

        prob_graph = {f"{u}|{v}": count / num_simulations for (u, v), count in edge_counts.items()}
        return prob_graph

    def calculate_propagation_steps(self, beta: float, source_nodes: Union[Any, List[Any]], num_simulations: int, max_steps: int = 4) -> Dict[str, Any]:
        """多次仿真计算“按时间步”的传播结果。

        返回结构：
        {
          "steps": [
            {"t": 0, "nodes": [...], "edges": []},
            {"t": 1, "nodes": [...], "edges": [{"source":u,"target":v,"prob":p}, ...]},
            ...
          ],
          "edge_prob_by_step": [ {"u|v": p, ...}, ... ],
        }

        说明：
        - steps[0] 固定为种子集合（t=0）。
        - t>=1 的 edges 是“该步新增感染边”的概率（在 num_simulations 次仿真中出现的比例）。
        - nodes 是累积感染节点集合（方便前端做累积展示）。
        """
        if not isinstance(source_nodes, list):
            source_nodes = [source_nodes]

        valid_source_nodes = [node for node in source_nodes if self.G.has_node(node)]
        if not valid_source_nodes:
            return {"steps": [{"t": 0, "nodes": [], "edges": []}], "edge_prob_by_step": []}

        try:
            max_steps = int(max_steps)
        except Exception:
            max_steps = 4
        max_steps = max(1, min(max_steps, 20))

        edge_counts_by_step: List[defaultdict] = [defaultdict(int) for _ in range(max_steps)]
        node_counts_by_t: List[defaultdict] = [defaultdict(int) for _ in range(max_steps + 1)]

        for _ in range(num_simulations):
            steps_edges = self._run_single_sir_steps(beta, valid_source_nodes, max_steps=max_steps)

            infected_set = set(valid_source_nodes)
            node_counts_by_t[0]["__seed__"] += 1  # 占位，便于保持结构一致

            # 记录 t=0 的节点
            for n in infected_set:
                node_counts_by_t[0][str(n)] += 1

            # 逐步累积
            for i in range(max_steps):
                if i < len(steps_edges):
                    for u, v in steps_edges[i]:
                        edge_counts_by_step[i][(u, v)] += 1
                        infected_set.add(v)

                # t=i+1 的累积感染节点
                for n in infected_set:
                    node_counts_by_t[i + 1][str(n)] += 1

        steps = []
        steps.append({
            "t": 0,
            "nodes": [str(n) for n in valid_source_nodes],
            "edges": [],
        })

        edge_prob_by_step = []
        for i in range(max_steps):
            # 该步新增感染边概率
            m = {f"{u}|{v}": c / num_simulations for (u, v), c in edge_counts_by_step[i].items()}
            edge_prob_by_step.append(m)

            # 该时刻累积感染节点（概率>0 即出现过）
            nodes_t = [k for k, c in node_counts_by_t[i + 1].items() if k != "__seed__" and c > 0]
            steps.append({
                "t": i + 1,
                "nodes": sorted(nodes_t),
                "edges": [
                    {"source": kv.split("|")[0], "target": kv.split("|")[1], "prob": p}
                    for kv, p in sorted(m.items(), key=lambda x: x[1], reverse=True)
                ],
            })

        return {"steps": steps, "edge_prob_by_step": edge_prob_by_step}

