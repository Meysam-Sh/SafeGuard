from docplex.mp.model import Model 
import itertools
from itertools import islice
import random, copy
import time
import networkx as nx
import numpy as np
from collections import defaultdict
# from initilization import Get_edges
import initilization

topo = input("select a topology: B4 ATT Bestel Cgonet Dial_Telecom:")
edges_list,n = initilization.Get_edges(topo)
tm1 = initilization.TMGeneartion(n)
print(tm1)

nodes = [i for i in range(1, n + 1)]
TCAM = [750,1500,2+e2,16e+3]
Tc = {i:np.random.choice(TCAM) for i in nodes} 
print(len(edges_list))
aux = []
for (i,j) in edges_list:
  aux.append((j,i))
for (i,j) in aux:
  edges_list.append((i,j))  
c = {(i,j):50000 for (i,j) in edges_list}
net = nx.DiGraph()
net.add_edges_from(edges_list)
pairs=list(itertools.product(net.nodes(), net.nodes()))
flows = {}
Pri  = [30,20,10]
for h in Pri:
    flows[h] = random.sample(pairs, 400)
for h in flows:
    for (src,dst) in flows[h]:
      if src == dst:
        flows[h].remove((src,dst))  
while len(flows)>60:
  flows.pop()
  
  
  
  
b = {(src,dst,h):50 for h in flows for (src,dst) in flows[h]}
m = {(src,dst,h):15 for h in flows for (src,dst) in flows[h]}
P = {}
for h in flows:
    for (src,dst) in flows[h]:   
        P[src,dst,h] = list(islice(nx.shortest_simple_paths(net, src, dst), 2))  

length = []
for value in P.values():
    for p in value:
        length.append(len(p))
print(sum(length) / len(length))

Q = defaultdict(dict)
aux = defaultdict(dict)
for (src,dst,h) in P:
    for r in P[src,dst,h]: 
        path_pairs = list(zip(r, r[1:]))
        links = copy.copy(net.edges())
        links = list(links)
        from_source = []
        for (i,j) in links:
            if i == src:
                from_source.append((i,j))
        for (i,j) in from_source:
            links.remove((i,j))            
        for (i,j) in path_pairs[1:]:
            Q[src,dst,h][i+j] = []
            if len(P[src,dst,h]) > 1:
                path1 = P[src,dst,h][0]
                path2 = P[src,dst,h][1]
                path_pairs1 = list(zip(path1, path1[1:]))
                path_pairs2 = list(zip(path2, path2[1:]))
                if (i,j) not in path_pairs1:
                    Q[src,dst,h][i+j].append(path1)
                elif (i,j) not in path_pairs2:
                    Q[src,dst,h][i+j].append(path2)                     
            path = copy.copy(r)          
            portion = path[0:path.index(i)+1]
            remaining_edges = copy.copy(links)
            remaining_edges.remove((i,j))
            portion_pairs = list(zip(portion, portion[1:]))
            for (p,q) in portion_pairs:
                if (p,q) in remaining_edges:
                    remaining_edges.remove((p,q))
                    remaining_edges.remove((q,p))    
            newgraph = nx.DiGraph()
            newgraph.add_edges_from(remaining_edges)  
            has_path = False
            if i in newgraph.nodes():
                if nx.has_path(newgraph,i,dst):
                    has_path = True
                    try:
                        path1,path2 = list(islice(nx.shortest_simple_paths(newgraph, i, dst), 2))                  
                        aux[src,dst][i] = [path1,path2]
                    except: 
                        aux[src,dst][i] = [list(nx.shortest_path(newgraph,i,dst))]
            if len(portion) and has_path:   
                for backup in aux[src,dst][i]:
                    backup_path = portion[0:-1] + backup                       
                    Q[src,dst,h][i+j].append(backup_path)

start = time.time()
rr = [(12,61)]
for (i,j) in edges_list:                 
    failed_link = random.sample(edges_list, 1)
    (i,j) = failed_link[0]
    affected_flows = []
    nonaffected_flows = []
    for h in flows:
        for (src,dst) in flows[h]:
            for path in P[src,dst,h]:
                test = copy.copy(path)
                path_pairs = list(zip(test, test[1:]))
                path_pairs = path_pairs[1:]
                if (i,j) in path_pairs or (j,i) in path_pairs:
                    affected_flows.append((src,dst,h))                   
                    break
            if (src,dst,h) not in affected_flows:
                nonaffected_flows.append((src,dst,h))   
    t = defaultdict(dict)        
    for (src,dst,h) in nonaffected_flows:
        for p in P[src,dst,h]:
            t[src,dst,h][tuple(p)] = 0.5*b[src,dst,h] 
    e = i+j
    index = [(tuple([src,dst,h]),tuple(p)) for (src,dst,h) in affected_flows for p in Q[src,dst,h][e]]
    mdl = Model('CVRP')
    x = mdl.binary_var_dict(index,name = 'x')
    y = mdl.continuous_var_dict(index,name = 'y')
    mdl.minimize(mdl.sum(mdl.sum(x[tuple([src,dst,h]),tuple(p)]*len(p)/h + mdl.sum(y[tuple([src,dst,h]),tuple(p)]/c[i,j] for (i,j) in edges_list if (i,j) in list(zip(p, p[1:]))) for p in Q[src,dst,h][e]) for (src,dst,h) in affected_flows))
    mdl.add_constraints((mdl.sum(mdl.sum(y[tuple([src,dst,h]),tuple(p)] for p in Q[src,dst,h][e] if (i,j) in list(zip(p, p[1:]))) for (src,dst,h) in affected_flows) + mdl.sum(mdl.sum(t[src,dst,h][tuple(p)] for p in P[src,dst,h] if (i,j) in list(zip(p, p[1:]))) for (src,dst,h) in nonaffected_flows))<= c[i,j] for (i,j) in edges_list)
    mdl.add_constraints((mdl.sum(mdl.sum(x[tuple([src,dst,h]),tuple(p)]*m[src,dst,h] for p in Q[src,dst,h][e] if i in p) for (src,dst,h) in affected_flows) + mdl.sum(mdl.sum(m[src,dst,h] for p in P[src,dst,h] if i in p) for (src,dst,h) in nonaffected_flows))<= Tc[i] for i in nodes)
    mdl.add_constraints(x[tuple([src,dst,h]),tuple(p)] <= y[tuple([src,dst,h]),tuple(p)] for (src,dst,h) in affected_flows for p in Q[src,dst,h][e])
    mdl.add_constraints(y[tuple([src,dst,h]),tuple(p)] <= x[tuple([src,dst,h]),tuple(p)]*b[src,dst,h] for (src,dst,h) in affected_flows for p in Q[src,dst,h][e])
    mdl.add_constraints(mdl.sum(y[tuple([src,dst,h]),tuple(p)] for p in Q[src,dst,h][e]) == b[src,dst,h] for (src,dst,h) in affected_flows)
    solution = mdl.solve(log_output= True) 
    print(solution)
    print('='*50)
    print('Failed link: ', (i,j))
    print('Affected flows: ', affected_flows)
    print('Not affected flows: ', nonaffected_flows)
    print('='*50)
done = time.time()
elapsed = done - start
print('elapsed time:',elapsed)     


