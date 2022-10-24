#!/bin/bash
docker build -t id-to-registres .
docker run --name id-registres --expose=4000 -p 4000:5000 -d id-to-registres:latest