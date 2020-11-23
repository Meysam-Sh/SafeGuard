from docplex.mp.model import Model 
import itertools
import time
from itertools import islice
import random, copy
import networkx as nx
from collections import defaultdict

## for B4
# n = 12
## for ATT
# n = 25

## for B4
# edges_list = [(1,2),(1,4),(1,6),(2,3),(3,5),(4,5),(4,7),(4,8),(5,6),(6,7),(6,8),(7,8),(7,9),(8,10),(9,10),(9,11),(9,12),(10,11),(10,12)]

## for ATT
# edges_list = [(1,2),(1,3),(1,7),(1,8),(2,7),(3,4),(3,7),(3,10),(3,16),(3,17),(3,18),(3,21),(3,22),(4,9),(4,10),(4,7),(5,6),(5,8),(6,8),(6,9),(6,10),(6,14),
#           (6,15),(7,8),(9,10),(9,14),(10,14),(10,17),(10,23),(11,12),(11,14),(11,15),(12,13),(12,14),(12,15),(13,25),(13,14),(14,16),(14,17),
#           (14,18),(14,23),(16,17),(16,18),(16,22),(17,18),(18,19),(18,20),(18,21),(18,22),(18,23),(19,22),(20,21),(22,23),(23,24),(23,25),(24,25)]


## for Cognet
# n = 197
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


nodes = [i for i in range(1, n + 1)]
Tc = {i:1000 for i in nodes}

## add the link with reverted direction to the edges_list 
aux = []
for (i,j) in edges_list:
  aux.append((j,i))
for (i,j) in aux:
  edges_list.append((i,j))  
## link capacities  
c = {(i,j):10000 for (i,j) in edges_list}
net = nx.DiGraph()
net.add_edges_from(edges_list)
## created random flows
pairs=list(itertools.product(net.nodes(), net.nodes()))
flows = random.sample(pairs, 1000)
for (src,dst) in flows:
  if src == dst:
    flows.remove((src,dst)) 
while len(flows)>1000:
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
            path_pairs1 = list(zip(path1, path1[1:]))
            Q[src,dst][i+j] = []
            if (i,j) not in path_pairs1:
                Q[src,dst][i+j].append(path1)
            if len(P[src,dst]) > 1:
                path2 = P[src,dst][1]
                path_pairs2 = list(zip(path2, path2[1:]))
                if (i,j) not in path_pairs2:
                    Q[src,dst][i+j].append(path2)    
            # elif (i,j) not in path_pairs2:
            #     Q[src,dst][i+j].append(path2)                     
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

min = 0 
max = 1
for (src ,dst) in Q:
    for s in Q[src,dst]:
        for p in Q[src,dst][s]:
            if len(p) < min:
                min = len(p)
            if len(p) > max:
                max = len(p)                   

start = time.time()
count = 0 
for (i,j) in edges_list: 
    count += 1
    print("**********************************",count,"**********************************")
## a random failed link                 
    failed_link = (i,j)
    # (i,j) = failed_link[0]
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
    mdl.minimize(mdl.sum(mdl.sum(100*x[src,dst,tuple(p)]*len(p) + mdl.sum(y[src,dst,tuple(p)]/c[i,j] for (i,j) in edges_list if (i,j) in list(zip(p, p[1:]))) for p in Q[src,dst][e]) for (src,dst) in affected_flows))
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

done = time.time()    
elapsed = done - start
print('elapsed time:',elapsed)

# for (src,dst) in affected_flows:
#      for p in Q[src,dst][e]:
#         #  if x[src,dst,tuple(e)] > 0:
#         print(x[src,dst,tuple(e)])
