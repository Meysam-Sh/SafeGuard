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
import initilization

# topo = raw_input("Select a topology")
# edge_list, n, number_of_links = initilization.Get_edges(topo)
n, number_of_links, number_of_primary_routes = 12 , 38, 8 
# flows = initilization.TMGeneration(n)
Pri = [30,20,10]
flows = {}
for i in range(1,13):
  for j in range(1,13):
    for h in Pri:
      if j!=i:
        flows[i,j,h] = random.randint(20,100)
 
memory_demand = {}
for (src,dst,h) in flows:
    memory_demand[src,dst,h] = 1
print(int(0.2*len(flows.keys())))    
for (src,dst,h) in random.sample(flows.keys(), int(0.2*len(flows.keys()))):
    memory_demand[src,dst,h] = random.randint(100, 1000)    

nodes = [i for i in range(1,n+1)]
link_capacity = 1000
TCAM = [750,1500,2000,16000]
#switch_capacity = {i:np.random.choice(TCAM) for i in nodes} 
switch_capacity = {i:15000 for i in nodes}

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
        self.index = defaultdict(dict)
        self.group_id = {}
        self.rules = {}
        self.P = []
        self.table_ID = {}
        self.GroupCounter = []
        self.TableCounter = []
        self.Registered = 0
        self.LinkNums = 0
        self.List = []
        self.capacity = {}
        self.load = {}
        self.use = {}
        self.traffic_size = {}
        self.DataPath = {}
        # self.monitor_thread = hub.spawn(self._monitor)
        self.priority = {}
        self.net=nx.DiGraph()  
        self.IPv4 = {1:"10.0.0.1", 2:"10.0.0.2", 3:"10.0.0.3", 4:"10.0.0.4", 5:"10.0.0.5",6:"10.0.0.6", 7:"10.0.0.7", 8:"10.0.0.8", 9:"10.0.0.9", 10:"10.0.0.10",
                     11:"10.0.0.11", 12:"10.0.0.12",13:"10.0.0.13", 14:"10.0.0.14", 15:"10.0.0.15", 16:"10.0.0.16", 17:"10.0.0.17", 18:"10.0.0.18", 17:"10.0.0.17",
                     18:"10.0.0.8", 19:"10.0.0.19", 20:"10.0.0.20", 21:"10.0.0.21", 22:"10.0.0.22", 23:"10.0.0.23", 24:"10.0.0.24", 25:"10.0.0.25"}
            
    events = [event.EventLinkAdd]
    @set_ev_cls(events)
    def get_topology(self, ev):
        self.net=nx.DiGraph()
        links = copy.copy(get_link(self, None)) 
        edges_list=[] 
        if len(links)> 0:
            for link in links:
                src = link.src
                dst = link.dst
                edges_list.append((src.dpid,dst.dpid,{'port':src.port_no})) 
                self.load[src.dpid,dst.dpid] = 0
            self.net.add_edges_from(edges_list)  
        self.LinkNums += 1
        print('link  ', self.LinkNums)
        if self.LinkNums == number_of_links and self.reg == n:
            print('**** ALL CONNECTED')           
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
        self.priority[datapath.id] = 300
        self.DataPath[datapath.id] = datapath
        self.Registered += 1
        self.List.append(datapath.id)
        self.List.sort()
        self.List = list(set(self.List))
        print(self.List,'len',len(self.List))        

    def add_flow(self, dp, p, match, actions, table=0):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
        mod = parser.OFPFlowMod(datapath = dp, priority = p, match = match, idle_timeout = 0, hard_timeout = 0, instructions = inst,table_id = table)
        dp.send_msg(mod)        
    
    def get_all_pair_path(self):
        nodes=self.net.nodes
        nodes=list(nodes)
        pairs=list(itertools.product(nodes, nodes))
        for pair in pairs:
            src,dst=pair
            if src!=dst:
                paths = self.k_shortest_paths(self.net,src,dst,number_of_primary_paths)
                paths = sorted(paths, key=len)
                self.all_pair_path[src,dst] = paths
            # for i in range(paths):
                # self.all_pair_path[src,dst,H[i]] = paths[i]
                        
        for (src,dst) in self.all_pair_path:
            for r in self.all_pair_path[src,dst]: 
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
                    path_pairs1 = list(zip(path1, path1[1:]))                   
                    self.all_backup_path[src,dst][i] = []
                    if (i,j) not in path_pairs1:
                        self.all_backup_path[src,dst][i].append(path1)
                    if len(self.all_backup_path[src,dst]) == 2:    
                        path2 = self.all_pair_path[src,dst][1]
                        path_pairs2 = list(zip(path2, path2[1:]))
                        if (i,j) not in path_pairs2:
                            self.all_backup_path[src,dst][i].append(path2)
                    if len(self.all_backup_path[src,dst]) == 2:    
                        path3 = self.all_pair_path[src,dst][2]
                        path_pairs3 = list(zip(path3, path3[1:]))
                        if (i,j) not in path_pairs3:
                            self.all_backup_path[src,dst][i].append(path3)              
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
                    if i in newgraph.nodes():
                        if nx.has_path(newgraph,i,dst):
                            backup_path = list(nx.shortest_path(newgraph,i,dst))
                            if len(portion): 
                                backup_path += portion[0:-1]                       
                                self.all_backup_path[src,dst][i].append(backup_path) 
        
    def traffic_split(self):
        for (i,j) in self.net.edges():
            for (p,q) in self.net.edges():
                self.load[p,q] = 0 
                self.capacity[p,q] = copy.copy(link_capacity)
                        
            affected_flows = []
            nonaffected_flows = []
            for (src,dst) in self.all_pair_path:
                for path in self.all_pair_path[src,dst]:
                    index = self.all_pair_path[src,dst].index(path)
                    path_pairs = list(zip(path, path[1:]))
                    path_pairs = path_pairs[1:]
                    if (i,j) in path_pairs:
                        affected_flows.append((src,dst))          
                        break                      
                if (src,dst) not in affected_flows:
                    nonaffected_flows.append((src,dst)) 
                    
            for (src,dst) in nonaffected_flows:
                for path in self.all_pair_path[src,dst]: 
                    index = self.all_pair_path[src,dst].index(path)
                    for (p,q) in list(zip(path, path[1:])):
                        self.load[p,q] += flows[src,dst,H[index]] 
                        self.capacity[p,q] -= flows[src,dst,H[index]]
                        self.use[p,q] += 1                

            aux = {}  
            index = {}
            for (src,dst,h) in affected_flows:
                index[src,dst] = 0
                self.weight1[src,dst][i] = [1,1,1]
                self.index[src,dst][i] = []
            
            for h in H:   
                notSorted = {}
                for (src,dst) in self.all_pair_path:
                    if (src,dst,h) in affected_flows:
                        notSorted[src,dst,h] = affected_flows[src,dst,h]
                sorted = dict(notSorted(aux.items(), key=operator.itemgetter(1), reverse=True))  
                for (x,y,z) in sorted:
                    aux[x,y,z] = sorted[x,y,z] 
            demand = copy.copy(flows[src,dst,h])    
            
            for (src,dst,h) in aux:
                for path in self.all_backup_path[src,dst][i]:                      
                    b = self.get_bottleneck_link(path)
                    if b != 0:   
                        path_pairs = list(zip(path, path[1:]))    
                        for (p,q) in path_pairs:
                            if self.rules[p] + m[H.index(h)] > switch_capacity[p]*mu:
                        # self.backup_path[src,dst][i].append(path)        
                                a = min(demand[src,dst,h],b)
                                forward = True  
                            elif switch_capacity[p]*mu <= self.rules[p] + m[H.index(h)] < switch_capacity[p]:
                                if flows[src,dst,h] <= b:
                                    a = flows[src,dst,h]
                                    forward = True
                            if forward:
                                weight = int(100*(a/ flows[src,dst,h]))         
                                self.weight1[src,dst][i][index[src,dst]] = weight
                                self.index[src,dst][i].append(self.all_backup_path[src,dst,h][i].index(path))
                                index[src,dst] += 1      
                                
                                self.rules[p] += memory_demand[src,dst,h]
                                for (p,q) in path_pairs:
                                    self.load[p,q] += a
                                    self.capacity[p,q] -= a
                                demand[src,dst,h] -= a  
        print('Finished')               
        
    def k_shortest_paths(self, G, source, target, k):
        return list(islice(nx.shortest_simple_paths(G, source, target), k))    
           
    def get_bottleneck_link(self,path):
        path_bw = []
        for (i,j) in list(zip(path, path[1:])):
            path_bw.append(self.capacity[i,j])
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
        intermediate_sw=datapath.id   
        self.GroupCounter[src_sw-1] += 3
        self.TableCounter[src_sw-1] += 1
        group_id = priority = int(src_sw)*200+int(dst_sw)*100
        
        actions = [parser.OFPActionGroup(group_id)]
        match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
        self.add_flow(datapath, priority, match, actions, table = 0)
        
        path1 = self.all_pair_path[src_sw,dst_sw][0]
        path2 = self.all_pair_path[src_sw,dst_sw][1]
        path3 = self.all_pair_path[src_sw,dst_sw][2]
        next_sw1 = path1[path1.index(src_sw)+1]
        next_sw2 = path2[path2.index(src_sw)+1]
        next_sw3 = path3[path3.index(src_sw)+1]
        out_port1 = self.net[src_sw][next_sw1]['port']
        out_port2 = self.net[src_sw][next_sw2]['port']
        out_port3 = self.net[src_sw][next_sw3]['port']
        
        buckets = [parser.OFPBucket(weight=1, actions= [parser.OFPActionGroup(group_id+1)]),
                   parser.OFPBucket(weight=1, actions= [parser.OFPActionGroup(group_id+2)]),
                   parser.OFPBucket(weight=1, actions= [parser.OFPActionGroup(group_id+3)]),]
        req = parser.OFPGroupMod(datapath, ofproto.OFPFC_ADD,ofproto.OFPGT_SELECT, group_id, buckets)
        datapath.send_msg(req)
        
       
        actions1 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:01"), parser.OFPActionOutput(out_port1)]
        actions2 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:02"), parser.OFPActionOutput(out_port2)]
        watch_group = 0
        weight = 0
        buckets = [parser.OFPBucket(weight,out_port1,watch_group,actions1),
                   parser.OFPBucket(weight,out_port2,watch_group ,actions2)]
        req = parser.OFPGroupMod(datapath,ofproto.OFPGC_ADD,ofproto.OFPGT_FF,group_id+1,buckets)                  
        datapath.send_msg(req)
        
        actions1 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:02"), parser.OFPActionOutput(out_port2)]
        actions2 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:03"), parser.OFPActionOutput(out_port3)]
        buckets = [parser.OFPBucket(weight,out_port2,watch_group,actions1),
                   parser.OFPBucket(weight,out_port3,watch_group,actions2)]                 
        req = parser.OFPGroupMod(datapath,ofproto.OFPGC_ADD,ofproto.OFPGT_FF,group_id+2,buckets)                  
        datapath.send_msg(req)        

        actions1 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:03"), parser.OFPActionOutput(out_port3)]
        actions2 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:02"), parser.OFPActionOutput(out_port2)]
        buckets = [parser.OFPBucket(weight,out_port3,watch_group,actions1),
                   parser.OFPBucket(weight,out_port2,watch_group,actions2)]                 
        req = parser.OFPGroupMod(datapath,ofproto.OFPGC_ADD,ofproto.OFPGT_FF,group_id+3,buckets)                  
        datapath.send_msg(req)    
        
        for path in self.all_pair_path[src_sw,dst_sw]:
            for i in path[1:-1]:
                group_id = int(src_sw)*100+int(dst_sw)*50+31*i
                l = len(self.weight1[src_sw,dst_sw][i])
                buckets = []
                for n in range(l):
                    try: 
                        s = self.index[src_sw,dst_sw][i][n]
                        path = self.all_backup_path[src_sw,dst_sw][i][s]
                        next_sw = path[path.index(src_sw)+1]
                        out_port = self.net[src_sw][next_sw]['port'] 
                        action = [parser.OFPActionOutput(out_port)]
                        buckets.append(parser.OFPBucket(self.weight1[src_sw,dst_sw][i][n], out_port,watch_group, action))
                    except:
                        pass
                req = parser.OFPGroupMod(datapath, ofproto.OFPFC_ADD,ofproto.OFPGT_SELECT, group_id, buckets)
                datapath.send_msg(req)      
        
        duplicates = []
        for Path in self.all_pair_path[src_sw,dst_sw]:
            for intermediate in Path[1:-1]:
                datapath = self.DataPath[intermediate]
                self.group_id[intermediate] += 1
                next_sw1 = Path[Path.index(intermediate)+1] 
                path = self.all_backup_path[src_sw,dst_sw][i]
                next_sw2 = path[path.index(intermediate)+1]  
                out_port1 = self.net[intermediate][next_sw1]['port']                
                out_port2 = self.net[intermediate][next_sw2]['port']                 
                actions1 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:01"), parser.OFPActionOutput(out_port1)]
                actions2 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:02"), parser.OFPActionOutput(out_port2)]
                prev = Path[Path.index(intermediate)-1]
                in_port = self.net[intermediate][prev]['port']
                self.priority[intermediate] -= 1
                self.TableCounter[intermediate-1] += 1
                Match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
                actions = [parser.OFPActionGroup(self.group_id[intermediate])]
                self.add_flow(datapath, self.priority[intermediate], Match, actions, table = 0) 
                
                watch_group = 0
                weight = 0
                buckets = [parser.OFPBucket(weight,out_port1,watch_group,actions1),
                           parser.OFPBucket(weight,out_port2,watch_group,actions2)]
                req = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD,ofproto.OFPGT_FF,self.group_id[intermediate],buckets)
                datapath.send_msg(req)
                    
        datapath = self.DataPath[dst_sw]
        self.TableCounter[dst_sw-1] += 1
        self.priority[dst_sw] -= 1
        actions = [parser.OFPActionOutput(1)]
        match = parser.OFPMatch(eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
        self.add_flow(datapath, self.priority[dst_sw], match, actions,table=0)
    
        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,data=msg.data, in_port=in_port, actions=actions)
        datapath.send_msg(out)    
        print("==========number of rules==========")
        print((sum(self.GroupCounter)+sum(self.TableCounter))/2)
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
            for i in range(len(self.all_pair_path[src,dst])):
                path = copy.copy(self.all_pair_path[src,dst][i])
                path = path[1:]
                if (h1,h2) in list(zip(path, path[1:])):
                    modify = True
                    intermidate = h1
                if (h2,h1) in list(zip(path, path[1:])):
                    modify = True
                    intermidate = h2
                if modify:
                    datapath = self.DataPath[src]
                    parser = datapath.ofproto_parser
                    ofproto = datapath.ofproto
                    group_id = int(src)*200+int(dst)*100+31*i
                    
                    actions = [parser.OFPActionGroup(group_id)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
                    match = parser.OFPMatch(in_port=1, eth_type=2048, ipv4_src=self.IPv4[src], ipv4_dst=self.IPv4[dst])
                    mod = parser.OFPFlowMod(datapath=datapath, priority=int(src)*200+int(dst)*100, idle_timeout=0, hard_timeout=0,
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
