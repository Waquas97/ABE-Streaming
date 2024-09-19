#!/bin/bash
sudo apt-get update
sudo apt-get --assume-yes install -y gcc g++ make libssl-dev tcl libexpat1-dev libpcre3-dev zlib1g-dev libcap-dev libxml2-dev libtool
sudo apt-get --assume-yes install cmake
sudo apt-get --assume-yes install pkg-config
sudo apt-get --assume-yes install libpcre2-8
sudo apt-get --assume-yes install libpcre2-dev
git clone https://git-wip-us.apache.org/repos/asf/trafficserver.git
cd trafficserver/
cmake -B build -DCMAKE_INSTALL_PREFIX=/opt/ts
cmake --build build
cmake --build build -t test
sudo cmake --install build
cd /opt/ts
sudo bin/traffic_server -R 1

cd

wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/records.yaml
sudo rm /opt/ts/etc/trafficserver/records.yaml
sudo mv records.yaml /opt/ts/etc/trafficserver/ 

echo 'map https://10.10.1.2:443 https://10.10.1.1:443' | sudo tee -a /opt/ts/etc/trafficserver/remap.config
echo 'map http://10.10.1.2:80 http://10.10.1.1:80' | sudo tee -a /opt/ts/etc/trafficserver/remap.config
sudo /opt/ts/bin/./trafficserver restart


wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/TC-cache.sh
bash TC-cache.sh
