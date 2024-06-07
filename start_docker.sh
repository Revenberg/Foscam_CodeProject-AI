#/bin/bash
cd ~ 

sudo mkdir /var/docker

sudo mkdir /var/docker/mosquitto

sudo mkdir /var/docker/codeprojectai-server
sudo mkdir /var/docker/codeprojectai-server/opt
sudo mkdir /var/docker/codeprojectai-server/data
sudo mkdir /var/docker/codeprojectai-server/modules

sudo mkdir /var/docker/home-assistance/config

sudo mkdir /var/docker/nginx
sudo cp ~/nginx/* /var/docker/nginx/

sudo chown 1000:1000 -R /var/docker/

sudo cp ~/mosquitto/* /var/docker/mosquitto/
sudo chown 1881:1881 -R /var/docker/mosquitto/

docker-compose down
docker-compose up -d --force-recreate

echo "docker exec -it homeassistant bash"
echo "wget -O - https://get.hacs.xyz | bash -"

