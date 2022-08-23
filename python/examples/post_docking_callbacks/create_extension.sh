#!/bin/bash -e

SCRIPT=${BASH_SOURCE[0]}
SCRIPT_PATH="$(dirname "$SCRIPT")"
cd $SCRIPT_PATH

# Builds the image
docker build -t docking_callback:arm64 -f Dockerfile.arm64 .

# Exports the image, uses pigz
docker save docking_callback:arm64 | pigz > aws_docking_callback.tar.gz

tar -cvzf aws_docking_callback.spx \
    aws_docking_callback.tar.gz \
    manifest.json \
    docker-compose.yml \
    icon.png

# Cleanup intermediate image
rm aws_docking_callback.tar.gz
