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
from collections import defaultdict


time_to_collect=10
class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.net=nx.DiGraph()

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

    def forwarding(self, msg, eth_type, ip_src, ip_dst):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        flow_info = (eth_type, ip_src, ip_dst, in_port)
        src_sw=int(ip_src.split('.')[3])
        dst_sw=int(ip_dst.split('.')[3])
        curr_sw=datapath.id
        path = list(nx.shortest_path(self.net, src_sw, dst_sw))
           
        if curr_sw != dst_sw:
            next_sw = path[path.index(curr_sw)+1]
            out_port = self.net[curr_sw][next_sw]['port']
            actions = [parser.OFPActionOutput(out_port)]
            if curr_sw == src_sw:
                actions.append(parser.OFPActionSetField(eth_src="00:00:00:00:00:00"))
                match = parser.OFPMatch(in_port=in_port, ipv4_dst=flow_info[2])
            else:
                match = parser.OFPMatch(eth_src="00:00:00:00:00:00", in_port=in_port, ipv4_dst=flow_info[2])
        else:
            actions = [parser.OFPActionOutput(1)]
            match = parser.OFPMatch(in_port=in_port, ipv4_dst=flow_info[2])
        
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
                self.forwarding(msg, eth_type, ip_pkt.src, ip_pkt.dst)
