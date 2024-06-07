#!/bin/bash

#git pull
#chmod +x build.sh

docker image build --progress=plain --no-cache -t revenberg/codeprojectai:latest .

docker push revenberg/codeprojectai:latest

#docker run -i revenberg/codeprojectai:latest 

