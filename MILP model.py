from docplex.mp.model import Model 
import itertools
from itertools import islice
import random, copy
import time
import networkx as nx
from collections import defaultdict

## for B4
n = 12
## for ATT
# n = 25
# n = 80
n = 197
nodes = [i for i in range(1, n + 1)]
Tc = {i:10000 for i in nodes}
## for B4
# edges_list = [(1,2),(1,4),(1,6),(2,3),(3,5),(4,5),(4,7),(4,8),(5,6),(6,7),(6,8),(7,8),(7,9),(8,10),(9,10),(9,11),(9,12),(10,11),(10,12)]

## for ATT
# edges_list = [(1,2),(1,3),(1,7),(1,8),(2,7),(3,4),(3,7),(3,10),(3,16),(3,17),(3,18),(3,21),(3,22),(4,9),(4,10),(4,7),(5,6),(5,8),(6,8),(6,9),(6,10),(6,14),
#           (6,15),(7,8),(9,10),(9,14),(10,14),(10,17),(10,23),(11,12),(11,14),(11,15),(12,13),(12,14),(12,15),(13,25),(13,14),(14,16),(14,17),
#           (14,18),(14,23),(16,17),(16,18),(16,22),(17,18),(18,19),(18,20),(18,21),(18,22),(18,23),(19,22),(20,21),(22,23),(23,24),(23,25),(24,25)]

# edges_list = [(1,44),(1,45),(2,45),(2,46),(2,72),(3,57),(3,4),(4,54),(5,66),(5,11),(6,66),(6,28),(6,53),(6,26),(7,55),(7,72),(8,30),(8,31),(9,10),(9,76),
#               (10,11),(11,56),(12,61),(12,56),(13,67),(13,60),(14,76),(14,37),(14,56),(15,59),(15,20),(16,59),(16,20),(17,19),(17,64),(18,50),(18,79),
#               (19,22),(19,23),(19,32),(20,33),(20,34),(20,39),(20,60,),(21,49),(21,23),(22,62),(24,26),(24,32),(25,29),(25,32),(27,28),(27,29),(30,76),
#               (31,46),(34,61),(35,82),(35,83),(35,80),(36,41),(36,54),(37,81),(38,61),(38,39),(39,60),(40,41),(41,42),(42,43),(42,44),(47,70),(47,48),(48,79),
#               (49,55),(50,73),(51,71),(51,63),(52,73),(52,68),(53,61),(56,67),(57,84),(58,65),(58,59),(62,70),(63,64),(68,69),(69,70),(69,71),(74,75),
#               (75,79),(77,78),(78,79),(78,80),(78,80)]

edges_list = [(1,177),(1,10),(2,9),(2,177),(2,115),(2,117),(2,176),(3,77),(3,78),(4,5),(4,78),(5,7),(5,136),(6,132),
              (6,7),(7,8),(8,9),(8,175),(9,195),(9,10),(9,192),(11,12),(11,14),(12,17),(13,33),(13,14),(13,31),(14,17),
              (14,16),(15,65),(15,130),(15,16),(17,18),(19,20),(19,31),(20,90),(20,69),(20,83),(21,22),(21,24),(22,27),
              (23,189),(23,24),(25,28),(26,172),(26,56),(27,28),(27,29),(27,30),(29,52),(29,55),(30,79),(31,36),(32,38),
              (33,34),(33,38),(35,38),(37,39),(37,40),(38,161),(38,39),(39,197),(40,182),(41,42),(41,43),(42,44),(42,190),
              (43,44),(43,144),(45,46),(45,48),(46,49),(46,165),(47,50),(47,48),(49,156),(49,182),(50,178),(50,166),
              (51,58),(51,52),(52,189),(53,54),(53,56),(54,59),(55,56),(57,58),(57,60),(59,60),(61,62),(61,70),(62,129),
              (62,123),(63,145),(63,87),(63,64),(64,69),(64,150),(65,66),(65,68),(65,69),(66,67),(67,68),(68,70),(70,145),
              (71,80),(71,184),(72,73),(72,80),(73,74),(74,75),(75,184),(76,174),(76,184),(77,174),(78,153),(78,163),(78,134),
              (79,95),(79,80),(81,82),(81,87),(81,88),(83,89),(83,84),(83,151),(84,149),(85,149),(85,86),(87,88),(88,89),(90,151),
              (91,173),(92,100),(92,93),(93,97),(93,94),(93,184),(95,172),(96,97),(96,172),(97,98),(98,173),(99,195),(99,132),
              (100,101),(101,133),(102,105),(102,181),(102,103),(103,110),(104,105),(104,107),(106,107),(106,108),(106,180),
              (108,109),(108,130),(109,180),(110,111),(111,129),(112,113),(112,141),(113,138),(114,115),(114,192),(116,117),
              (116,119),(118,121),(118,119),(120,177),(120,176),(121,176),(122,123),(122,125),(124,125),(124,126),(124,127),
              (128,129),(128,131),(130,131),(132,143),(133,136),(134,174),(135,138),(135,139),(135,136),(137,140),(138,173),
              (139,175),(139,142),(140,175),(141,142),(143,144),(144,186),(145,150),(146,158),(147,153),(147,155),(148,167),
              (148,178),(149,155),(150,151),(152,153),(153,154),(154,161),(154,155),(155,160),(155,184),(156,196),(156,157),
              (156,166),(157,158),(158,159),(159,184),(159,166),(162,163),(163,164),(163,168),(164,188),(164,165),(166,182),
              (166,185),(166,187),(167,171),(167,184),(168,169),(169,170),(170,186),(179,180),(182,197),(183,190),(184,185),
              (184,187),(187,188),(191,192),(193,194),(194,195),(196,197)]
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
    flows[h] = random.sample(pairs, 200)
for h in flows:
    for (src,dst) in flows[h]:
      if src == dst:
        flows[h].remove((src,dst))  
# while len(flows)>60:
#   flows.pop()
b = {(src,dst,h):50 for h in flows for (src,dst) in flows[h]}
m = {(src,dst,h):15 for h in flows for (src,dst) in flows[h]}
P = {}
for h in flows:
    for (src,dst) in flows[h]:   
        P[src,dst,h] = list(islice(nx.shortest_simple_paths(net, src, dst), 2))  
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
    # failed_link = random.sample(edges_list, 1)
    # (i,j) = failed_link[0]
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
    # print('Not affected flows: ', nonaffected_flows)
    print('='*50)
done = time.time()
elapsed = done - start
print('elapsed time:',elapsed)     


