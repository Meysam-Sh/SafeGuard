#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import UserSwitch
from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel
from mininet.cli import CLI
import random
import thread
import re
import itertools
from multiprocessing.dummy import Pool as ThreadPool 
from multiprocessing import Process

edges = [(1,2),(1,3),(1,7),(1,8),(2,7),(3,4),(3,7),(3,10),(3,16),(3,17),(3,18),(3,21),(3,22),(4,9),(4,10),(4,7),(5,6),(5,8),(6,8),(6,9),(6,10),(6,14),
          (6,15),(7,8),(9,10),(9,14),(10,14),(10,17),(10,23),(11,12),(11,14),(11,15),(12,13),(12,14),(12,15),(13,25),(13,14),(14,16),(14,17),
          (14,18),(14,23),(16,17),(16,18),(16,22),(17,18),(18,19),(18,20),(18,21),(18,22),(18,23),(19,22),(20,21),(22,23),(23,24),(23,25),(24,25)]          

selected_pairs = []

class ATT(Topo):
    # buliding the topology      
    def build(self):
        prev_switch=''
        for node in range(25):
            switch = self.addSwitch('s%s'%(node+1))
            host = self.addHost('h%s'%(node+1))
            self.addLink( host, switch)
        for (sw1, sw2) in edges:
            prev_switch='s%s'%(sw1)
            switch='s%s'%(sw2)
            self.addLink(prev_switch,switch,cls=TCLink,bw=1000)

# generate traffic between one source-detination pair
def doIperf(src,dst):
    port,time,startLoad=5001,10,25
    dst.cmd('sudo pkill iperf')
    dst.cmd(('iperf -s -p %s -u -D')%(port))   
    try:
        output=src.cmd(('iperf -c %s -p %s -u -t %d -b %sM')%(dst.IP(),port,time,startLoad))
        print output                
    except:
        pass

#creates multi-threads for simultaneous traffic generation
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

# ping between selected pairs 
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

# runner of the topology
def runner():
    topo = ATT()
    c = RemoteController('c','127.0.0.1',6653)
    net = Mininet( topo=topo,switch=UserSwitch,controller=c,autoSetMacs=True,autoStaticArp=True)
    net.start()
    CLI.do_MyTraffic=MyTraffic
    CLI.do_PingPair=PingPair
    CLI(net)
    net.stop()
if __name__ == '__main__':
    setLogLevel('info')
    runner()
