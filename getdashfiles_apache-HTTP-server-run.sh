wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/CPABE-encrypted-2quality.tar.xz
mkdir dash
tar -xf CPABE-encrypted-2quality.tar.xz -C dash
rm CPABE-encrypted-2quality.tar.xz
sudo apt update
sudo apt --assume-yes install apache2
sudo systemctl start apache2
sudo sudo mv dash/ /var/www/html

wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/TC-server.sh
bash TC-server.sh
