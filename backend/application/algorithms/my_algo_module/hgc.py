# -*-coding:GBK-*-
__author__ = 'jiaxun Li'
import numpy as np
import time
import networkx as nx
import itertools
import random
import math
import statistics
import pandas as pd
networkName = 'Email'


Mygraph = nx.Graph()

rawC = 0
def load_graph(path):
    G = nx.Graph()
    with open(path, 'r') as text:
        for line in text:
            vertices = line.strip().split(' ')
            source = int(vertices[0])
            target = int(vertices[-1])
            G.add_edge(source, target)
    return G
# file = open(NetworkAddress)
# while 1:
#     lines = file.readlines(10000)
#     if not lines:
#         break
#     for line in lines:
#         #input format of the network
#         line = line[:-1]
#         Mygraph.add_edge(int(line[:6]), int(line[7:]))
# file.close()
# data = loadmat(r'C:\Users\ADM\Desktop\Network-Data-master\13_Power.mat')
# am = data[list(data.keys())[-1]]  






#Mygraph = load_graph(r'C:\Users\ADM\Desktop\CycleRatio-main\Dataset\Yeast.txt')
#Mygraph = load_graph(r'C:\Users\ADM\Desktop\dolphin.txt')
# Mygraph.remove_edges_from(nx.selfloop_edges(Mygraph))
G = Mygraph.copy()




NodeNum = Mygraph.number_of_nodes()  #
print(networkName)
print('Number of nodes = ', NodeNum)
print("Number of deges:", Mygraph.number_of_edges())



DEF_IMPOSSLEN = NodeNum + 1 #Impossible simple cycle length

SmallestCycles = set()
NodeGirth = dict()
NumSmallCycles = 0
CycLenDict = dict()
CycleRatio = {}

SmallestCyclesOfNodes = {} #




Coreness = nx.core_number(Mygraph)

removeNodes =set()
for i in Mygraph.nodes():  #
    SmallestCyclesOfNodes[i] = set()
    CycleRatio[i] = 0
    if Mygraph.degree(i) <= 1 or Coreness[i] <= 1:
        NodeGirth[i] = 0
        removeNodes.add(i)
    else:
        NodeGirth[i] = DEF_IMPOSSLEN



Mygraph.remove_nodes_from(removeNodes)  #
NumNode = Mygraph.number_of_nodes()  #update

for i in range(3,Mygraph.number_of_nodes()+2):
    CycLenDict[i] = 0



def my_all_shortest_paths(G, source, target):
    pred = nx.predecessor(G, source)
    if target not in pred:
        raise nx.NetworkXNoPath(
            f"Target {target} cannot be reached" f"from given sources"
        )
    sources = {source}
    seen = {target}
    stack = [[target, 0]]
    top = 0
    while top >= 0:
        node, i = stack[top]
        if node in sources:
            yield [p for p, n in reversed(stack[: top + 1])]
        if len(pred[node]) > i:
            stack[top][1] = i + 1
            next = pred[node][i]
            if next in seen:
                continue
            else:
                seen.add(next)
            top += 1
            if top == len(stack):
                stack.append([next, 0])
            else:
                stack[top][:] = [next, 0]
        else:
            seen.discard(node)
            top -= 1


def getandJudgeSimpleCircle(objectList):#
    numEdge = 0
    for eleArr in list(itertools.combinations(objectList, 2)):
        if Mygraph.has_edge(eleArr[0], eleArr[1]):
            numEdge += 1
    if numEdge != len(objectList):
        return False
    else:
        return True


def getSmallestCycles():
    NodeList = list(Mygraph.nodes())
    NodeList.sort()
    #setp 1
    curCyc = list()
    for ix in NodeList[:-2]:  #v1
        if NodeGirth[ix] == 0:
            continue
        curCyc.append(ix)
        for jx in NodeList[NodeList.index(ix) + 1 : -1]:  #v2
            if NodeGirth[jx] == 0:
                continue
            curCyc.append(jx)
            if Mygraph.has_edge(ix,jx):
                for kx in NodeList[NodeList.index(jx) + 1:]:      #v3
                    if NodeGirth[kx] == 0:
                        continue
                    if Mygraph.has_edge(kx,ix):
                        curCyc.append(kx)
                        if Mygraph.has_edge(kx,jx):
                            SmallestCycles.add(tuple(curCyc))
                            for i in curCyc:
                                NodeGirth[i] = 3
                        curCyc.pop()
            curCyc.pop()
        curCyc.pop()
    # setp 2
    ResiNodeList = []  # Residual Node List
    for nod in NodeList:
        if NodeGirth[nod] == DEF_IMPOSSLEN:
            ResiNodeList.append(nod)
    if len(ResiNodeList) == 0:
        return
    else:
        visitedNodes = dict.fromkeys(ResiNodeList,set())
        for nod in ResiNodeList:
            if Coreness[nod] == 2 and NodeGirth[nod] < DEF_IMPOSSLEN:
                continue
            for nei in list(Mygraph.neighbors(nod)):
                if Coreness[nei] == 2 and NodeGirth[nei] < DEF_IMPOSSLEN:
                    continue
                if not nei in visitedNodes.keys() or not nod in visitedNodes[nei]:
                    visitedNodes[nod].add(nei)
                    if nei not in visitedNodes.keys():
                        visitedNodes[nei] = set([nod])
                    else:
                        visitedNodes[nei].add(nod)
                    if Coreness[nei] == 2 and NodeGirth[nei] < DEF_IMPOSSLEN:
                        continue
                    Mygraph.remove_edge(nod, nei)
                    if nx.has_path(Mygraph, nod, nei):
                        for path in my_all_shortest_paths(Mygraph, nod, nei):
                            lenPath = len(path)
                            path.sort()
                            SmallestCycles.add(tuple(path))
                            for i in path:
                                if NodeGirth[i] > lenPath:
                                    NodeGirth[i] = lenPath
                    Mygraph.add_edge(nod, nei)





def StatisticsAndCalculateIndicators(): #
    global NumSmallCycles
    NumSmallCycles = len(SmallestCycles)
    for cyc in SmallestCycles:
        lenCyc = len(cyc)
        CycLenDict[lenCyc] += 1
        for nod in cyc:
            SmallestCyclesOfNodes[nod].add(cyc)
    for objNode,SmaCycs in SmallestCyclesOfNodes.items():
        if len(SmaCycs) == 0:
            continue
        cycleNeighbors = set()
        NeiOccurTimes = {}
        for cyc in SmaCycs:
            for n in cyc:
                if n in NeiOccurTimes.keys():
                    NeiOccurTimes[n] += 1
                else:
                    NeiOccurTimes[n] = 1
            cycleNeighbors = cycleNeighbors.union(cyc)
        cycleNeighbors.remove(objNode)
        del NeiOccurTimes[objNode]
        sum = 0
        for nei in cycleNeighbors:
            sum += float(NeiOccurTimes[nei]) / len(SmallestCyclesOfNodes[nei])
        CycleRatio[objNode] = sum + 1
    return CycleRatio




def printAndOutput_ResultAndDistribution(objectList,nameString,Outpath):
    addrespath = Outpath + nameString + '.txt'
    Distribution = {}#

    for value in objectList.values():
        if value in Distribution.keys():
            Distribution[value] += 1
        else:
            Distribution[value] = 1

    for (myk, myv) in Distribution.items():
        Distribution[myk] = myv / float(NodeNum)

    rankedDict_ObjectList = sorted(objectList.items(), key=lambda d: d[1], reverse=True)
    fileout3 = open(addrespath, 'w')
    for d in range(len(rankedDict_ObjectList)):
        fileout3.writelines("%6d %12.6f  \n" % (rankedDict_ObjectList[d][0],rankedDict_ObjectList[d][1]))
    fileout3.close()
    addrespath2 = Outpath + 'Distribution_' + nameString + '.txt'
    fileout2 = open(addrespath2, 'w')
    for (myk, myv) in Distribution.items():
        fileout2.writelines("%12.6f %12.6f  \n" % (myk, myv))
    fileout2.close()


def printAndOutput_BasicCirclesDistribution(myCycLenDict,nameString,Outpath): #Copy_AllSimpleCircle
    Distribution = myCycLenDict
    global NumSmallCycles
    print('\nDistribution of SmallestBasicCycles:')
    float_allBasicCircles = float(NumSmallCycles)
    addrespath2 = Outpath + 'Distribution_' + nameString + '.txt'
    fileout2 = open(addrespath2, 'w')
    for (myk, myv) in Distribution.items():
        if myv > 0:
            fileout2.writelines("%10d %15d  %12.6f  \n" % (myk, myv,myv/float_allBasicCircles))
            print('len:%10d,count:%10d,ratio:%12.6f' % (myk, myv,myv/float_allBasicCircles))
    fileout2.close()

    List= list(SmallestCycles)
    rankedSBC_Set = sorted(List, key=lambda d: len(d), reverse=True)
    addrespath3 = Outpath + 'allSmallestBasicCycles.txt'
    fileout3 = open(addrespath3, 'w')
    for cy in rankedSBC_Set:
        fileout3.writelines("%s\n" %list(cy))
    fileout3.close()



class InfluenceCalculator:
    def __init__(self, graph):
        self.G = graph

    def sir_model(self, beta, source_node):
        """
        SIR模型的简化实现，恢复概率为1
        """
        nodes = self.G.nodes()
        state = {node: 'S' for node in nodes}
        state[source_node] = 'I'

        while 'I' in state.values():
            susceptible_nodes = [node for node in nodes if state[node] == 'S']
            for susceptible_node in susceptible_nodes:
                neighbors = list(self.G.neighbors(susceptible_node))
                for neighbor in neighbors:
                    if state[neighbor] == 'I' and random.random() < beta:
                        state[susceptible_node] = 'I'
                        break  # 一旦感染，中断内循环
            for node in nodes:
                if state[node] == 'I':
                    state[node] = 'R'

        recovered_nodes = [node for node in nodes if state[node] == 'R']
        return len(recovered_nodes)

    def calculate_average_influence(self, beta, source_node, experiments=100, iterations_per_experiment=100):
        """
        计算节点的平均影响度量
        """
        total_influence = 0
        for _ in range(experiments):
            total_influence += self.sir_model(beta, source_node)

        average_influence = total_influence / experiments
        return average_influence

    def calculate_sorted_nodes(self, beta):
        """
        计算并返回按平均影响度量降序排序的节点列表
        """
        average_influence_measures = [(node, self.calculate_average_influence(beta, node)) for node in self.G.nodes()]
        sorted_nodes = sorted(average_influence_measures, key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_nodes],[item[1] for item in sorted_nodes],dict(sorted_nodes)

    def calculate_transmission_capacity(self, beta, initial_infected_nodes, experiments=100, iterations_per_experiment=30):
        """
        计算节点在30个不同时间步中的传染能力
        """
        transmission_capacity = []
        for _ in range(experiments):
            infected_nodes = initial_infected_nodes.copy()  # 复制初始感染节点列表
            recovered_nodes = []
            for _ in range(iterations_per_experiment):
                for node in infected_nodes[:]:  # 使用切片来复制列表，避免在循环中修改列表长度
                    neighbors = list(self.G.neighbors(node))
                    for neighbor in neighbors:
                        if random.random() < beta and neighbor not in infected_nodes and neighbor not in recovered_nodes:
                            infected_nodes.append(neighbor)
                    infected_nodes.remove(node)
                    recovered_nodes.append(node)
                transmission_capacity.append(len(infected_nodes) + len(recovered_nodes))
        return transmission_capacity[:30]  # 返回传染能力列表的前30个元素

def  kendall(list1,list2):
    consist = 0
    inconsist = 0
    for i in range(len(list1)):
        for j in range(i+1,len(list1)):
            a = i
            b = j
            a1 = list2.index(list1[i])
            b1 = list2.index(list1[j])
            if (a>b and a1>b1) or (a<b and a1<b1):
                consist += 1
            elif (a<b and a1>b1) or (a>b and a1<b1):
                inconsist += 1
    #print(consist,inconsist)
    return (consist - inconsist)/(0.5*len(list1)*(len(list1)-1))

def each_order_neighbor(G,node,n):
    neighbors = []
    for i in range(1,n+1):
        neighbors.append(find_n_order_neighbor(G,node,i))
        if i != 1:
            neighbors[i-1] -= neighbors[i-2]
    return neighbors

def find_n_order_neighbor(G,node,n):
    source_node = node
    # 执行广度优先搜索，获取1-3阶邻居的边
    all_order_edges = nx.bfs_edges(G,source_node,depth_limit=n)
    # 获取1-3阶邻居的节点集合

    all_order_neighbors = {source_node} | set(v for u,v in all_order_edges)
    all_order_neighbors.discard(node)
    return all_order_neighbors


def jaccard_similarity(list1, list2,p):
    list3 = list1[:p]
    list4 = list2[:p]
    set1 = set(list3)
    set2 = set(list4)

    intersection = len(set1.intersection(set2))
    #print("int",intersection)
    union = len(set1.union(set2))
    #print("union",union)
    jaccard_coefficient = intersection / union if union > 0 else 0
    return jaccard_coefficient

def middle_node(G,node1,node2):
    # 查找开始节点的邻居节点
    start_neighbors = list(G.neighbors(node1))
    # 查找结束节点的邻居节点
    end_neighbors = list(G.neighbors(node2))
    # 查找路径长度为2的中间节点
    middle_nodes = list(set(start_neighbors) & set(end_neighbors))
    if len(middle_nodes) == 1:
        return middle_nodes[0]
    else:
        # 计算每个节点的度
        degrees = {node: G.degree(node) for node in middle_nodes}

        # 找到度最大的节点
        min_degree_node = min(degrees, key=degrees.get)
        return min_degree_node
def ED(G):
    ED = {}
    for node in G.nodes():
        all_neighbors = each_order_neighbor(G,node,2)    #所有二阶邻居    [{一阶},{二阶}]
        ed1 = {}
        for nei1 in all_neighbors[0]:
            D = 1 - math.log(1/G.degree(node),10)
            ed1[nei1] = round(D,4)
        ED[node] = ed1


    for node in G.nodes():
        all_neighbors = each_order_neighbor(G,node,2)    #所有二阶邻居    [{一阶},{二阶}]
        ed2 = {}
        for nei2 in all_neighbors[1]:
            middle_nodes = middle_node(G,node,nei2)
            D = ED[node][middle_nodes]  + 1 - math.log(1/G.degree(middle_nodes),10)
            ed2[nei2] = round(D,4)
        ED[node].update(ed2)
    return ED

def threshhold(G):
    # 计算网络的平均度
    avg_degree = sum(dict(G.degree()).values()) / len(G)
    # 计算网络中每个节点的度数，求平方并相加
    squared_degree_sum = sum(deg ** 2 for node, deg in G.degree())
    # 计算度的平方的平均值
    average_squared_degree = squared_degree_sum / len(G)
    beita = avg_degree / (average_squared_degree - avg_degree)
    return round(beita, 4)

def SH(G):
    num = nx.number_of_nodes(G)
    #print(num)
    #得到邻接矩阵
    A=np.array(nx.adjacency_matrix(G,nodelist=range(0,num)).todense())
    #print(A)
    #转化为p_ij矩阵。p_ij代表节点i花费在节点j上的精力。
    A=A/A.sum(axis=0).reshape(-1,1)
    C=[]#保存各个节点的约束系数
    count = 0
    for i in range(A.shape[0]):
        #知道当前节点的邻居节点
        n_idx=np.where(A[i]>0)[0]
        c_i=0
        for j in n_idx:
            #节点i和节点j的共同邻居
            com_n_idx=np.where(np.logical_and(A[i]>0,A[j]>0))[0]
            tmp=sum([A[i][k]*A[k][j] for k in com_n_idx])+A[i][j]
            c_i+=tmp*tmp
        C.append((count,round(c_i,4)))              #结果是列表 [(节点序号,SH值)] SH值越小说明节点作用越大
        count += 1
    sh = {key:value for key,value in C}             #转换为字典{节点，值}
    return sh

def LC(G):
    LC = {}
    for node in G.nodes():
        nei = nx.neighbors(G,node)
        nei_degrees = 0
        for n in nei:
            nei_degrees += nx.degree(G,n)
        LC[node] = (nx.degree(G,node))**2 + nx.degree(G,node) + 2 * nei_degrees
    return LC

def LGM(G,R):
    LGM = {}
    for node in G.nodes():
        neighbors = each_order_neighbor(G,node,R)
        s = 0
        d = 1
        for nei in neighbors:
            for n in nei:
                s += (G.degree(node)*G.degree(n)) / d ** 2
            d += 1
        s = round(s,4)
        LGM[node] = s
    LGM = dict(sorted(LGM.items(),key=lambda x:x[1],reverse=True))
    lgm_list = [key for key in LGM.keys()]
    lgm_value = [key for key in LGM.values()]
    return lgm_list,lgm_value,LGM


def normalized(data):
    max_value = max(data.values())
    min_value = min(data.values())

    for key, value in data.items():
        normalized_value = (value - min_value) / (max_value - min_value)
        mapped_value = normalized_value * 999 + 1
        data[key] = mapped_value

    return data



def propagation_influence(b,initial_infected_nodes,r ):
    initial_infected_nodes = initial_infected_nodes
    b=b
    recovery_rate = r  # 康复率

    num_simulations = 100  # 设置模拟次数
    recovered_totals = []  # 存储每次模拟的恢复节点总数

    # 存储每个时间步的统计数据
    susceptible_count = [0] * 30
    infected_count = [0] * 30
    recovered_count = [0] * 30

    for _ in range(num_simulations):
        # 初始化节点状态
        node_status = {}
        for node in G.nodes():
            if node in initial_infected_nodes:
                node_status[node] = 'I'
            else:
                node_status[node] = 'S'

        # 模拟传播过程并记录每个时间步的易感者、感染者和康复者数量
        for t in range(30):
            # 记录当前易感者、感染者和康复者数量
            num_susceptible = sum(1 for status in node_status.values() if status == 'S')
            num_infected = sum(1 for status in node_status.values() if status == 'I')
            num_recovered = sum(1 for status in node_status.values() if status == 'R')
            susceptible_count[t] += num_susceptible
            infected_count[t] += num_infected
            recovered_count[t] += num_recovered

            # 传播过程模拟
            for node in G.nodes():
                if node_status[node] == 'I':
                    neighbors = list(G.neighbors(node))
                    for neighbor in neighbors:
                        if node_status[neighbor] == 'S' and random.random() < b:
                            node_status[neighbor] = 'I'
                    if random.random() < recovery_rate:
                        node_status[node] = 'R'

        # 更新恢复的节点总数并存储
        recovered_total = sum(1 for status in node_status.values() if status == 'R')
        recovered_totals.append(recovered_total)

    # 计算每个时间步的平均值
    avg_susceptible = [count / num_simulations for count in susceptible_count]
    avg_infected = [count / num_simulations for count in infected_count]
    avg_recovered = [count / num_simulations for count in recovered_count]

    # 输出每次模拟的恢复节点总数
    #print("每次模拟的恢复节点总数:", recovered_totals)
    avg_recovered_total = sum(recovered_totals) / num_simulations
    # print("恢复节点总数的平均值:", avg_recovered_total)
    # print("感染率:", avg_recovered_total / NodeNum)

    ic = [score/num_simulations for score in infected_count]
    rc = [score/num_simulations for score in recovered_count]
    result = [(x+y)/len(G.nodes()) for x,y in zip(ic,rc)]
    # print("infected",ic)
    # print("recovered",rc)
    # print("tptal",result)
    return result


def bigger_ks_nodes(node,neighbors):
    new_neighbors = []
    for nei in neighbors:
        if s_ks[nei] > s_ks[node]:
            new_neighbors.append(nei)
    return new_neighbors


def Mr(dic):
    '''
    两种dic
    1.[{},{}],有些算法是一块块拼接的，用上边算
    2.{}，普通的用这样算
    '''
    N = 0
    m = 0

    summary = {}
    for i in dic:
        N += 1
        summary.setdefault(dic[i],list()).append(i)
    for i in summary:
            Nr = len(summary[i])
            m += Nr*(Nr-1)
    m = (1 - m/(N*(N-1))) ** 2
    return m




# main fun
StartTime = time.time()
getSmallestCycles()
EndTime1 = time.time()

#StatisticsAndCalculateIndicators()

ks = nx.core_number(G)
s_ks = dict(sorted(ks.items(),key=lambda x:x[1],reverse=True))


CR = StatisticsAndCalculateIndicators()
cr_list = dict(sorted(CR.items(),key=lambda x:x[1],reverse=True))
print("CR",cr_list)

#average_cr = sum(cr_list.values())/len(cr_list)
#cr_list = normalized(cr_list)
#print("cr_list",cr_list)
crl = [key for key in cr_list.keys()]
cr_value = [key for key in cr_list.values()]

average_cr = sum(cr_list.values())/len(cr_list)







lgm_list,lgm_value,lgm = LGM(G,2)
#print("lgm:",lgm_list)


#cr_list = [key for key in cr_list.keys()]
dc_list = nx.degree_centrality(G)
dc_list = dict(sorted(dc_list.items(),key=lambda x:x[1],reverse=True))

dl = [key for key in dc_list.keys()]
dc_value = [value for value in dc_list.values()]
print("dc_value",dc_value)

#--------------------------------------------------------------------------------------------------------
ED = ED(G)
#--------------------------------------------------------------------------------------------------------
sh = SH(G)


degrees = dict(G.degree())
DK = {}
for node in G.nodes():
    neighbors = find_n_order_neighbor(G,node,2)
    length1 = len(neighbors)
    new_neighbors = bigger_ks_nodes(node,neighbors)
    length2 = len(new_neighbors)

    if length2 == 0:
        length2 = 1
    Y = length2 / length1
    s = 0
    for nei in neighbors:
        s += degrees[nei]
    DK[node] = degrees[node]
DK = dict(sorted(DK.items(),key= lambda x:x[1],reverse=True))
print("dk",DK)


LCGM = {}
for node in G.nodes():

    neighbors = each_order_neighbor(G, node, 2)

    s = 0
    d = 1
    for nei in neighbors:
        for n in nei:
            #s += LC[node]*LC[n] / ED[node][n]**2    #d**2
            #s += nx.degree(G,node)*s_ks[node]*nx.degree(G,n)*s_ks[n] / ED[node][n]**2   #d**2
            s += DK[node]*DK[n] / ED[node][n]**2   #d**2
            #s += cr_list[node]*cr_list[n] / d**2
        d += 1
        s *= math.exp(-sh[node])
    s = round(s, 4)
    LCGM[node] = s

LCGM = dict(sorted(LCGM.items(),key=lambda x:x[1],reverse=True))
average_lcgm = sum(LCGM.values())/len(LCGM)
print('average_lcgm',average_lcgm)
print("lcgm_list",LCGM)
#LCGM = normalized(LCGM)

LCGM_list = [key for key in LCGM.keys()]




def RDP(G):
    I0 = {}
    for node in G.nodes():
        I0[node] = G.degree(node)

    #print("I0", I0)
    I1 = {}
    for node in G.nodes():
        nei = G.neighbors(node)
        score = 0
        for n in nei:
            score += I0[n]
        I1[node] = score / 1 ** 2
    #print("I1", I1)
    I2 = {}
    for node in G.nodes():
        nei = G.neighbors(node)
        score = 0
        for n in nei:
            score += I1[n]
        I2[node] = score / 2 ** 2
    #print("I2", I2)
    I3 = {}
    for node in G.nodes():
        nei = G.neighbors(node)
        score = 0
        for n in nei:
            score += I2[n]
        I3[node] = score / 3 ** 2
    #print("I3", I3)

    RDP = {}
    for node in G.nodes():
        RDP[node] = I1[node] + I2[node] + I3[node]
    return RDP

RDP = RDP(G)
RDP = dict(sorted(RDP.items(),key=lambda x:x[1],reverse=True))
RDP_list = [key for key in RDP.keys()]
RDP_value = [key for key in RDP.values()]
#print(RDP)


def RCP(G):
    I0 = {}
    for node in G.nodes():
        I0[node] = cr_list[node]

    #print("I0", I0)
    I1 = {}
    for node in G.nodes():
        nei = G.neighbors(node)
        score = 0
        for n in nei:
            score += I0[n]
        I1[node] = score / 1 ** 2
    #print("I1", I1)
    I2 = {}
    for node in G.nodes():
        nei = G.neighbors(node)
        score = 0
        for n in nei:
            score += I1[n]
        I2[node] = score / 2 ** 2
    #print("I2", I2)
    I3 = {}
    for node in G.nodes():
        nei = G.neighbors(node)
        score = 0
        for n in nei:
            score += I2[n]
        I3[node] = score / 3 ** 2
    #print("I3", I3)

    RCP = {}
    for node in G.nodes():
        RCP[node] = I1[node] + I2[node] + I3[node]
        RCP[node] *= math.exp(-sh[node])
    return RCP
RCP = RCP(G)
RCP = dict(sorted(RCP.items(),key=lambda x:x[1],reverse=True))
average_rcp = sum(RCP.values())/len(RCP)
print('average_rcp',average_rcp)
print("RCP",RCP)
#RCP = normalized(RCP)
RCP_list = [key for key in RCP.keys()]
#print("RCP",RCP)

# RCPGM = {}
# for node in G.nodes():
#
#     neighbors = each_order_neighbor(G, node, 2)
#     s = 0
#     d = 1
#     for nei in neighbors:
#         for n in nei:
#             s += G.degree(node)*G.degree(n) /  d**2 #ED[node][n]**2  #d**2
#             #s += dc_list[node]*dc_list[n] /  d**2
#             #s += nx.degree(G,node)*nx.degree(G,n) / d**2   #d**2
#             #s += cr_list[node]*cr_list[n] / d**2
#         d += 1
#     s = round(s, 4)
#     RCPGM[node] = s
# RCPGM = dict(sorted(RCPGM.items(),key=lambda x:x[1],reverse=True))
# print("RCPGM",RCPGM)
# RCPGM_list = [key for key in RCPGM.keys()]


LC_RCP = {}
gama = average_lcgm / average_rcp
print("gama",gama)
for node in G.nodes():
    LC_RCP[node] = LCGM[node] + gama*RCP[node]
LC_RCP = dict(sorted(LC_RCP.items(),key=lambda x:x[1],reverse=True))
LC_RCP_list = [key for key in LC_RCP.keys()]
LC_RCP_value = [key for key in LC_RCP.values()]
print("LC_RCP",LC_RCP_list)

hgc = LC_RCP
#return hgc

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
        num = nx.number_of_nodes(G)
        A = np.array(nx.adjacency_matrix(G, nodelist=range(0, num)).todense())
        A = A / A.sum(axis=0).reshape(-1, 1)
        C = []
        count = 0
        for i in range(A.shape[0]):
            n_idx = np.where(A[i] > 0)[0]
            c_i = 0
            for j in n_idx:
                com_n_idx = np.where(np.logical_and(A[i] > 0, A[j] > 0))[0]
                tmp = sum([A[i][k] * A[k][j] for k in com_n_idx]) + A[i][j]
                c_i += tmp * tmp
            C.append((count, round(c_i, 4)))
            count += 1
        return {key: value for key, value in C}

    # ============ 计算流程（复制原代码逻辑，但移除所有print）============
    
    # 1. 计算必要的中间指标
    degrees = dict(G.degree())
    ks = nx.core_number(G)
    s_ks = dict(sorted(ks.items(), key=lambda x: x[1], reverse=True))
    ED_dict = ED(G)
    sh = SH(G)
    
    # 2. 计算CR
    CR = StatisticsAndCalculateIndicators()
    cr_list = dict(sorted(CR.items(),key=lambda x:x[1],reverse=True))
    
    
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
