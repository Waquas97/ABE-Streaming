# For me to copy paste on server node terminal
wget -L https://raw.githubusercontent.com/Waquas97/ABE-Streaming/master/Small-Scale/getdashfiles_apache-server-run.sh
bash getdashfiles_apache-server-run.sh 

sudo tail -f /var/log/apache2/access.log | grep '10.10'
