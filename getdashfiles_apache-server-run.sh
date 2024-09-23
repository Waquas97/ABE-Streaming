#!/bin/bash

#get video segments
cd /var/www/html

# Base URL for the files
base_url="https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-allI/"

# Outer loop for the streams (0 to 4)
for stream in {0..4}; do
    wget -L "${base_url}init-stream${stream}.m4s"
    # Inner loop for the chunks (00001 to 00150)
    for chunk in $(seq -f "%05g" 1 150); do
        # Construct the file name
        file_name="enc_allI_chunk-stream${stream}-${chunk}.m4s"
        
        # Full URL
        url="${base_url}${file_name}"
        
        # Download the file using wget
        wget -L "${url}"

    done
done
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-allI/BigBuckBunny-allI.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-allI/BigBuckBunny-allI-copy1.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-allI/BigBuckBunny-allI-copy2.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-allI/BigBuckBunny-allI-copy3.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-allI/BigBuckBunny-allI-copy4.mpd

wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/symlinkgen.sh
bash symlinkgen.sh
cd

sudo apt update
sudo apt --assume-yes install apache2
sudo apt --assume-yes install openssl
sudo a2enmod ssl
sudo a2ensite default-ssl
sudo ufw allow 'Apache Full'
sudo systemctl restart apache2

wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/TC-server.sh
bash TC-server.sh

sudo mv *.m4s /var/www/html/
sudo mv *.mpd /var/www/html/
sudo apt-get --assume-yes install sysstat
