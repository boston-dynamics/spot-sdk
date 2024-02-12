# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Create a Spot Extension from an existing docker file."""

import tarfile
from pathlib import Path

json_template = '''
{{
  "description": "{description}",
  "version": "{version}",
  "images" : ["{image}"]
}}
'''

compose_template = '''
services:
  app:
    image: "{image}:latest"
    network_mode: "host"
    volumes:
      - "/opt/payload_credentials:/creds"
    restart: unless-stopped
'''


def create_artifacts(description: str, image: Path, version: str):
    image_stem = image.stem
    manifest = json_template.format(description=description, version=version, image=image)
    docker_compose = compose_template.format(image=image_stem)
    with open('manifest.json', 'w') as f:
        f.write(manifest)
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', '-i', type=Path,
                        help='Docker saved image file.  File name stem should match the image tag.')
    parser.add_argument('--description', '-d', type=str, help='Name of extension', required=False,
                        default='')
    parser.add_argument('--version', '-v', type=str,
                        help='Version number of extension, e.g. 23.43.12', required=True)
    args = parser.parse_args()

    assert args.image.exists()
    create_artifacts(args.description, args.image, args.version)


if __name__ == '__main__':
    main()
