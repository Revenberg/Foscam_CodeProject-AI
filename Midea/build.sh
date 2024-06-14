#!/bin/bash

#git pull
#chmod +x build.sh

docker image build --progress=plain --no-cache -t revenberg/midea:latest .

#docker push revenberg/codeprojectai:latest

docker run -i --network host revenberg/midea:latest
