#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel
from mininet.cli import CLI
import random
import thread
import re
from multiprocessing.dummy import Pool as ThreadPool 
from multiprocessing import Process



#edges = [(1,2),(1,4),(2,3),(3,4)]
edges = [(1,2),(1,4),(2,3),(3,4), (1,3)]
class CompleteGraphTopo(Topo):
    def build(self):
    
        prev_switch=''
        for node in range(4):
            switch = self.addSwitch('s%s'%(node+1))
            host = self.addHost('h%s'%(node+1))
            self.addLink( host, switch)
        for (sw1, sw2) in edges:
            prev_switch='s%s'%(sw1)
            switch='s%s'%(sw2)
            #self.addLink(prev_switch,switch,cls=TCLink,bw=10)
            self.addLink(prev_switch,switch)
    
    def ofp_version(self,switch, protocols):
 
        protocols_str = ','.join(protocols)
        command = 'ovs-vsctl set Bridge %s protocols=%s' % (switch, protocols)
        switch.cmd(command.split(' '))

    def ofp_version(self,switch, protocols):
        """
        sets openFlow version for each switch from mininet.
        """
        protocols_str = ','.join(protocols)
        command = 'ovs-vsctl set Bridge %s protocols=%s' % (switch, protocols)
        switch.cmd(command.split(' '))


def runner():
    topo = CompleteGraphTopo()
    c = RemoteController('c','127.0.0.1',6653)
    net = Mininet( topo=topo,controller=c,waitConnected=True,autoSetMacs=True,autoStaticArp=True)
    net.start()
    CLI(net)
    net.stop()
if __name__ == '__main__':
    setLogLevel('info')
    runner()
