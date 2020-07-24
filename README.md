# Instruction for running SafeGuard

This is a proactive failure recovery approach implementation.

## Setting up the environment:
 
	Download and install Mininet from http://mininet.org/download/
	Install Ryu controller in Mininet using "pip install Ryu" or from the source code in https://github.com/faucetsdn/ryu
	Install CpqD software Switch from https://github.com/CPqD/ofsoftswitch13
## How to run SafeGurad:
	Whenever you Run SafeGuard, you need to have two Mininet terminals open. 
	Run the topology script in one terminal using "sudo python B4.py (or ATT.py)"
	Then run SafeGuard controller app in the other one using "ryu-manager --observe-links SafeGuard.py"

## How to generate the link utilization results:
	1) Create a list of random source-destination pairs 
		*size of this list should be 60 for B4 and 200 for ATT network topology. 
	2) Pass that list to "selected_piars" variable in both SafeGurd.py script and the topology script (B4.py or ATT.py)
	3) Run the topology script and then run SafeGuard controller app and 
	4) Wait for all switches to get connected. At that time, you'll see 'all connected' output in the controller window. 
	5) Run "My_Traffic()" command at the topology window. This will automatically fail a random link in the network. It will also generate UDP traffic using iperf between the list of pairs. 
	6) At the topology terminal the number of flows will output.
	7) At the controller the port statistics will be printed at each 30 second interval.
	8) When all flows are finished an "elapsed time" value will output in the topology Terminal. At this time, wait for the last port statistics output in the controller. When it appears, just stop the controller app running using Ctrl+Z.
	9) To compute the link utilization on a link, you need to use this formula: (8*number of bytes transported by the origin port of a link)/(1000*elapsed_time)
	The port numbers you need to check are recorded in file ... 

# Contribute
...
# Acknowledgments
...
# Contact
...

	
