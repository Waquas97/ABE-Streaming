#!/bin/bash
#traffic control on server to limit local netwrok interface, this will limit speed to cache, clients,etc everyone.

sudo tc qdisc add dev $(ifconfig | grep -o 'enp[^:]*') root tbf rate 100kbps burst 32kbit latency 50ms

