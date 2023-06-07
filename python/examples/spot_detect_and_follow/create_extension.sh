#!/bin/bash -e

SCRIPT=${BASH_SOURCE[0]}
SCRIPT_PATH="$(dirname "$SCRIPT")"
cd $SCRIPT_PATH

# Builds the image
docker build -t spot_detect_and_follow -f Dockerfile.l4t .

# Exports the image, uses pigz
docker save spot_detect_and_follow | pigz > spot_detect_and_follow.tar.gz

tar -cvzf spot_detect_and_follow.spx \
    spot_detect_and_follow.tar.gz \
    manifest.json \
    docker-compose.yml

# Cleanup intermediate image
rm spot_detect_and_follow.tar.gz
