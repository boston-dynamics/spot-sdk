#!/bin/bash -e

SCRIPT=${BASH_SOURCE[0]}
SCRIPT_PATH="$(dirname "$SCRIPT")"
cd $SCRIPT_PATH

FETCH_DIR=~/fetch

# Copy over the latest files
cp $FETCH_DIR/network_compute_server.py .
cp -r $FETCH_DIR/models-with-protos .

mkdir -p data
rm -rf data/*
# Dogtoy model
cp -r $FETCH_DIR/dogtoy/exported-models/dogtoy-model data/.
# and its label map
cp $FETCH_DIR/dogtoy/annotations/label_map.pbtxt data/dogtoy-model/.
# coco model (includes its label map)
cp -r $FETCH_DIR/dogtoy/pre-trained-models/ssd_resnet50_v1_fpn_640x640_coco17_tpu-8 data/.

# Build the image
sudo docker build -t fetch_detector:l4t -f Dockerfile.l4t .

# Exports the image, uses pigz
sudo docker save fetch_detector:l4t | pigz > fetch_detector_image.tar.gz

# Built the Spot Extension by taring all the files together
tar -cvzf fetch_detector.spx \
    fetch_detector_image.tar.gz \
    manifest.json \
    docker-compose.yml \
    data

# Cleanup intermediate image
rm fetch_detector_image.tar.gz