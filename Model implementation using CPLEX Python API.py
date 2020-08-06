from docplex.mp.model import Model 
import itertools
from itertools import islice
import random, copy
import networkx as nx
from collections import defaultdict

n = 12
nodes = [i for i in range(1, n + 1)]
Tc = {i:200 for i in nodes}
edges_list = [(1,2),(1,4),(1,6),(2,3),(3,5),(4,5),(4,7),(4,8),(5,6),(6,7),(6,8),(7,8),(7,9),(8,10),(9,10),(9,11),(9,12),(10,11),(10,12)]
aux = []
for (i,j) in edges_list:
  aux.append((j,i))
for (i,j) in aux:
  edges_list.append((i,j))  
c = {(i,j):1000 for (i,j) in edges_list}
net = nx.DiGraph()
net.add_edges_from(edges_list)
pairs=list(itertools.product(net.nodes(), net.nodes()))
flows = random.sample(pairs, 70)
for (src,dst) in flows:
  if src == dst:
    flows.remove((src,dst)) 
while len(flows)>60:
  flows.pop()
b = {(src,dst):50 for (src,dst) in flows}
P = {}
for (src,dst) in flows:    
  P[src,dst] = list(islice(nx.shortest_simple_paths(net, src, dst), 2))   
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
            Q[src,dst][i] = []
            if (i,j) not in path_pairs1:
                Q[src,dst][i].append(path1)
            elif (i,j) not in path_pairs2:
                Q[src,dst][i].append(path2)                     
            path = copy.copy(r)           
            # portion = path[0:path[path.index(i)-1]]
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
                    Q[src,dst][i].append(backup_path)

r = defaultdict(dict)
for (i,j) in edges_list:
    for (src,dst) in Q:
        paths = list(Q[src,dst].values())
        for p in paths[0]:
            path_pairs = list(zip(p, p[1:]))
            if (i,j) in path_pairs:
                r[i,j][tuple(p)] = 1
            else:
                r[i,j][tuple(p)] = 0
        for p in P[src,dst]:
            if p not in paths:
                path_pairs = list(zip(p, p[1:]))
                if (i,j) in path_pairs:
                    r[i,j][tuple(p)] = 1
                else:
                    r[i,j][tuple(p)] = 0
s = defaultdict(dict)
for i in nodes:
    for (src,dst) in Q:
        paths = list(Q[src,dst].values())
        for p in paths[0]:
            if i in p:
                s[i][tuple(p)] = 1
            else:
                s[i][tuple(p)] = 0
        for p in P[src,dst]:
            if p not in paths:
                if i in p:
                    s[i][tuple(p)] = 1
                else:
                    s[i][tuple(p)] = 0                  
failed_link = random.sample(edges_list, 1)
print(failed_link[0])
affected_flows = []
nonaffected_flows = []
for (src,dst) in P:
    for path in P[src,dst]:
        test = copy.copy(path)
        path_pairs = list(zip(path, path[1:]))
        path_pairs = path_pairs[1:]
        if failed_link[0] in path_pairs:
            affected_flows.append((src,dst))                   
            break
    if (src,dst) not in affected_flows:
        nonaffected_flows.append((src,dst))   
t = defaultdict(dict)        
for (src,dst) in nonaffected_flows:
    for p in P[src,dst]:
        t[src,dst][tuple(p)] = 0.5*b[src,dst]
        
f = failed_link[0][0]
index = [(src,dst,p) for (src,dst) in affected_flows for p in Q[src,dst][f]]

mdl = Model('CVRP')
x = mdl.binary_var_dict(index,name = 'x')
y = mdl.continuous_var_dict(index,name = 'y')
mdl.minimize(mdl.sum(mdl.sum(x[src,dst,p]*len(p)+ (mdl.sum(y[src,dst,p]*r[src,dst][tuple(p)]/c[i,j]) for (i,j) in edges_list)) for p in Q[src,dst][f]) for (src,dst) in affected_flows)
mdl.add_constraints((mdl.sum(mdl.sum(y[src,dst,p]*r[src,dst][tuple(p)] for p in Q[src,dst][f]) for (src,dst) in affected_flows) + mdl.sum(mdl.sum(t[src,dst,tuple(p)]*r[src,dst][tuple(p)] for p in P[src,dst]) for (src,dst) in nonaffected_flows))<= c[i,j] for (i,j) in edges_list)
mdl.add_constraints((mdl.sum(mdl.sum(x[src,dst,p]*s[i][tuple(p)] for p in Q[src,dst][f]) for (src,dst) in affected_flows) + mdl.sum(mdl.sum(s[i][tuple(p)] for p in P[src,dst]) for (src,dst) in nonaffected_flows))<= Tc[i] for i in nodes)
mdl.add_constraints(x[src,dst,p] <= y[src,dst,p] for (src,dst) in affected_flows for p in Q[src,dst][f])
mdl.add_constraints(y[src,dst,p] <= x[src,dst,p]*b[src,dst] for (src,dst) in affected_flows for p in Q[src,dst][f])
mdl.add_constraints(mdl.sum(y[src,dst,p] for p in Q[src,dst][f]) == b[src,dst] for (src,dst) in affected_flows)
solution = mdl.solve(log_output= True) 
print(solution)






