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




edges = [(1,2),(1,4),(2,3),(3,4)]
class CompleteGraphTopo(Topo):
    def build(self):
               
        host1 = self.addHost("h1")
        host2 = self.addHost("h2")
        host3 = self.addHost("h3")
        switch1 = self.addSwitch("s1")
        switch2 = self.addSwitch("s2")
        switch3 = self.addSwitch("s3")
        self.addLink(switch1,host1, 1)
        self.addLink(switch2,host2, 1)
        self.addLink(switch3,host3, 1)
        self.addLink(switch1,switch2, 2, 2)
        self.addLink(switch2,switch3, 3, 2)
    
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
