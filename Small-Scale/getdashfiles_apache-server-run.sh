#!/bin/bash

#get video segments
cd /var/www/html

# Base URL for the files
base_url="https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-Full/"

# Outer loop for the streams (0 to 4)
for stream in {0..4}; do
    wget -L "${base_url}init-stream${stream}.m4s"
    # Inner loop for the chunks (00001 to 00150)
    for chunk in $(seq -f "%05g" 1 150); do
        # Construct the file name
        file_name="chunk-stream${stream}-${chunk}.m4s.cpabe"
        
        # Full URL
        url="${base_url}${file_name}"
        
        # Download the file using wget
        wget -L "${url}"

    done
done
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-Full/BigBuckBunny-Full.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-Full/BigBuckBunny-Full-copy1.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-Full/BigBuckBunny-Full-copy2.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-Full/BigBuckBunny-Full-copy3.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-Full/BigBuckBunny-Full-copy4.mpd


cd

# Base URL for the files
base_url="https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-original/"

# Outer loop for the streams (0 to 4)
for stream in {0..4}; do
    wget -L "${base_url}init-stream${stream}.m4s"
    # Inner loop for the chunks (00001 to 00150)
    for chunk in $(seq -f "%05g" 1 150); do
        # Construct the file name
        file_name="chunk-stream${stream}-${chunk}.m4s"
        
        # Full URL
        url="${base_url}${file_name}"
        
        # Download the file using wget
        wget -L "${url}"

    done
done
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-original/original.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-original/original-copy1.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-original/original-copy2.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-original/original-copy3.mpd
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/BigBuckBunny-original/original-copy4.mpd

wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale/symlinkgen.sh
bash symlinkgen.sh
cd

sudo apt update
sudo apt --assume-yes install apache2
sudo apt --assume-yes install openssl
sudo a2enmod ssl
sudo a2ensite default-ssl
sudo ufw allow 'Apache Full'
sudo systemctl restart apache2

wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale/TC-server.sh
bash TC-server.sh
sudo apt-get --assume-yes install sysstat

sudo mv *.m4s /var/www/html/
sudo mv *.mpd /var/www/html/
