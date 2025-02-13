import numpy as np
import time
import subprocess
import sys
# import poisson
# import zipf
from datetime import datetime
import signal


####################################################### CHANGE CACHE SIZES ###########################################################
def change_cache_size(cache_id, cache_size):
    # Define the variable
   

    # Define the SSH command with the variable included
    ssh_command = (
        f"ssh waquas97@pc{cache_id}.cloudlab.umass.edu "
        f"'sudo /opt/ts/bin/./trafficserver stop && "
        f"sudo /opt/ts/bin/./traffic_server -Cclear && "
        f"sudo sed -i \"/^var\\/trafficserver/c\\var/trafficserver {str(cache_size)}M\" /opt/ts/etc/trafficserver/storage.config && "
        f"sudo /opt/ts/bin/./trafficserver restart'"
    )

    # Run the SSH command with subprocess
    try:
        process = subprocess.run(ssh_command, shell=True, check=True, capture_output=True, text=True)
        print("Output:", process.stdout)
        print("Errors:", process.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")

########################################################################################################################################

####################################################### CHANGE CLIENT LOG FOLDER NAMES ###########################################################
def change_client_logs(node_id, cache_size, typerun):
    ssh_command = (
        f"ssh waquas97@pc{node_id}.cloudlab.umass.edu "
        f"'rm 360-https-client1/log/*.m4s &&"
        f"mv 360-https-client1/log/ 360-https-client1/log-cache{cache_size}-{typerun} && "
        f"rm 360-https-client2/log/*.m4s &&"
        f"mv 360-https-client2/log/ 360-https-client3/log-cache{cache_size}-{typerun} && "
        f"rm 360-https-client3/log/*.m4s &&"
        f"mv 360-https-client3/log/ 360-https-client2/log-cache{cache_size}-{typerun} && "
        f"rm 360-https-client4/log/*.m4s &&"
        f"mv 360-https-client4/log/ 360-https-client4/log-cache{cache_size}-{typerun} && "
        f"rm 360-https-client5/log/*.m4s &&"
        f"mv 360-https-client5/log/ 360-https-client5/log-cache{cache_size}-{typerun} &&"
        f"rm 360-https-client6/log/*.m4s &&"
        f"mv 360-https-client6/log/ 360-https-client6/log-cache{cache_size}-{typerun} '"
    )

    # Run the SSH command with subprocess
    try:
        process = subprocess.run(ssh_command, shell=True, check=True, capture_output=True, text=True)
        print("Output:", process.stdout)
        print("Errors:", process.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")

########################################################################################################################################

#################################### terminate command ##################################################################################
def terminate_pidstat_tcpdump(node_id, whatproc):
    # Command to kill the pidstat process on the remote node
    kill_command = f"ssh waquas97@pc{node_id}.cloudlab.umass.edu 'sudo pkill {whatproc}'"
    subprocess.run(kill_command, shell=True, check=True)
###########################################################################################################################################

#################################### capinfos tcpdump and remove command ##################################################################################
def process_tcpdump(cache_id, cache_size,typerun):
    # Command to kill the pidstat process on the remote node
    proc_command = f"ssh waquas97@pc{cache_id}.cloudlab.umass.edu 'capinfos tcpdump-cache{cache_size}-{typerun}.pcap > tcpdump-cache{cache_size}-{typerun}.txt && rm tcpdump-cache{cache_size}-{typerun}.pcap'"
    subprocess.run(proc_command, shell=True, check=True)
###########################################################################################################################################

#################################### record hitmiss ##################################################################################
def hitmiss(cache_id, cache_size, typerun, when):
    # Command to kill the pidstat process on the remote node
    hitmisscommand = f"ssh waquas97@pc{cache_id}.cloudlab.umass.edu 'sudo /opt/ts/bin/./traffic_ctl metric match proxy.process.http.cache > hitmiss-cache{cache_size}-{typerun}-{when}.txt'"
    subprocess.run(hitmisscommand, shell=True, check=True)
###########################################################################################################################################



#################################################################### RUN STREAMING CLIENTS FUNCTION #########################################
# Function to run the program on a node and capture output
def run_program_on_node(node_ip, vid, clientnum, cache_size, typerun, clientpernode, lastnode_id):
    # Incorporate sleep time in the command
    command = (
        f"ssh -y waquas97@{node_ip} 'cd 360-https-client{clientnum} && "
        f"python dash_client.py -m https://10.10.1.2/{vid} -p basic -d '"
    )
    
    
    # Run the subprocess without waiting for it to finish
    if node_ip==f"pc{lastnode_id}.cloudlab.umass.edu" and clientnum==clientpernode: process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True) 
    else: process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Optionally, you can collect the output asynchronously if needed
    # stdout, stderr = process.communicate()
    
    # if stdout:
    #     print(f"Output for {node_ip}:\n{stdout}")
    
    # if stderr:
        #     print(f"Error for {node_ip}:\n{stderr}")
    
    # except Exception as e:
    #     print(f"Failed to run command on {node_ip}: {e}")
########################################################################################################################################################

# Parse node IDs from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python final-run_clients.py <node_id_1> <node_id_2> ...")
    sys.exit(1)

# Extract node IDs from arguments
node_ids = sys.argv[3:]
server_id=sys.argv[1]
cache_id= sys.argv[2]
lastnode_id=node_ids[-1]

# print (node_ids[-1])
# print(server_id,cache_id)
# Build the list of client nodes' IPs or hostnames based on node IDs
nodes = [f"pc{id}.cloudlab.umass.edu" for id in node_ids]


#experiment 30client, poisson lambda 20, zipf skew same 1.5 as ACMMSYS 
sleep_times=[22, 19, 18, 19, 15, 20, 22, 14, 20, 13, 18, 20, 19, 23, 21, 20, 18, 17, 17, 17, 23, 28, 24, 20, 16, 20, 14, 21, 14, 14]
selected_videos= ['help360-HTTPS-4tiles.mpd', 'help360-HTTPS-4tiles-copy2.mpd', 'help360-HTTPS-4tiles.mpd', 'help360-HTTPS-4tiles-copy4.mpd', 'help360-HTTPS-4tiles.mpd', 'help360-HTTPS-4tiles-copy4.mpd', 'help360-HTTPS-4tiles.mpd', 'help360-HTTPS-4tiles-copy3.mpd', 'help360-HTTPS-4tiles-copy2.mpd', 'help360-HTTPS-4tiles-copy1.mpd', 'help360-HTTPS-4tiles-copy1.mpd', 'help360-HTTPS-4tiles-copy1.mpd', 'help360-HTTPS-4tiles.mpd', 'help360-HTTPS-4tiles-copy4.mpd', 'help360-HTTPS-4tiles-copy4.mpd', 'help360-HTTPS-4tiles-copy4.mpd', 'help360-HTTPS-4tiles-copy4.mpd', 'help360-HTTPS-4tiles-copy3.mpd', 'help360-HTTPS-4tiles-copy2.mpd', 'help360-HTTPS-4tiles-copy1.mpd', 'help360-HTTPS-4tiles-copy1.mpd', 'help360-HTTPS-4tiles-copy4.mpd', 'help360-HTTPS-4tiles.mpd', 'help360-HTTPS-4tiles.mpd', 'help360-HTTPS-4tiles-copy4.mpd', 'help360-HTTPS-4tiles-copy2.mpd', 'help360-HTTPS-4tiles-copy4.mpd', 'help360-HTTPS-4tiles.mpd', 'help360-HTTPS-4tiles-copy2.mpd', 'help360-HTTPS-4tiles-copy2.mpd']


clientpernode=6
# FUNCTION change_client_logs NEEDS TO VARY TOO, NOW FIXED FOR 6.



#cache_sizes=[10,100,250,500,1000,1500,2000] #CACHES SIZES PAPER
cache_sizes=[0] # run differently ALSO PAPER SIZE

for cache_size in cache_sizes:
    #change_cache_size(cache_id, cache_size)
    print('new cachesize: '+str(cache_size)+' has been set and cache cleared and logs reset')
    #for typerun in ['warmup','actual']:
    for typerun in ['actual']:
        print('type is:'+typerun)








        #########################################################################  MAIN  ###########################################################################
        


        ############################## hitmiss before ###########################
        hitmiss(cache_id, cache_size,typerun,'before')
        ########################################################################


        ###################################################### Run PIDSTAT cache and server and tcmpdum cache ##################################
        pd_cache_command = (
                f"ssh waquas97@pc{cache_id}.cloudlab.umass.edu "
                f"'pidstat -h -u -p $(pgrep TS_MAIN | tr \"\\n\" \",\") 1 > cpu-cache-usage-cache{cache_size}-{typerun}.txt'"
            )
        pd_server_command = (
                f"ssh waquas97@pc{server_id}.cloudlab.umass.edu "
                f"'pidstat -h -u -p $(pgrep apache2 | tr \"\\n\" \",\") 1 > cpu-server-usage-cache{cache_size}-{typerun}.txt'"
            )
        tcpdump_cache_command = (
                f"ssh waquas97@pc{cache_id}.cloudlab.umass.edu "
                f"'sudo tcpdump -i $(ifconfig | grep -o \"enp[^:]*\") -s 0 -w tcpdump-cache{cache_size}-{typerun}.pcap host node0-link-1'"
            )

        pidstat_cache = subprocess.Popen(pd_cache_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        pidstat_server = subprocess.Popen(pd_server_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        tcpdump_cache = subprocess.Popen(tcpdump_cache_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


        ########################################################################################################################################


        ############################################################## RUN CLIENTS  ###############################################
        cl=0
        for clientnum in range(1,clientpernode+1):
            for n in range(0, len(nodes)):
                print(f"Sleeping for {sleep_times[cl]} seconds before running on node {node_ids[n]} and clientnum {clientnum}")
                time.sleep(sleep_times[cl])
                run_program_on_node(nodes[n], selected_videos[cl], clientnum, cache_size, typerun, clientpernode, lastnode_id)
                cl=cl+1
        ###########################################################################################################################


        ###################### STOP recodings ###########################
        time.sleep(5)
        terminate_pidstat_tcpdump(cache_id,'pidstat')
        terminate_pidstat_tcpdump(server_id,'pidstat')
        terminate_pidstat_tcpdump(cache_id,'tcpdump')
        #################################################################


        ################ Process tcpdump and remove #####################
        process_tcpdump(cache_id, cache_size,typerun)
        #################################################################


        ################## Change folder log names ######################
        for l in range(0, len(nodes)):
            change_client_logs(node_ids[l],cache_size,typerun)
        #################################################################


        ####################### hitmiss after ###########################
        hitmiss(cache_id, cache_size,typerun,'after')
        #################################################################



# python dash_client.py -m https://10.10.1.2/help360-HTTPS-4tiles.mpd -p basic -d