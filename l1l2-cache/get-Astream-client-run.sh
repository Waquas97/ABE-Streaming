#!/bin/bash

# Get CPABE toolkit install script and run
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/setup-cpabetoolkit.sh
bash setup-cpabetoolkit.sh

# Get Astream DASH client
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/l1l2-cache/http-client.tar.xz
mkdir client
tar -xf Astream-DASH-Client-with-Decryption.tar.xz -C client
rm Astream-DASH-Client-with-Decryption.tar.xz

# run dash client, might need to remove this from here later
cd client
#python dash_client.py -m http://10.10.1.2/dash/BigBuckBunny-allI.mpd -p basic -d



