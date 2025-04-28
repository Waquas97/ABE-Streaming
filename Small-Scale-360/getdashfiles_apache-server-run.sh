

#!/bin/bash


#get ABE MPDs and segments

base_url="https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Help360-SE-ABE-allI-allP-2sec-chunks/"

for i in {1..30}; do
    wget -L "${base_url}30MPDS-headtraces-symlinks-majorP-minorI/help360-SE-ABE-MajorP-MinorI-4tiles-${i}.mpd"
    wget -L "${base_url}30MPDS-headtraces-symlinks-allP/help360-SE-ABE-allP-4tiles-${i}.mpd"
done

for scheme in {"allI","allP"};do
   for tile in {1..9}; do
        # Outer loop for the streams (0 to 4)
        for stream in {0..3}; do
            wget -L "${base_url}init-stream${stream}.m4s"
            # Inner loop for the chunks (00001 to 00174)
            for chunk in $(seq -f "%05g" 1 147); do
                wget -L "${base_url}tile${tile}-enc_${scheme}_chunk-stream${stream}-${chunk}.m4s"
            
            done
        done
   done
done



#get HTPS MPDs and segments
base_url="https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Help360-HTTPS-2sec-chunks/"

for i in {1..30}; do
    wget -L "${base_url}30MPDS-headtraces-symlinks/help360-HTTPS-4tiles-${i}.mpd"
done

for tile in {1..9}; do
    # Outer loop for the streams (0 to 4)
    for stream in {0..3}; do
        wget -L "${base_url}init-stream${stream}.m4s"
        # Inner loop for the chunks (00001 to 00147)
        for chunk in $(seq -f "%05g" 1 147); do
            wget -L "${base_url}tile${tile}-chunk-stream${stream}-${chunk}.m4s"
        
        done
    done
done






wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale-360/symlinkgen.sh
bash symlinkgen.sh


sudo apt update
sudo apt --assume-yes install apache2
sudo apt --assume-yes install openssl
sudo a2enmod ssl
sudo a2ensite default-ssl
sudo ufw allow 'Apache Full'
sudo systemctl restart apache2

wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale-360/TC-server.sh
bash TC-server.sh
sudo apt-get --assume-yes install sysstat

sudo mv *.m4s /var/www/html/
sudo mv *.mpd /var/www/html/
