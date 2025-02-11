#!/bin/bash

#!/bin/bash

# Get CPABE toolkit install script and run
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale-360/setup-cpabetoolkit.sh
bash setup-cpabetoolkit.sh

# Get Astream DASH client
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale-360/https-client.tar.xz
tar -xf https-client.tar.xz
rm https-client.tar.xz

# Get Astream DASH client
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale-360/360-SE-client.tar.xz
tar -xf 360-SE-client.tar.xz
rm 360-SE-client.tar.xz

