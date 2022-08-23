#!/bin/bash -e

SCRIPT=${BASH_SOURCE[0]}
SCRIPT_PATH="$(dirname "$SCRIPT")"
cd $SCRIPT_PATH

# Builds the image
docker build -t fire_ext_detector:l4t -f Dockerfile.l4t .

# Exports the image, uses pigz
docker save fire_ext_detector:l4t | pigz > fire_ext_detector_image.tar.gz

tar -cvzf fire_extinguisher_detector.spx \
    fire_ext_detector_image.tar.gz \
    manifest.json \
    docker-compose.yml \
    icon.png

# Cleanup intermediate image
rm fire_ext_detector_image.tar.gz
