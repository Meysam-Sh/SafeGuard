from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4
from ryu.lib import mac
import copy,itertools
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
import networkx as nx
import random
from ryu.lib import hub
from itertools import islice
import operator
from ryu.lib.packet import vlan
from collections import defaultdict
from operator import attrgetter

traffic_size = 50
c = 1000
class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.net=nx.DiGraph()
        self.all_pair_path={}
        self.all_backup_path = defaultdict(dict)
        self.backup_path = defaultdict(dict)
        self.weight1 = defaultdict(dict)
        self.weight2 = defaultdict(dict)
        self.group_id = {}
        self.rules = {}
        self.P = []
        self.table_ID = {}
        self.GroupCounter = []
        self.TableCounter = []
        self.reg = 0
        self.LinkNums = 0
        self.List = []
        self.load = {}
        self.traffic_size = {}
        self.DataPath = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.priority = {}
        self.net=nx.DiGraph()
        edges_list = [(1, 6, {'port': 4}), (11, 10, {'port': 3}), (10, 11, {'port': 4}), (5, 4, {'port': 3}), (4, 1, {'port': 2}), (4, 8, {'port': 5}),
        (8, 4, {'port': 2}), (5, 3, {  'port': 2}), (10, 9, {'port': 3}), (8, 7, {'port': 4}), (9, 7, {'port': 2}), (1, 2, {'port': 2}),
        (9, 11, {'port': 4}), (4, 5, {'port': 3}), (10, 8, {'port': 2}  ), (7, 9, {'port': 5}), (1, 4, {'port': 3}), (8, 6, {'port': 3}),
        (9, 10, {'port': 3}), (3, 2, {'port': 2}), (7, 4, {'port': 2}), (6, 8, {'port': 5}), (3, 5, {'port': 3}), (5, 6, {'port': 4}),
        (8, 10, {'port': 5}), (11, 9, {'port': 2}), (7,   8, {'port': 4}), (4, 7, {'port': 4}), (2, 3, {'port': 3}), (6, 5, {'port': 3}),
        (6, 1, {'port': 2}), (6, 7, {'port': 4}), (2, 1, {'port': 2}), (7, 6, {'port': 3}),(7, 6, {'port': 3}),(10, 12, {'port': 5}),
        (12, 10, {'port': 3}),(9, 12, {'port': 5}),(12, 9, {'port': 2})]
        
        # edges_list = [(1, 2, {'port': 2}),(2, 1, {'port': 2}),(1, 3, {'port': 3}),(3, 1, {'port': 2}),(1, 4, {'port': 4}),(7, 1, {'port': 2}),(1, 8, {'port': 5}),(8, 1, {'port': 2}),(2, 7, {'port': 3}),(7, 2, {'port': 3}),(3, 4, {'port': 3}),(4, 3, {'port': 2}),(3, 7, {'port': 4}),(7, 3, {'port': 4}),(3, 10, {'port': 5}),(10, 3, {'port': 2}),(3, 16, {'port': 6}),(6, 3, {'port': 2}),(3, 17, {'port': 7}),(17, 3, {'port': 2}),(3, 18, {'port': 8}),(18, 3, {'port': 2}),(3, 21, {'port': 9}),(21, 3, {'port': 2}),(3, 22, {'port': 10}),(22, 3, {'port': 2}),(4, 7, {'port': 5}),(7, 4, {'port': 5}),(4, 9, {'port': 3}),(9, 4, {'port': 2}),(4, 10, {'port': 4}),(10, 4, {'port': 3}),(5, 6, {'port': 2}),(6, 5, {'port': 2}),(5, 8, {'port': 3}),(8, 5, {'port': 3}),(6, 8, {'port': 3}),(8, 6, {'port': 4}),(6, 9, {'port': 4}),(9, 6, {'port': 3}),(6, 10, {'port': 5}),(10, 6, {'port': 4}),(6, 14, {'port': 6}),(14, 6, {'port': 2}),(6, 15, {'port': 7}),(15, 6, {'port': 2}),(7, 8, {'port': 6}),(8, 7, {'port': 5}),(9, 10, {'port': 4}),(10, 9, {'port': 5}),(9, 14, {'port': 5}),(14, 9, {'port': 3}),(10, 14, {'port': 6}),(14, 10, {'port': 4}),(10, 17, {'port': 7}),(17, 10, {'port': 3}),(10, 23, {'port': 8}),(23, 10, {'port': 2}),(11, 12, {'port': 2}),(12, 11, {'port': 2}),(11, 14, {'port': 3}),(14, 11, {'port': 5}),(11, 15, {'port': 4}),(15, 11, {'port': 3}),(12, 13, {'port': 3}),(13, 12, {'port': 2}),(12, 14, {'port': 4}),(14, 12, {'port': 6}),(12, 15, {'port': 5}),(15, 12, {'port': 4}),(13, 14, {'port': 4}),(14, 13, {'port': 7}),(13, 25, {'port': 3}),(25, 13, {'port': 2}),(14, 16, {'port': 8}),(16, 14, {'port': 3}),(14, 17, {'port': 9}),(17, 14, {'port': 4}),(14, 18, {'port': 10}),(18, 14, {'port': 3}),(14, 23, {'port': 11}),(23, 14, {'port': 3}),(16, 17, {'port': 4}),(17, 16, {'port': 5}),(16, 18, {'port': 5}),(18, 16, {'port': 4}),(16, 22, {'port': 6}),(22, 16, {'port': 3}),(17, 18, {'port': 6}),(18, 17, {'port': 5}),(18, 19, {'port': 6}),(19, 18, {'port': 2}),(18, 20, {'port': 7}),(20, 18, {'port': 2}),(18, 21, {'port': 8}),(21, 18, {'port': 3}),(18, 22, {'port': 9}),(22, 18, {'port': 4}),(18, 23, {'port': 10}),(23, 18, {'port': 4}),(19, 22, {'port': 3}),(22, 19, {'port': 5}),(20, 21, {'port': 3}),(21, 20, {'port': 4}),(22, 23, {'port': 6}),(23, 22, {'port': 5}),(23, 24, {'port': 6}),(24, 23, {'port': 2}),(23, 25, {'port': 7}),(25, 23, {'port': 3}),(24, 25, {'port': 3}),(25, 24, {'port': 4})]
        
        self.IPv4 = {1:"10.0.0.1", 2:"10.0.0.2", 3:"10.0.0.3", 4:"10.0.0.4", 5:"10.0.0.5",6:"10.0.0.6", 7:"10.0.0.7", 8:"10.0.0.8", 9:"10.0.0.9", 10:"10.0.0.10", 11:"10.0.0.11", 12:"10.0.0.12"}
        self.net.add_edges_from(edges_list)  
        for (i,j) in self.net.edges():
            self.load[i,j] = 0 
        for node in self.net.nodes():
            self.rules[node] = 0    
            
    events = [event.EventLinkAdd]
    @set_ev_cls(events)
    def get_topology(self, ev):
        self.net=nx.DiGraph()
        links = copy.copy(get_link(self, None)) 
        edges_list=[] 
        if len(links)>0:
            for link in links:
                src = link.src
                dst = link.dst
                edges_list.append((src.dpid,dst.dpid,{'port':src.port_no})) 
                self.load[src.dpid,dst.dpid] = 0
            self.net.add_edges_from(edges_list)  
        self.LinkNums += 1
        print('link  ', self.LinkNums)
        if self.LinkNums == 38 and self.reg == 12:
            print('links')           
            self.get_all_pair_path() 
            self.traffic_split()
            
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        self.GroupCounter.append(0)
        self.TableCounter.append(0)
        self.group_id[datapath.id] = 0
        self.table_ID[datapath.id] = 0
        self.priority[datapath.id] = 2
        self.DataPath[datapath.id] = datapath
        self.reg += 1
        self.List.append(datapath.id)
        self.List.sort()
        self.List = list(set(self.List))
        print(self.List,'len',len(self.List))
        if self.reg == 12:
            self.get_all_pair_path() 
            self.traffic_split()           
        # if len(self.List) == 25:
            # self.get_all_pair_path() 
            # self.traffic_split() 

    def add_flow(self, dp, p, match, actions, table=0):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=p, match=match, idle_timeout=0, hard_timeout=0, instructions=inst,table_id=table)
        dp.send_msg(mod)        
    
    def get_all_pair_path(self):
        nodes=self.net.nodes
        nodes=list(nodes)
        pairs=list(itertools.product(nodes, nodes))
        # src,dst = [1,3]
        for pair in pairs:
            src,dst=pair
            if src!=dst:
                self.all_pair_path[src,dst] = self.get_disjoint_paths(src,dst)
                self.traffic_size[src,dst] = traffic_size
        
        for (i,j) in self.net.edges():
            for (src,dst) in self.all_pair_path:
                for path in self.all_pair_path[src,dst]:
                # path = copy.copy(self.all_pair_path[src,dst][0])
                    if (i,j) in list(zip(path, path[1:])):
                        self.load[i,j] += self.traffic_size[src,dst] 

        for (src,dst) in self.all_pair_path:
            for r in self.all_pair_path[src,dst]: 
                # n = self.all_pair_path[src,dst].index(r)
                path_pairs = list(zip(r, r[1:]))
                edges = copy.copy(self.net.edges())
                edges = list(edges)
                from_source = []
                for (i,j) in edges:
                    if i == src:
                        from_source.append((i,j))
                for (i,j) in from_source:
                    edges.remove((i,j))
                    
                for (i,j) in path_pairs[1:]:  
                    path1 = self.all_pair_path[src,dst][0]
                    path2 = self.all_pair_path[src,dst][1]
                    path_pairs1 = list(zip(path1, path1[1:]))
                    path_pairs2 = list(zip(path2, path2[1:]))
                    self.all_backup_path[src,dst][i] = []
                    if (i,j) not in path_pairs1:
                        self.all_backup_path[src,dst][i].append(path1)
                    elif (i,j) not in path_pairs2:
                        self.all_backup_path[src,dst][i].append(path2)                     
                    path = copy.copy(r)
                    
                    # portion = path[0:path[path.index(i)-1]]
                    portion = path[0:path.index(i)+1]
                    remaining_edges = copy.copy(edges)
                    remaining_edges.remove((i,j))
                    portion_pairs = list(zip(portion, portion[1:]))
                    for (p,q) in portion_pairs:
                        if (p,q) in remaining_edges:
                            remaining_edges.remove((p,q))
                            remaining_edges.remove((q,p))    
                    newgraph = nx.DiGraph()
                    newgraph.add_edges_from(remaining_edges)  
                    # self.backup_path[src,dst][i] = []  
                    has_path = False
                    if i in newgraph.nodes():
                        if nx.has_path(newgraph,i,dst):
                            has_path = True
                            try:
                                path1,path2 = self.k_shortest_paths(newgraph,i,dst,2)
                                self.backup_path[src,dst][i] = [path1,path2]
                            except: 
                                self.backup_path[src,dst][i] = [list(nx.shortest_path(newgraph,i,dst))]
                    if len(portion):   
                        # self.all_backup_path[src,dst][i].append(portion) 
                        if has_path:
                            for backup in self.backup_path[src,dst][i]:
                                # print(src,dst,portion,backup)
                                backup_path = portion[0:-1] + backup                       
                                self.all_backup_path[src,dst][i].append(backup_path)  
        
        aux = copy.copy(self.all_backup_path)
        for i in self.all_backup_path.keys():
            aux = self.all_backup_path[i]
            for j in aux.keys():
                for k in range(len(aux[j])):
                    self.P.append(aux[j][k])
        self.P.sort(key=len)
                        
    def traffic_split(self):
        for (i,j) in self.net.edges():
            affected_flows = []
            for (src,dst) in self.all_pair_path:
                for path in self.all_pair_path[src,dst]:
                    test = copy.copy(path)
                    path_pairs = list(zip(path, path[1:]))
                    path_pairs = path_pairs[1:]
                    if (i,j) in path_pairs:
                        affected_flows.append((src,dst))                   
                        for (p,q) in path_pairs[path_pairs.index((i,j))+1:]:
                            self.load[p,q] -= .05*self.traffic_size[src,dst] 
                        break
                        
            aux = {}        
            for (src,dst) in affected_flows:
                aux[src,dst] = self.traffic_size[src,dst] 
                self.weight1[src,dst][i] = []
            sorted_aux = dict(sorted(aux.items(), key=operator.itemgetter(1)))
            
            demand = copy.copy(self.traffic_size)
            for path in self.P:
                for (src,dst) in sorted_aux:
                    if path in self.all_backup_path[src,dst][i]:                      
                        b = self.get_bottleneck_link(path)
                        if len(self.weight1[src,dst][i]) == 3:
                            break
                        path_pairs = list(zip(path, path[1:]))    
                        for (p,q) in path_pairs:
                            if self.rules[p] > c:
                                break
                        a = min(self.traffic_size[src,dst],b)   
                        self.rules[p] += 1
                        for (p,q) in path_pairs:
                            self.load[p,q] += a
                        demand[src,dst] -= a
                        weight = int(100*(a/self.traffic_size[src,dst]))
                        self.weight1[src,dst][i].append(weight)
                        if demand[src,dst] == 0:
                            del sorted_aux[src,dst]
                            
            self.weight2[src,dst][i] = []                
            for (src,dst) in affected_flows:            
                bw = []
                for bachup in self.backup_path[src,dst][i]:
                    bw.append(self.get_bottleneck_link(bachup))
                for b in bw:
                    weight = int(b/sum(bw))
                    self.weight2[src,dst][i].append(weight)                            
        print('Finished')           
        
    def get_disjoint_paths(self,src,dst):
        edge_disjoint_paths = list(nx.edge_disjoint_paths(self.net, src, dst))
        path1 = edge_disjoint_paths[0]
        path2 = edge_disjoint_paths[1]
        paths = [path1, path2]
        return paths       
        
    def k_shortest_paths(self, G, source, target, k):
        return list(islice(nx.shortest_simple_paths(G, source, target), k))    
           
    def get_bottleneck_link(self,path):
        path_bw = []
        for (i,j) in list(zip(path, path[1:])):
            path_bw.append(c - self.load[i,j])
        bottleneck_link = min(path_bw)
        return bottleneck_link    
    
    def forwarding(self, msg, eth_type, ip_src, ip_dst):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        flow_info = (eth_type, ip_src, ip_dst)
        src_sw=int(ip_src.split('.')[3])
        dst_sw=int(ip_dst.split('.')[3])
        print(src_sw,dst_sw)
        curr_sw=datapath.id   
        # print('src', src_sw, 'dst:',dst_sw, 'curr:', curr_sw,'\n')
        
        self.GroupCounter[curr_sw-1] += 3
        self.TableCounter[curr_sw-1] += 1
        group_id = int(src_sw)*3+int(dst_sw)*2
        table_ID = int(src_sw)*3+int(dst_sw)*2 
        priority = int(src_sw)*3+int(dst_sw)*2
        
        actions = [parser.OFPActionGroup(group_id)]
        match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
        self.add_flow(datapath, 200, match, actions, table = 0)
        
        path1 = self.all_pair_path[src_sw,dst_sw][0]
        path2 = self.all_pair_path[src_sw,dst_sw][1]
        next_sw1 = path1[path1.index(src_sw)+1]
        next_sw2 = path2[path2.index(src_sw)+1]
        out_port1 = self.net[src_sw][next_sw1]['port']
        out_port2 = self.net[src_sw][next_sw2]['port']
        out_port = [out_port1,out_port2]
        
        buckets = [parser.OFPBucket(weight=1, actions= [parser.OFPActionGroup(100)]),
                   parser.OFPBucket(weight=1, actions= [parser.OFPActionGroup(200)])]
        # Add SELECT group
        req = parser.OFPGroupMod(datapath, ofproto.OFPFC_ADD,ofproto.OFPGT_SELECT, group_id, buckets)
        datapath.send_msg(req)
            
        # FFG1: defult out_port is set to the eth of the first path. The backup out_port is set to the eth of the second path
        actions1 = [parser.OFPActionOutput(out_port1)]
        actions2 = [parser.OFPActionOutput(out_port2)]
        weight = 0
        buckets = [parser.OFPBucket(weight,out_port1,ofproto.OFPG_ANY,actions1),
                   parser.OFPBucket(weight,out_port2,ofproto.OFPG_ANY,actions2)]
        req = parser.OFPGroupMod(datapath,ofproto.OFPGC_ADD,ofproto.OFPGT_FF,100,buckets)                  
        datapath.send_msg(req)
        
        # FFG2: defult out_port is set to the eth of the second path. The backup out_port is set to the eth of the third path
        actions1 = [parser.OFPActionOutput(out_port2)]
        actions2 = [parser.OFPActionOutput(out_port1)]
        weight = 0
        buckets = [parser.OFPBucket(weight,out_port2,ofproto.OFPG_ANY,actions1),
                   parser.OFPBucket(weight,out_port1,ofproto.OFPG_ANY,actions2)]                 
        req = parser.OFPGroupMod(datapath,ofproto.OFPGC_ADD,ofproto.OFPGT_FF,200,buckets)                  
        datapath.send_msg(req)                   
        
        for path in self.all_pair_path[src_sw,dst_sw]:
            for i in path[1:-1]:
                if len(self.all_backup_path[src_sw,dst_sw][i])>0:
                    self.GroupCounter[src_sw-1] += 1
                    group_id = int(src_sw)*3+int(dst_sw)*2+i
                    l = len(self.weight1[src_sw,dst_sw][i])
                    buckets = []
                    watch_group = ofproto_v1_3.OFPQ_ALL 
                    for n in range(l):
                        action = [parser.OFPActionOutput(out_port[n])]
                        buckets.append(parser.OFPBucket(self.weight1[src_sw,dst_sw][i][n], out_port[n], watch_group, action))
                    req = parser.OFPGroupMod(datapath, ofproto.OFPFC_ADD,ofproto.OFPGT_SELECT, group_id, buckets)
                    datapath.send_msg(req)      
        
        duplicate = []
        for path in self.all_pair_path[src_sw,dst_sw]:
            for curr in path[1:-1]:
                duplicate.append(curr)
                pairs = list(zip(duplicate, duplicate[1:]))
                if (curr,path[path.index(curr)+1]) not in pairs: 
                    datapath = self.DataPath[curr]
                    prev = path[path.index(curr)-1]
                    in_port = self.net[curr][prev]['port']
                    self.priority[curr] += 1
                    table_ID = int(src_sw)*3+int(dst_sw)*2+4*curr
                    group_id = int(src_sw)*3+int(dst_sw)*4*curr
                    match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])                    
                    self.group_id[curr] += 1 
                    group_id = int(src_sw)*3+int(dst_sw)*2+i
                    self.GroupCounter[curr-1] += 1
                    
                    next_sw = path[path.index(curr)+1]
                    out_port = self.net[curr][next_sw]['port']
                    next_sw1 = backup1[backup1.index(curr)+1]
                    next_sw2 = backup2[backup2.index(curr)+1]
                    out_port1 = self.net[curr][next_sw1]['port']
                    out_port2 = self.net[curr][next_sw2]['port']
                    actions1 = [parser.OFPActionOutput(out_port1)]
                    actions2 = [parser.OFPActionOutput(out_port2)]
                    watch_group = ofproto_v1_3.OFPQ_ALL 
                    
                    buckets = []
                    watch_group = ofproto_v1_3.OFPQ_ALL 
                    for backup in self.backup_path[src_sw,dst_sw][curr]:
                        backup = self.backup_path[src_sw,dst_sw][curr]
                        next_sw = backup1[backup.index(curr)+1]
                        out_port = self.net[curr][next_sw1]['port']
                        actions = [parser.OFPActionOutput(out_port)]
                        buckets.append(parser.OFPBucket(1, out_port, watch_group, action))
                    req = parser.OFPGroupMod(datapath, ofproto.OFPFC_ADD,ofproto.OFPGT_SELECT, group_id, buckets)
                    datapath.send_msg(req) 
                    
                    inst=[parser.OFPInstructionGotoTable(table_ID)]
                    match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
                    mod = parser.OFPFlowMod(datapath=datapath, priority=self.priority[curr], idle_timeout=0, hard_timeout=0, 
                                        match=match, instructions=inst,table_id=0)
                    datapath.send_msg(mod)
                    
                    actions = [parser.OFPActionOutput(out_port)]
                    match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
                    self.add_flow(datapath, 0, match, actions, table = table_ID)
                    
                    for backup in self.backup_path[src_sw,dst_sw][curr]:
                        for i in backup[1:-1]:
                            datapath = self.DataPath[i]
                            prev = backup[backup.index(i)-1]
                            # print(i,prev)
                            in_port = self.net[i][prev]['port']
                            self.priority[i] += 1
                            self.TableCounter[dst_sw-1] += 1
                            next_sw = backup[backup.index(i)+1]
                            out_port = self.net[i][next_sw]['port']    
                            actions = [parser.OFPActionOutput(out_port)]
                            match = parser.OFPMatch(eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
                            self.add_flow(datapath, self.priority[i], match, actions,table=0)    
                 
        datapath = self.DataPath[dst_sw]
        self.TableCounter[dst_sw-1] += 1
        self.table_ID[dst_sw] += 1
        self.priority[dst_sw] += 1
        actions = [parser.OFPActionOutput(1)]
        match = parser.OFPMatch(eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
        self.add_flow(datapath, self.priority[dst_sw], match, actions,table=0)
    
        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,data=msg.data, in_port=in_port, actions=actions)
        datapath.send_msg(out)    
        print(sum(self.GroupCounter))
        print(sum(self.TableCounter))
        return    

    @set_ev_cls(event.EventLinkDelete, MAIN_DISPATCHER)
    def link_failure_handler(self, ev):
        link = ev.link
        if "DOWN" not in str(link.src):
            return
        h1 = link.src.dpid
        h2 = link.dst.dpid
        print "Failure link:(",h1,",",h2,")"
        modify = False
        for (src,dst) in self.all_pair_path:
            print("===")
            print(src,dst)
            for i in range(len(self.all_pair_path[src,dst])):
                path = copy.copy(self.all_pair_path[src,dst][i])
                path = path[1:]
                if (h1,h2) in list(zip(path, path[1:])):
                    print("has")
                    modify = True
                    intermidate = h1
                if (h2,h1) in list(zip(path, path[1:])):
                    print("has")
                    modify = True
                    intermidate = h2
                print("===")
                if modify:
                    datapath = self.DataPath[src]
                    parser = datapath.ofproto_parser
                    ofproto = datapath.ofproto
                    table_ID = int(src)*3+int(dst)*2+intermidate
                    
                    inst=[parser.OFPInstructionGotoTable(table_ID)]
                    match = parser.OFPMatch(in_port=1, eth_type=2048, ipv4_src=self.IPv4[src], ipv4_dst=self.IPv4[dst])
                    mod = parser.OFPFlowMod(datapath=datapath, priority=200,
                                match=match, instructions=inst, command = ofproto.OFPFC_MODIFY, table_id=0)
                    datapath.send_msg(mod)

    def _monitor(self):
        while True:
            for dp in self.DataPath.values():
                if dp.id < 13:
                    self._request_stats(dp)
            hub.sleep(45)
            
    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if isinstance(ip_pkt, ipv4.ipv4):
            if ip_pkt.src == '0.0.0.0':
                return 
            if len(pkt.get_protocols(ethernet.ethernet)):
                eth_type = pkt.get_protocols(ethernet.ethernet)[0].ethertype
                self.forwarding(msg, eth_type, ip_pkt.src, ip_pkt.dst)    
