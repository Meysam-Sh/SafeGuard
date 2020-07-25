#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel
from mininet.node import UserSwitch
from mininet.cli import CLI
import random
from time import sleep
import itertools
import thread
import re
import time
from multiprocessing.dummy import Pool as ThreadPool 
from multiprocessing import Process

edges = [(1,2),(1,4),(1,6),(2,3),(3,5),(4,5),(4,7),(4,8),(5,6),(6,7),(6,8),(7,8),(7,9),(8,10),(9,10),(9,11),(9,12),(10,11),(10,12)]
selected_pairs = []

nodes = [i for i in range(1,12)]
class CompleteGraphTopo(Topo):
    def build(self):
        for node in range(16):
            switch = self.addSwitch('s%s'%(node+1))
            host = self.addHost('h%s'%(node+1))
            self.addLink( host, switch)
        for (sw1, sw2) in edges:
            prev_switch='s%s'%(sw1)
            switch='s%s'%(sw2)
            self.addLink(prev_switch,switch,cls=TCLink,bw=1000)

def doIperf(src,dst):
    port,time,startLoad=5001,30,50
    dst.cmd('sudo pkill iperf')
    dst.cmd(('iperf -s -p %s -u -D')%(port))
    
    try:
        output=src.cmd(('iperf -c %s -p %s -u -t %d -b %sm')%(dst.IP(),port,time,startLoad))
        print output                      
    except:
        pass

def MyTraffic(self,line):
    net = self.mn
    thread =[]
    RandomFail = random.sample(edges, 1)
    a= 's%s'%(RandomFail[0][0])
    b= 's%s'%(RandomFail[0][1])
    net.configLinkStatus(a, b, 'down')   
    counter = 0
    start = time.time()
    print(start)
    for (i,j) in selected_pairs:
    	src= 'h%s'%(i)
    	dst= 'h%s'%(j)
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

    
        
def PingPair(self,line):
    net = self.mn
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
    net = Mininet( topo=topo,switch=UserSwitch,controller=c,autoSetMacs=True,autoStaticArp=True)
    net.start()
    CLI.do_MyTraffic=myiperf
    CLI.do_PingPair=PingPair
    CLI(net)
    net.stop()
if __name__ == '__main__':
    setLogLevel('info')
    runner()
