Instruction for runnig SafeGuard



#Setting up the enviromnment:
 
	--Download and install Mininet from http://mininet.org/download/
      
  --Install Ryu controler in Mininet usign "pip install Ryu" or from the source code in https://github.com/faucetsdn/ryu

	--Install CpqD sofware Switch from https://github.com/CPqD/ofsoftswitch13

# How to run SafeGurad:
	--Whenever you Run SafeGuard, you need to have two Mininet termnials open. 
	--Run the topology script in one terminal using "sudo python B4.py (or ATT.py)"
	--Then run SafeGuard controller app in the other one using "ryu-manager --observe-links SafeGuard.py"

# How to generate the link ltilzation results:
	--Create a list of random soure-destination pairs 
		**size of this list should be 60 for B4 and 200 for ATT network topology. 
	--Pass that list to "SelectedPiars" variable in both SafeGurd.py script and the topology script (B4.py or ATT.py)
	--Run the toplogy script and then run SafeGuard controller app and 
	--Wait for all switches to get connected. At that time you'll see 'all connected' oupput in the controller window. 
	--Run "My_Traffic()" command at the topology window. This will automatically fail a random link in the network. It will also generate UDP traffic using iperf beween the list of pairs. 
	--At the toppology terminal the number of flows will output.
	--At the controller the port statistics will be printed at each 30 second interval.
	--When all flows are finished an "elapsed time" value will ouptput in the topology Terminal. At this time, wait for the last port statistics ouput in the controller. When it apears, just stop the controler app runnig using Ctrl+Z.
	--To compute the link utilization on a link, you need to use this formula: (8*number of bytes transported by the origin port of a link)/(1000*elapsed_time)
	--The port numbers you need to check are recored in file ... 
	
