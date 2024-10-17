#!/bin/bash
#traffic control on server to limit local network interface, this will limit speed to cache, clients,etc everyone.
sudo tc qdisc del dev $(ifconfig | grep -o 'enp[^:]*') root
sudo tc qdisc add dev $(ifconfig | grep -o 'enp[^:]*') handle 1: root htb default 11
sudo tc class add dev $(ifconfig | grep -o 'enp[^:]*') parent 1: classid 1:1 htb rate 200mbit
sudo tc class add dev $(ifconfig | grep -o 'enp[^:]*') parent 1:1 classid 1:11 htb rate 30mbit
sudo tc class add dev $(ifconfig | grep -o 'enp[^:]*') parent 1:1 classid 1:12 htb rate 30mbit
sudo tc class add dev $(ifconfig | grep -o 'enp[^:]*') parent 1:1 classid 1:13 htb rate 30mbit
sudo tc class add dev $(ifconfig | grep -o 'enp[^:]*') parent 1:1 classid 1:14 htb rate 30mbit
sudo tc class add dev $(ifconfig | grep -o 'enp[^:]*') parent 1:1 classid 1:15 htb rate 30mbit
sudo tc class add dev $(ifconfig | grep -o 'enp[^:]*') parent 1:1 classid 1:16 htb rate 50mbit


sudo tc filter add dev $(ifconfig | grep -o 'enp[^:]*') parent 1: protocol ip prio 1 u32 match ip src 10.10.1.1 match ip dst 10.10.1.2 flowid 1:16 
sudo tc filter add dev $(ifconfig | grep -o 'enp[^:]*') parent 1: protocol ip prio 1 u32 match ip src 10.10.1.2 match ip dst 10.10.1.3 flowid 1:15 
sudo tc filter add dev $(ifconfig | grep -o 'enp[^:]*') parent 1: protocol ip prio 1 u32 match ip src 10.10.1.2 match ip dst 10.10.1.4 flowid 1:14 
sudo tc filter add dev $(ifconfig | grep -o 'enp[^:]*') parent 1: protocol ip prio 1 u32 match ip src 10.10.1.2 match ip dst 10.10.1.5 flowid 1:13 
sudo tc filter add dev $(ifconfig | grep -o 'enp[^:]*') parent 1: protocol ip prio 1 u32 match ip src 10.10.1.2 match ip dst 10.10.1.6 flowid 1:12 

