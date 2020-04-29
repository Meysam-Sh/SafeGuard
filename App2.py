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

time_to_collect=1000
class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.net=nx.DiGraph()
        self.all_pair_path={}
        #self.group_id = 0
        self.GroupTableNums = []
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        self.GroupTableNums.append(0)
        
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
        flow_info = (eth_type, ip_src, ip_dst)
        src_sw=int(ip_src.split('.')[3])
        dst_sw=int(ip_dst.split('.')[3])
        curr_sw=datapath.id
        
        # Three paths fro src to dst are generated
        paths = list(nx.all_simple_paths(self.net, src_sw, dst_sw))
        path1 = paths[0]
        path2 = paths[1]
        path3 = paths[2]
           
        if curr_sw==src_sw:     
            self.GroupTableNums[curr_sw-1] += 1
            group_id = self.GroupTableNums[curr_sw-1]
 
            next_sw1 = path1[path1.index(src_sw)+1]
            next_sw2 = path2[path2.index(src_sw)+1]
            next_sw3 = path3[path3.index(src_sw)+1]
            # One oup_port for each path
            out_port1 = self.net[src_sw][next_sw1]['port']
            out_port2 = self.net[src_sw][next_sw2]['port']
            out_port3 = self.net[src_sw][next_sw3]['port']
            
            # A SELECT group with three buckets. Each bucket tags the packet and then it points to a FFG
            actions_1 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:01"), parser.OFPActionGroup(group_id+1)]
            actions_2 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:02"), parser.OFPActionGroup(group_id+2)]
            actions_3 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:03"), parser.OFPActionGroup(group_id+3)]
            weight_1 = 33
            weight_2 = 33
            weight_3 = 34
            watch_group = ofproto_v1_3.OFPQ_ALL
            buckets = [
                parser.OFPBucket(weight_1, 1, watch_group, actions_1),
                parser.OFPBucket(weight_2, 1, watch_group, actions_2),
                parser.OFPBucket(weight_3, 1, watch_group, actions_3)]
            # Add SELECT group
            req = parser.OFPGroupMod(datapath, ofproto.OFPFC_ADD,ofproto.OFPGT_SELECT, group_id, buckets)
            datapath.send_msg(req)
                
            # FFG1: defult out_port is set to the eth of the first path. The backup out_port is set to the eth of the second path
            actions1 = [parser.OFPActionOutput(out_port1)]
            actions2 = [parser.OFPActionOutput(out_port2)]
            weight = 0
            buckets = [parser.OFPBucket(weight,out_port1,ofproto.OFPG_ANY,actions1),parser.OFPBucket(weight,out_port2,ofproto.OFPG_ANY,actions2)]
            req = parser.OFPGroupMod(datapath,ofproto.OFPGC_ADD,ofproto.OFPGT_FF,group_id+1,buckets)                  
            datapath.send_msg(req)
            
            # FFG2: defult out_port is set to the eth of the second path. The backup out_port is set to the eth of the third path
            actions1 = [parser.OFPActionOutput(out_port2)]
            actions2 = [parser.OFPActionOutput(out_port3)]
            weight = 0
            buckets = [parser.OFPBucket(weight,out_port2,ofproto.OFPG_ANY,actions1),parser.OFPBucket(weight,out_port3,ofproto.OFPG_ANY,actions2)]
            req = parser.OFPGroupMod(datapath,ofproto.OFPGC_ADD,ofproto.OFPGT_FF,group_id+2,buckets)                  
            datapath.send_msg(req)
            
            # FFG3: defult out_port is set to the eth of the third path. The backup out_port is set to the eth of the first path
            actions1 = [parser.OFPActionOutput(out_port3)]
            actions2 = [parser.OFPActionOutput(out_port1)]
            weight = 0
            buckets = [parser.OFPBucket(weight,out_port3,ofproto.OFPG_ANY,actions1),parser.OFPBucket(weight,out_port1,ofproto.OFPG_ANY,actions2)]
            req = parser.OFPGroupMod(datapath,ofproto.OFPGC_ADD,ofproto.OFPGT_FF,group_id+3,buckets)                  
            datapath.send_msg(req)
            
            actions = [parser.OFPActionGroup(group_id)]
            match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_dst=flow_info[2])
            self.add_flow(datapath, 1, match, actions,table=0)            
            
        elif curr_sw != dst_sw:
            # For now: at the intermidate node one flow entry is added. The match field is the tag of the packet, etc. The action 
            # is sending packet to the appropriate uotport 
            if curr_sw in path1:
                path = path1
                match = parser.OFPMatch(eth_src="00:00:00:00:00:01", in_port=in_port, eth_type=flow_info[0], ipv4_dst=flow_info[2])
            elif curr_sw in path2: 
                path = path2
                match = parser.OFPMatch(eth_src="00:00:00:00:00:02", in_port=in_port, eth_type=flow_info[0], ipv4_dst=flow_info[2])
            else: 
                path = path3
                match = parser.OFPMatch(eth_src="00:00:00:00:00:03", in_port=in_port, eth_type=flow_info[0], ipv4_dst=flow_info[2])
            next_sw = path[path.index(curr_sw)+1]
            out_port = self.net[curr_sw][next_sw]['port']
            actions = [parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, 1, match, actions,table=0)
        else:
            # For now: at the dst node one flow entry is added. The action is sending packet to the appropriate out_port
            actions = [parser.OFPActionOutput(1)]
            match = parser.OFPMatch(in_port=in_port, eth_type=flow_info[0], ipv4_dst=flow_info[2])
            self.add_flow(datapath, 1, match, actions,table=0)
        
        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, data=msg.data, in_port=in_port, actions=actions)
        datapath.send_msg(out)     
        return    

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        if msg.reason == ofproto.OFPPR_ADD:
            reason = 'ADD'
        elif msg.reason == ofproto.OFPPR_DELETE:
            reason = 'DELETE'
        elif msg.reason == ofproto.OFPPR_MODIFY:
            reason = 'MODIFY'
        else:
            reason = 'unknown'

        self.logger.debug('OFPPortStatus received: reason=%s desc=%s',
                          reason, msg.desc)
        
        # when a port1 of s1 is down, we modify the first group of s1. After this modification, the select group
        # of s1 has TWO buckets, etc. 
        if datapath.id == 1:
            actions_1 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:01"), parser.OFPActionGroup(2)]
            actions_2 = [parser.OFPActionSetField(eth_src="00:00:00:00:00:02"), parser.OFPActionGroup(3)]

            weight_1 = 50
            weight_2 = 50
            watch_group = ofproto_v1_3.OFPQ_ALL
            buckets = [
                parser.OFPBucket(weight_1, 1, watch_group, actions_1),
                parser.OFPBucket(weight_2, 1, watch_group, actions_2)]
            req = parser.OFPGroupMod(datapath, ofproto.OFPGC_MODIFY,ofproto.OFPGT_SELECT, 1, buckets)
            datapath.send_msg(req)

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
                #self.forwarding(msg, ip_pkt.src, ip_pkt.dst)
                self.forwarding(msg, eth_type, ip_pkt.src, ip_pkt.dst)
