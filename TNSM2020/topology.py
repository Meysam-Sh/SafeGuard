from mininet.topo import Topo
from mininet.net import Mininet
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
import initilization
from multiprocessing.dummy import Pool as ThreadPool 
from multiprocessing import Process

topo = raw_input("Select a topology: B4, ATT, Dial Telecom, Cogent")
edge_list, n = initilization.Get_edges(topo)

# flows = initilization.TMGeneration(n)
Pri = [30,20,10]
flows = {}
pairs = []
for i in range(1,13):
  for j in range(1,13):
    for h in Pri:
      if j!=i:
        flows[i,j,h] = random.randint(20,100)
        pairs.append((i,j))
  

nodes = [i for i in range(1,17)]
class network(Topo):
    # buliding the topology 
    def build(self):
        for node in range(16):
            switch = self.addSwitch('s%s'%(node+1))
            host = self.addHost('h%s'%(node+1))
            self.addLink( host, switch)
        for (sw1, sw2) in edge_list:
            prev_switch='s%s'%(sw1)
            switch='s%s'%(sw2)
            self.addLink(prev_switch,switch,cls=TCLink,bw=1000)

# generate traffic between one source-detination pair
def doIperf(src,dst):
    port,time,startLoad=5001,30,50
    dst.cmd('sudo pkill iperf')
    dst.cmd(('iperf -s -p %s -u -D')%(port))
    
    try:
        output=src.cmd(('iperf -c %s -p %s -u -t %d -b %sm')%(dst.IP(),port,time,startLoad))
        print output                      
    except:
        pass

#creates multi-thread for simultaneous traffic generation
def MyTraffic(self,line):
    net = self.mn
    thread = [] 
    counter = 0
    start = time.time()
    print(start)
    for (i,j,h) in flows:
    	src = 'h%s'%(i)
    	dst = 'h%s'%(j)
    	src = net.getNodeByName(src)
    	dst = net.getNodeByName(dst)
    	p = Process(target=doIperf,args=(src,dst))
    	thread.append(p)
    for t in thread:
    	t.start()
    for t in thread:
        counter += 1
        print("Flow number:", counter+1)
    	t.join()
    RandomFail = random.sample(edges, 1)
    a = 's%s'%(RandomFail[0][0])
    b = 's%s'%(RandomFail[0][1])
    net.configLinkStatus(a, b, 'down')      
    done = time.time()
    elapsed = done - start
    print(elapsed) 

# ping between pairs 
def PingPair(self,line):
    net = self.mn
    counter = 0
    for (i,j) in pairs:
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
    topo = network()
    c = RemoteController('c','127.0.0.1',6653)
    net = Mininet( topo = topo,controller = c,waitConnected = True,autoSetMacs = True,autoStaticArp = True)
    #snet = Mininet( topo=topo,switch=UserSwitch,controller=c,autoSetMacs=True,autoStaticArp=True)
    net.start()
    CLI.do_MyTraffic = MyTraffic
    CLI.do_PingPair = PingPair
    CLI(net)
    net.stop()
if __name__ == '__main__':
    setLogLevel('info')
    runner()