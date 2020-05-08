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
from ryu.lib.packet import vlan
from collections import defaultdict

# time_to_collect=1000000
class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.net=nx.DiGraph()
        self.all_pair_path={}
        self.all_backup_path = defaultdict(dict)
        self.group_id = {}
        self.table_ID = {}
        self.GroupCounter = []
        self.TableCounter = []
        self.LinkNums = 0
        self.DataPath = {}
        self.priority = {}
        self.IPv4 = {1:"10.0.0.1", 2:"10.0.0.2", 3:"10.0.0.3", 4:"10.0.0.4", 5:"10.0.0.5",
                        6:"10.0.0.6", 7:"10.0.0.7", 8:"10.0.0.8", 9:"10.0.0.9", 10:"10.0.0.10"}
        
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

    def add_flow(self, dp, p, match, actions, table=0):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=p, match=match, instructions=inst,table_id=table)
        dp.send_msg(mod)

    # events = [event.EventSwitchEnter,
              # event.EventSwitchLeave, event.EventPortAdd,
              # event.EventLinkAdd]
              
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
            self.net.add_edges_from(edges_list)   
        self.LinkNums += 1
        if self.LinkNums == 20:
            print("yesss")
            self.get_all_pair_path()
            
    
    def get_all_pair_path(self):
        nodes=self.net.nodes
        nodes=list(nodes)
        pairs=list(itertools.product(nodes, nodes))
        for pair in pairs:
            src,dst=pair
            if src!=dst:
                paths = self.get_disjoint_paths(src,dst)
                self.all_pair_path[src,dst] = paths

        for (src,dst) in self.all_pair_path:
            path1, path2 = copy.copy(self.all_pair_path[src,dst])
            
            path_pairs1 = list(zip(path1, path1[1:]))
            path_pairs2 = list(zip(path2, path2[1:]))
            
            from_source = []
            edges=self.net.edges()
            edges = list(edges)
            for (i,j) in edges:
                if i == src:
                    from_source.append((i,j))
            for (i,j) in from_source:
                edges.remove((i,j))
            remaining_edges1 = copy.copy(edges)
            remaining_edges2 = copy.copy(edges)
            for (i,j) in path_pairs1[1:]:
                remaining_edges2.remove((i,j)) 
            for (i,j) in path_pairs2[1:]:
                remaining_edges1.remove((i,j)) 
                
            for (i,j) in path_pairs1[1:]:  
                self.all_backup_path[src,dst][i] = [path2]
                aux = copy.copy(remaining_edges1)
                for (p,q) in path_pairs1[path_pairs1.index((i,j)):]:
                    aux.remove((p,q))
                newgraph = nx.DiGraph()
                newgraph.add_edges_from(aux)
                if i in newgraph.nodes():
                    if nx.has_path(newgraph,i,dst):             
                        backup_path = list(nx.shortest_path(newgraph,i,dst))
                        self.all_backup_path[src,dst][i].append(backup_path) 
            
            for (i,j) in path_pairs2[1:]:  
                self.all_backup_path[src,dst][i] = [path1]
                aux = copy.copy(remaining_edges2)
                for (p,q) in path_pairs2[path_pairs2.index((i,j)):]:
                    aux.remove((p,q))
                newgraph = nx.DiGraph()
                newgraph.add_edges_from(aux)
                if i in newgraph.nodes():
                    if nx.has_path(newgraph,i,dst):             
                        backup_path = list(nx.shortest_path(newgraph,i,dst))
                        self.all_backup_path[src,dst][i].append(backup_path)
        
    def get_disjoint_paths(self,src,dst):
        edge_disjoint_paths = list(nx.edge_disjoint_paths(self.net, src, dst))
        path1 = edge_disjoint_paths[0]
        path2 = edge_disjoint_paths[1]
        paths = [path1, path2]
        return paths
    
    def forwarding(self, msg, eth_type, ip_src, ip_dst):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        flow_info = (eth_type, ip_src, ip_dst)
        src_sw=int(ip_src.split('.')[3])
        dst_sw=int(ip_dst.split('.')[3])
        curr_sw=datapath.id   
    
        self.GroupCounter[curr_sw-1] += 1
        self.TableCounter[curr_sw-1] += 1
        group_id = int(src_sw)*3+int(dst_sw)*2
        table_ID = int(src_sw)*3+int(dst_sw)*2
        
        # actions = [parser.OFPActionOutput(2)]
        inst=[parser.OFPInstructionGotoTable(table_ID)]
        match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
        mod = parser.OFPFlowMod(datapath=datapath, priority=200,
                            match=match, instructions=inst,table_id=0)
        datapath.send_msg(mod)
        
        path1,path2 = self.all_pair_path[src_sw,dst_sw]
        next_sw1 = path1[path1.index(src_sw)+1]
        next_sw2 = path2[path2.index(src_sw)+1]
        
        # One oup_port for each path
        out_port1 = self.net[src_sw][next_sw1]['port']
        out_port2 = self.net[src_sw][next_sw2]['port']
        
        # A SELECT group with three buckets. Each bucket tags the packet and then it points to a FFG
        actions_1 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:01"), parser.OFPActionGroup(100)]
        actions_2 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:02"), parser.OFPActionGroup(200)]
        # actions_1 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:01"), parser.OFPActionOutput(out_port1)]
        # actions_2 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:02"), parser.OFPActionOutput(out_port2)]
        weight_1 = 50
        weight_2 = 50
        watch_group = ofproto_v1_3.OFPQ_ALL
        watch_port = ofproto_v1_3.OFPP_ANY
        buckets = [
            parser.OFPBucket(weight_1, out_port1, watch_group, actions_1),
            parser.OFPBucket(weight_2, out_port2, watch_group, actions_2)]
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
        
        actions = [parser.OFPActionGroup(group_id)]
        match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
        self.add_flow(datapath, 1, match, actions, table = table_ID)            
        
        intermidate = list(self.all_backup_path[src_sw,dst_sw].keys())
        print(intermidate)
        # for i in range(len(self.all_backup_path[src_sw,dst_sw])):
        for i in intermidate:
            if len(self.all_backup_path[src_sw,dst_sw][i]) == 1:
                self.GroupCounter[src_sw-1] += 1
                self.TableCounter[src_sw-1] += 1
                group_id = int(src_sw)*3+int(dst_sw)*2+i
                table_ID = int(src_sw)*3+int(dst_sw)*2+i                

                if i in path1: 
                    weight_1 = 0
                    weight_2 = 1
                else: 
                    weight_1 = 1
                    weight_2 = 0

                actions_1 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:01"), parser.OFPActionOutput(out_port1)]
                actions_2 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:02"), parser.OFPActionOutput(out_port2)]
                watch_group = ofproto_v1_3.OFPQ_ALL
                buckets = [
                    parser.OFPBucket(weight_1, out_port1, watch_group, actions_1),
                    parser.OFPBucket(weight_2, out_port2, watch_group, actions_2)]
                req = parser.OFPGroupMod(datapath, ofproto.OFPFC_ADD,ofproto.OFPGT_SELECT, group_id, buckets)
                datapath.send_msg(req)    
                
                actions = [parser.OFPActionGroup(group_id)]
                match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
                self.add_flow(datapath, 1, match, actions, table = table_ID)
        
        for i in range(len(self.all_pair_path[src_sw,dst_sw])):
            path1 = self.all_pair_path[src_sw,dst_sw][i]
            for curr in path1[1:-1]:
                datapath = self.DataPath[curr]
                prev = path1[path1.index(curr)-1]
                in_port = self.net[curr][prev]['port']
                self.priority[curr] += 1
                if i == 0:
                    match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
                else:
                    match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])                    
                if len(self.all_backup_path[src_sw,dst_sw][curr]) == 2:
                    self.group_id[curr] += 1 
                    self.GroupCounter[curr-1] += 1
                    path2 = self.all_backup_path[src_sw,dst_sw][curr][1]
                    next_sw1 = path1[path1.index(curr)+1]
                    next_sw2 = path2[path2.index(curr)+1]
                    out_port1 = self.net[curr][next_sw1]['port']
                    out_port2 = self.net[curr][next_sw2]['port']
                    actions1 = [parser.OFPActionOutput(out_port1)]
                    actions2 = [parser.OFPActionOutput(out_port2)]
                    weight = 0
                    buckets = [parser.OFPBucket(weight,out_port1,ofproto.OFPG_ANY,actions1),
                               parser.OFPBucket(weight,out_port2,ofproto.OFPG_ANY,actions2)]
                    req = parser.OFPGroupMod(datapath,ofproto.OFPGC_ADD,ofproto.OFPGT_FF,self.group_id[curr],buckets)                  
                    datapath.send_msg(req)
                    
                    actions = [parser.OFPActionGroup(self.group_id[curr])]
                    match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
                    self.add_flow(datapath, self.priority[curr], match, actions, table = 0)
                    
                else:         
                    self.TableCounter[curr-1] += 1
                    self.table_ID[curr] += 1 
                    next_sw = path1[path1.index(curr)+1]
                    out_port = self.net[curr][next_sw]['port']
                    actions = [parser.OFPActionOutput(out_port)]
                    # self.add_flow(datapath, 1, match, actions,table=self.table_ID[curr])
                    self.add_flow(datapath, self.priority[curr], match, actions,table=0)
      
    # For now: at the dst node one flow entry is added. The action 
    # is sending packet to the appropriate uotport 
        datapath = self.DataPath[dst_sw]
        self.TableCounter[dst_sw-1] += 1
        self.table_ID[dst_sw] += 1
        self.priority[dst_sw] += 1
        actions = [parser.OFPActionOutput(1)]
        match = parser.OFPMatch(eth_type=flow_info[0], ipv4_src=flow_info[1], ipv4_dst=flow_info[2])
        # self.add_flow(datapath, 1, match, actions,table=self.table_ID[dst_sw])
        self.add_flow(datapath, self.priority[dst_sw], match, actions,table=0)
    
        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,data=msg.data, in_port=in_port, actions=actions)
        datapath.send_msg(out)     
        return    

    @set_ev_cls(event.EventLinkDelete, MAIN_DISPATCHER)
    def link_failure_handler(self, ev):
        link = ev.link
        if "DOWN" not in str(link.src):
            return
        h1 = link.src.dpid
        h2 = link.dst.dpid
        print "Failure link:(",h1,",",h2,")"
        print(h1,h2)
        modify = False
        # for (src,dst) in self.all_pair_path:
        src = 1
        dst = 4
        for i in range(len(self.all_pair_path[src,dst])):
            path = copy.copy(self.all_pair_path[src,dst][i])
            path = path[1:]
            if (h1,h2) in list(zip(path, path[1:])):
                print('Too1')
                modify = True
                intermidate = h1
            if (h2,h1) in list(zip(path, path[1:])):
                print('Too2')
                modify = True
                intermidate = h2
            if modify:
                datapath = self.DataPath[src]
                parser = datapath.ofproto_parser
                ofproto = datapath.ofproto
                table_ID = int(src)*3+int(dst)*2+intermidate
                print("===================")
                inst=[parser.OFPInstructionGotoTable(table_ID)]
                match = parser.OFPMatch(in_port=1, eth_type=2048, ipv4_src=self.IPv4[src], ipv4_dst=self.IPv4[dst])
                mod = parser.OFPFlowMod(datapath=datapath, priority=200,
                            match=match, instructions=inst, command = ofproto.OFPFC_MODIFY, table_id=0)
                datapath.send_msg(mod)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if isinstance(ip_pkt, ipv4.ipv4):
            print("2222222222222222222222")
            if ip_pkt.src == '0.0.0.0':
                return 
            if len(pkt.get_protocols(ethernet.ethernet)):
                eth_type = pkt.get_protocols(ethernet.ethernet)[0].ethertype
                self.forwarding(msg, eth_type, ip_pkt.src, ip_pkt.dst)
