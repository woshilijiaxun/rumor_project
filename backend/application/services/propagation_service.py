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

