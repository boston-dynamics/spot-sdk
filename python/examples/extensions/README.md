<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Spot Extensions Build Script

The scripts in this directory can be used to build Spot Extensions.

- `generate_extension_data.py` creates a Spot Extension from an existing Docker image tarball.

- `build_extension.py` creates a Spot Extension from an existing Docker file or files as well as other supporting files.
  It uses the Docker API to build images and saves them to a compressed archive file.
  Then, it packages the archive file along with a manifest, Docker Compose file, and an icon into an SPX file.

## Install Dependencies

`generate_extension_data.py` does not have any additional dependencies.

Run the command below to install the necessary Python dependencies for `build_extension.py`:

```
python3 -m pip install -r requirements.txt
```

Docker must also be installed on the system.
See [Install Docker Engine](https://docs.docker.com/engine/install/) for more info.

## About generate_extension_data.py

The script generates a simple `manifest.json` and `docker-compose.yml` for a given image archive.
It should be used as a reference for how these files might be formatted.

### Arguments:

- `--image`: Required. Docker saved image file. File name stem should match the image tag.
- `--description`: Optional. Name of extension.

The format for running this command is:

```
python3 generate_extension_data.py \
    --image {/path/to/image.tar.gz} \
    [--description "Example description"]
```

For example, to build the artifacts for the AWS Post Docking Callback example,
run the following commands in this directory:

```
pushd ../post_docking_callbacks
docker build -t docking_callback:arm64 -f Dockerfile.arm64 .
popd
docker save docking_callback:arm64 | pigz > aws_docking_callback.tar.gz

python3 generate_extension_data.py \
    --image aws_docking_callback.tar.gz\
    --description "Post Docking S3 Upload Callback"
```

## About build_extension.py

The script builds the Docker image(s) specified in --dockerfile-paths with the corresponding tag(s) specified in `--build-image-tags`.
It saves all the Docker images specified in `--build-image-tags` and -`-extra-image-tags` to a compressed archive file specified in `--image-archive`.
It packages the archive file along with a manifest, Docker Compose file, and an icon into an SPX file specified in `--spx`.
The manifest file, compose file, and icon should either be located in the same directory as the first Dockerfile specified or `--package-dir` must be specified to indicate the directory.

Note: While the Spot Extension specification allows for multiple image archive tarballs in a single extension, this build script only supports one.

### Arguments:

- `--dockerfile-paths`: Required. Path to the Dockerfile(s). Image(s) will be built with this path as the context.
- `--build-image-tags`: Required. Tag(s) for Docker images being built. Should match arguments in `--dockerfile-paths` as well as the tags specified in the compose file.
- `--image-archive`: Required. Docker saved images file. Should match contents of manifest.json.
- `--package-dir`: Required. Directory containing manifest.json, docker-compose.yml, and icon.
- `--spx`: Required. Path to write the final SPX to.
- `--amd64`: Optional. Whether or not the target architecture is amd64. Otherwise defaults to an arm64 architecture for running on CORE I/O.
- `--extra-image-tags`: Optional. Additional image tags to save that do not need to be built (e.g. images pulled directly from Dockerhub).
- `--icon`: Optional. Path to the icon file. Default value is icon.png.
- `--additional-files`: Optional. List of any additional files in the package directory to be included in the resulting SPX, such as a `udev_rules` file.
- `--udev-rule`: Optional. Path to the udev rule. Default value is udev_rule.rule.

The format for running this command is:

```
python3 build_extension.py \
    [--amd64] \
    --dockerfile-paths {/path/to/image1.dockerfile} {/path/to/image2.dockerfile} \
    --build-image-tags {image1:tag} {image2:tag} \
    [--extra-image-tags {extra_image:tag}] \
    --image-archive {images_tarball.tar.gz} \
    --icon {icon.png} \
    --package-dir {/path/to/assets} \
    --spx {/path/to/output/extension.spx} \
    [--additional-files {file1.txt} {file2.jpg}]
```

For example, to build the Spot Extension for the AWS Post Dockering Callback example to run on ARM64,
follow the setup steps in the [README](../post_docking_callbacks/README.md),
then run the following command in this directory:

```
python3 build_extension.py \
    --dockerfile-paths ../post_docking_callbacks/Dockerfile.arm64 \
    --build-image-tags docking_callback:arm64 \
    --image-archive aws_docking_callback_arm64.tar.gz \
    --package-dir ../post_docking_callbacks \
    --spx ~/Downloads/aws_docking_callback.spx
```

## Troubleshooting

`build_extension.py` relies on using Docker commands, which are often restricted via OS-level permissions. The error messages if one does not have permissions to run Docker commands don't necessarily indicate this, and may instead show up as one or combination of the following errors:

```
- urllib3.exceptions.ProtocolError: ('Connection aborted.', PermissionError(13, 'Permission denied'))
- requests.exceptions.ConnectionError: ('Connection aborted.', PermissionError(13, 'Permission denied'))
- TypeError: HTTPConnection.request() got an unexpected keyword argument 'chunked'
- docker.errors.DockerException: Error while fetching server API version: ('Connection aborted.', PermissionError
- docker.errors.DockerException: Error while fetching server API version: HTTPConnection.request() got an unexpected keyword argument 'chunked'
```

If an error similar to one of the above shows up, there are a few approaches to successfully run Docker commands:

1. Add your user to the `docker` group using `sudo gpasswd -a $USER docker` or `usermod -a -G docker $USER`
2. Prepend the above `build_extension.py` command with `sudo`. Note: This does mean all parts of this command are run as a superuser, including the resulting extension being owned by root.
3. If you cannot run `sudo` commands or run as root on your device, ask your IT administrator how you can get permission to run Docker commands.
