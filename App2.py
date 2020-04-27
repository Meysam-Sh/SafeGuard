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


time_to_collect=10
class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.net=nx.DiGraph()
        self.all_pair_path={}
        self.group_id = 0

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
    def add_flow(self, dp, p, match, actions, table=0):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=dp, priority=p, match=match, instructions=inst,table_id=table)
        dp.send_msg(mod)

    events = [event.EventSwitchEnter,
              event.EventSwitchLeave, event.EventPortAdd,
              event.EventLinkAdd]
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

    def forwarding(self, msg, ip_src, ip_dst):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        flow_info = (ip_src, ip_dst, in_port)
        src_sw=int(ip_src.split('.')[3])
        dst_sw=int(ip_dst.split('.')[3])
        curr_sw=datapath.id
        
        path1,path2 = list(nx.edge_disjoint_paths(self.net, src_sw, dst_sw))       
        if curr_sw==src_sw:     
            self.group_id += 1
            next_sw1 = path1[path1.index(src_sw)+1]
            next_sw2 = path2[path2.index(src_sw)+1]
            out_port1 = self.net[src_sw][next_sw1]['port']
            out_port2 = self.net[src_sw][next_sw2]['port']
            actions = [parser.OFPActionGroup(self.group_id)]
            actions_1 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:01"), parser.OFPActionOutput(out_port1)]
            actions_2 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:02"), parser.OFPActionOutput(out_port2)]
            weight_1 = 50
            weight_2 = 50
            watch_port = ofproto_v1_3.OFPP_ANY
            watch_group = ofproto_v1_3.OFPQ_ALL
            buckets = [
                parser.OFPBucket(weight_1, watch_port, watch_group, actions_1),
                parser.OFPBucket(weight_2, watch_port, watch_group, actions_2)]
            req = parser.OFPGroupMod(datapath, ofproto.OFPFC_ADD,ofproto.OFPGT_SELECT, self.group_id, buckets)
            datapath.send_msg(req)
            match = parser.OFPMatch(in_port=in_port, ipv4_dst=ip_dst)
            self.add_flow(datapath, 1, match, actions,table=0)            
            
        elif curr_sw != dst_sw:
            if curr_sw in path1:
                path = path1
                match = parser.OFPMatch(eth_src="00:00:00:00:00:01", in_port=in_port, ipv4_dst=ip_dst)
            else: 
                path = path2
                match = parser.OFPMatch(eth_src="00:00:00:00:00:02", in_port=in_port, ipv4_dst=ip_dst)
            next_sw = path[path.index(curr_sw)+1]
            out_port = self.net[curr_sw][next_sw]['port']
            actions = [parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, 1, match, actions,table=0)
        else:
            actions = [parser.OFPActionOutput(1)]
            match = parser.OFPMatch(in_port=in_port, ipv4_dst=ip_dst)
            self.add_flow(datapath, 1, match, actions,table=0)
        
        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, data=msg.data, in_port=in_port, actions=actions)
        datapath.send_msg(out)     
        return    

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
                self.forwarding(msg, ip_pkt.src, ip_pkt.dst)
