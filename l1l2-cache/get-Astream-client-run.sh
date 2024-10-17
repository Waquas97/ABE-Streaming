#!/bin/bash

# Get CPABE toolkit install script and run
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/setup-cpabetoolkit.sh
bash setup-cpabetoolkit.sh

# Get Astream DASH client
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Astream-DASH-Client-with-Decryption.tar.xz
mkdir client
tar -xf Astream-DASH-Client-with-Decryption.tar.xz -C client
rm Astream-DASH-Client-with-Decryption.tar.xz

wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Original-Astream-DASH-NoCertCheck-MinorBugFix.tar.xz
mkdir https-client
tar -xf Original-Astream-DASH-NoCertCheck-MinorBugFix.tar.xz -C https-client
rm Original-Astream-DASH-NoCertCheck-MinorBugFix.tar.xz
mv https-client/client/* https-client/
rm -r https-client/client

# run dash client, might need to remove this from here later
# cd client
#python dash_client.py -m http://10.10.1.2/dash/BigBuckBunny-allI.mpd -p basic -d



