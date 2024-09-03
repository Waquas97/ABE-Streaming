#!/bin/bash
sudo apt-get update
sudo apt-get --assume-yes install trafficserver
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/records.config
sudo rm -r /etc/trafficserver/records.config
sudo mv records.config /etc/trafficserver/ 
echo 'map http://10.10.1.2 http://10.10.1.1:80' | sudo tee -a /etc/trafficserver/remap.config
sudo systemctl restart trafficserver

wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/TC-cache.sh
bash TC-cache.sh
