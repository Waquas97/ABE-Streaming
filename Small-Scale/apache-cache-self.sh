# For me to copy paste on cache node terminal
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale/apache-reverse-proxy-cache-SETUP.sh
bash apache-reverse-proxy-cache-SETUP.sh


# Need to do manually
sudo apt-get --assume-yes install wireshark-common


#For ssl cert and key have to do manually:
cd /opt/ts/etc
sudo mkdir ssl
cd ssl
sudo openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout server.key -out server.crt
sudo chmod 777 *


# TCP dump for capturing all pkts going in and out of node1 (server) fr
sudo tcpdump -i $(ifconfig | grep -o 'enp[^:]*') -s 0 -w traffic.pcap host node0-link-1
#clear tcpdump files
sudo rm *pcap
# get total volume from tcpdump file
capinfos traffic.pcap
     



# RESTART DOES NOT CLEAR THE CACHE, IT DOES CLEAR THE LOGS for hit miss and unconfirmed midgress.

#changing size of cache and restarting will clear cache as well

# Set Disc cache size
# size 100
sudo sed -i '/^var\/trafficserver/c\var/trafficserver 100M' /opt/ts/etc/trafficserver/storage.config
sudo /opt/ts/bin/./trafficserver restart
#size 250MB
sudo sed -i '/^var\/trafficserver/c\var/trafficserver 250M' /opt/ts/etc/trafficserver/storage.config
sudo /opt/ts/bin/./trafficserver restart
#size 500MB
sudo sed -i '/^var\/trafficserver/c\var/trafficserver 500M' /opt/ts/etc/trafficserver/storage.config
sudo /opt/ts/bin/./trafficserver restart

#  Ram cache is already set 0 in records.yaml






