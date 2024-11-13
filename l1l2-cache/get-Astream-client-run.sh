#!/bin/bash

# Get CPABE toolkit install script and run
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/setup-cpabetoolkit.sh
bash setup-cpabetoolkit.sh

# Get Astream DASH client
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/l1l2-cache/http-client.tar.xz
tar -xf http-client.tar.xz 
rm http-client.tar.xz

# Get Astream DASH client
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/l1l2-cache/https-client.tax.xz
tar -xf https-client.tax.xz
rm https-client.tax.xz


