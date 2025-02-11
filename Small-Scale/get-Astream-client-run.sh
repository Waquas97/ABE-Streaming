#!/bin/bash

#!/bin/bash

# Get CPABE toolkit install script and run
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale/setup-cpabetoolkit.sh
bash setup-cpabetoolkit.sh

# Get Astream DASH client
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale/https-client.tar.xz
tar -xf https-client.tar.xz
rm https-client.tar.xz

# Get Astream DASH client
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale/full-client.tar.xz
tar -xf full-client.tar.xz
rm full-client.tar.xz

