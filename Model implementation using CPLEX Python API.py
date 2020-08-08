from docplex.mp.model import Model 
import itertools
from itertools import islice
import random, copy
import networkx as nx
from collections import defaultdict

## for B4
n = 12
## for ATT
# n = 25
nodes = [i for i in range(1, n + 1)]
Tc = {i:200 for i in nodes}
## for B4
edges_list = [(1,2),(1,4),(1,6),(2,3),(3,5),(4,5),(4,7),(4,8),(5,6),(6,7),(6,8),(7,8),(7,9),(8,10),(9,10),(9,11),(9,12),(10,11),(10,12)]

## for ATT
# edges_list = [(1,2),(1,3),(1,7),(1,8),(2,7),(3,4),(3,7),(3,10),(3,16),(3,17),(3,18),(3,21),(3,22),(4,9),(4,10),(4,7),(5,6),(5,8),(6,8),(6,9),(6,10),(6,14),
#           (6,15),(7,8),(9,10),(9,14),(10,14),(10,17),(10,23),(11,12),(11,14),(11,15),(12,13),(12,14),(12,15),(13,25),(13,14),(14,16),(14,17),
#           (14,18),(14,23),(16,17),(16,18),(16,22),(17,18),(18,19),(18,20),(18,21),(18,22),(18,23),(19,22),(20,21),(22,23),(23,24),(23,25),(24,25)]

## add the link with reverted direction to the edges_list 
aux = []
for (i,j) in edges_list:
  aux.append((j,i))
for (i,j) in aux:
  edges_list.append((i,j))  
## link capacities  
c = {(i,j):1000 for (i,j) in edges_list}
net = nx.DiGraph()
net.add_edges_from(edges_list)
## created random flows
pairs=list(itertools.product(net.nodes(), net.nodes()))
flows = random.sample(pairs, 70)
print(flows)
for (src,dst) in flows:
  if src == dst:
    flows.remove((src,dst)) 
while len(flows)>60:
  flows.pop()
## flow demands  
b = {(src,dst):50 for (src,dst) in flows}
## primary routes 
P = {}
for (src,dst) in flows:    
  P[src,dst] = list(islice(nx.shortest_simple_paths(net, src, dst), 2))   
## backup routes  
Q = defaultdict(dict)
aux = defaultdict(dict)
for (src,dst) in P:
    for r in P[src,dst]: 
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
            path1 = P[src,dst][0]
            path2 = P[src,dst][1]
            path_pairs1 = list(zip(path1, path1[1:]))
            path_pairs2 = list(zip(path2, path2[1:]))
            Q[src,dst][i+j] = []
            if (i,j) not in path_pairs1:
                Q[src,dst][i+j].append(path1)
            elif (i,j) not in path_pairs2:
                Q[src,dst][i+j].append(path2)                     
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
                    Q[src,dst][i+j].append(backup_path)
                    
## a random failed link                 
failed_link = random.sample(edges_list, 1)
(i,j) = failed_link[0]
## identify the set of affected and non-affected flow
affected_flows = []
nonaffected_flows = []
for (src,dst) in flows:
    for path in P[src,dst]:
        test = copy.copy(path)
        path_pairs = list(zip(test, test[1:]))
        path_pairs = path_pairs[1:]
        if (i,j) in path_pairs or (j,i) in path_pairs:
            affected_flows.append((src,dst))                   
            break
    if (src,dst) not in affected_flows:
        nonaffected_flows.append((src,dst))   
## trafic rate of the non-affected flow      
t = defaultdict(dict)        
for (src,dst) in nonaffected_flows:
    for p in P[src,dst]:
        t[src,dst][tuple(p)] = 0.5*b[src,dst] 
e = i+j


index = [(src,dst,tuple(p)) for (src,dst) in affected_flows for p in Q[src,dst][e]]
mdl = Model('CVRP')
## decision variable x
x = mdl.binary_var_dict(index,name = 'x')
## decision variable y
y = mdl.continuous_var_dict(index,name = 'y')
## objective function
mdl.minimize(mdl.sum(mdl.sum(x[src,dst,tuple(p)]*len(p) + mdl.sum(300*y[src,dst,tuple(p)]/c[i,j] for (i,j) in edges_list if (i,j) in list(zip(p, p[1:]))) for p in Q[src,dst][e]) for (src,dst) in affected_flows))
## link capacity constraints
mdl.add_constraints((mdl.sum(mdl.sum(y[src,dst,tuple(p)] for p in Q[src,dst][e] if (i,j) in list(zip(p, p[1:]))) for (src,dst) in affected_flows) + mdl.sum(mdl.sum(t[src,dst][tuple(p)] for p in P[src,dst] if (i,j) in list(zip(p, p[1:]))) for (src,dst) in nonaffected_flows))<= c[i,j] for (i,j) in edges_list)
## node capacity constraints
mdl.add_constraints((mdl.sum(mdl.sum(x[src,dst,tuple(p)] for p in Q[src,dst][e] if i in p) for (src,dst) in affected_flows) + mdl.sum(mdl.sum(1 for p in P[src,dst] if i in p) for (src,dst) in nonaffected_flows))<= Tc[i] for i in nodes)
## traffic rate constraints
mdl.add_constraints(x[src,dst,tuple(p)] <= y[src,dst,tuple(p)] for (src,dst) in affected_flows for p in Q[src,dst][e])
mdl.add_constraints(y[src,dst,tuple(p)] <= x[src,dst,tuple(p)]*b[src,dst] for (src,dst) in affected_flows for p in Q[src,dst][e])
## flow satisfaction constraints
mdl.add_constraints(mdl.sum(y[src,dst,tuple(p)] for p in Q[src,dst][e]) == b[src,dst] for (src,dst) in affected_flows)
solution = mdl.solve(log_output= True) 
print(solution)
print('='*50)
print('Failed link: ', (i,j))
print('Affected flows: ', affected_flows)
# print('Not affected flows: ', nonaffected_flows)
print('='*50)


