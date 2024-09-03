#!/bin/bash
#traffic control on server to limit local netwrok interface, this will limit speed to cache, clients,etc everyone.
sudo tc qdisc del dev $(ifconfig | grep -o 'enp[^:]*') root
sudo tc qdisc add dev $(ifconfig | grep -o 'enp[^:]*') handle 1: root htb default 11
sudo tc class add dev $(ifconfig | grep -o 'enp[^:]*') parent 1:1 classid 1:11 htb rate 10mbit 


