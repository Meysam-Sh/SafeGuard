#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel
from mininet.cli import CLI
import random
import itertools
import thread
import re
import time
from multiprocessing.dummy import Pool as ThreadPool 
from multiprocessing import Process

edges = [(1,2),(1,4),(1,6),(2,3),(3,5),(4,5),(4,7),(4,8),(5,6),(6,7),(6,8),(7,8),(7,9),(8,10),(9,10),(9,11),(9,12),(10,11),(10,12)]

nodes = [i for i in range(1,13)]

class CompleteGraphTopo(Topo):
    def build(self):
        prev_switch=''
        for node in range(12):
            switch = self.addSwitch('s%s'%(node+1))
            host = self.addHost('h%s'%(node+1))
            self.addLink( host, switch)
        for (sw1, sw2) in edges:
            prev_switch='s%s'%(sw1)
            switch='s%s'%(sw2)
            self.addLink(prev_switch,switch,cls=TCLink,bw=1000)
            # self.addLink(prev_switch,switch)

    def enable_BFD(self,net):
        """
        Bidirectional Forwarding Detection(BFD) is a network protocol used to detect link failure between two forwarding elements.
        """
        switches=net.switches
        for switch in switches:
            self.ofp_version(switch, ['OpenFlow13'])
            intfs=switch.nameToIntf.keys()[1:]
            for intf in intfs:
                switch.cmd('ovs-vsctl set interface "%s" bfd:enable=true'%intf)

    def ofp_version(self,switch, protocols):
        """
        sets openFlow version for each switch from mininet.
        """
        protocols_str = ','.join(protocols)
        command = 'ovs-vsctl set Bridge %s protocols=%s' % (switch, protocols)
        switch.cmd(command.split(' '))

def doIperf(src,dst):
    port,time,startLoad=5001,30,50
    dst.cmd('sudo pkill iperf')
    dst.cmd(('iperf -s -p %s -u -D')%(port))
    # dst.cmd(('iperf -s -i 1'))
    
    try:
        output=src.cmd(('iperf -c %s -p %s -u -t %d -b %sm')%(dst.IP(),port,time,startLoad))
        # output=src.cmd(('iperf -c %s -t %d -b %sM')%(dst.IP(),time,startLoad))
        print output
                       
    except:
        pass

def myiperf(self,line):
    net = self.mn
    thread =[]
    RandomFail = random.sample(edges, 1)
    a= 's%s'%(RandomFail[0][0])
    b= 's%s'%(RandomFail[0][1])
    net.configLinkStatus(a, b, 'down')   
    counter = 0
    start = time.time()
    print(start)
    for i in range(1,3):
    	src= 'h%s'%(random.randint(1,12))
    	dst= 'h%s'%(random.randint(1,12))
    	src=net.getNodeByName(src)
    	dst=net.getNodeByName(dst)
    	p=Process(target=doIperf,args=(src,dst))
    	thread.append(p)
    for t in thread:
    	t.start()
    for t in thread:
        counter += 1
        print("Flow number:", counter+1)
    	t.join()
    done = time.time()
    elapsed = done - start
    print(elapsed) 

def test(self,line):
    port,time,startLoad=5001,2,5
    # dst.cmd(('iperf -s -p %s -u -D')%(port))
    net = self.mn
    print('test')
    
    src= 'h%s'%(random.randint(1,12))
    dst= 'h%s'%(random.randint(1,12))
    src=net.getNodeByName(src)
    dst=net.getNodeByName(dst)
    print(src,dst)
    dst.cmd('sudo pkill iperf')
    dst.cmd(('iperf -s -p %s -u -D')%(port))
    output=src.cmd(('iperf -c %s -p %s -u -t %d -b %sm')%(dst.IP(),port,time,startLoad))
    print(output)
    
        
def PingPair(self,line):
    net = self.mn
    pairs=list(itertools.product(nodes, nodes))
    selected_pairs = random.sample(pairs, 60)
    # print(selected_pairs)
    counter = 0
    for (i,j) in selected_pairs:
        counter += 1
        print('Ping number: ',counter)
        print(i,j)
    	src= 'h%s'%(i)
    	dst= 'h%s'%(j)
    	src=net.getNodeByName(src)
    	dst=net.getNodeByName(dst)
        output = src.cmd( 'ping -c1', dst.IP() )
        print(output)
        print("*"*25)

def runner():
    topo = CompleteGraphTopo()
    c = RemoteController('c','127.0.0.1',6653)
    net = Mininet( topo=topo,controller=c,waitConnected=True,autoSetMacs=True,autoStaticArp=True)
    topo.enable_BFD(net)
    net.start()
    CLI.do_myiperf=myiperf
    CLI.do_test=test
    CLI.do_PingPair=PingPair
    CLI(net)
    net.stop()
if __name__ == '__main__':
    setLogLevel('info')
    runner()
