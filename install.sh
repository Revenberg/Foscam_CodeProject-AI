#/bin/bash
# 1 user
# 2 password
sudo apt update && sudo apt full-upgrade -y
sudo apt autoremove -y
sudo useradd -p "$(openssl passwd -6 $2)" $1
sudo usermod -G sudo $1
sudo groupadd docker
sudo usermod -a -G docker $1


./docker.sh $1
