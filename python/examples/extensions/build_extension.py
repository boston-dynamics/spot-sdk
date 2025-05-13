# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Create a Spot Extension from an existing docker file."""

import io
import json
import re
import shutil
import subprocess
import tarfile
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import List

import pgzip

import docker

_IMAGES_MANIFEST_FIELD_NAME = "images"
_VERSION_FIELD_NAME = "version"
_EXTENSION_NAME_FIELD_ = "extension_name"
_DATE_FIELD_NAME = "date"
_INSTALLATION_TARGET_FIELD_NAME = "installation_target"


def build_image(client: docker.DockerClient, dockerfile_path: Path, tag: str, amd64: bool = False):
    """Builds the Docker image and saves it to a .tar.gz file.

    Args:
        client (docker.DockerClient): Docker client object.
        dockerfile_path (Path): Path to the Dockerfile.
        tag (str): Image tag.

    Returns:
        None
    """

    # Build the image
    print(f"Building image {tag} from {dockerfile_path}")
    if amd64:
        client.images.build(path=str(dockerfile_path.parent), tag=tag,
                            dockerfile=dockerfile_path.name, platform="linux/amd64")
    else:
        # Setting the platform seems to persist on future builds, so explicitly setting the
        # platform to ARM if "--amd64" is not specified ensures consistent builds.
        client.images.build(path=str(dockerfile_path.parent), tag=tag,
                            dockerfile=dockerfile_path.name, platform="linux/arm64")


def pull_extra_images(client: docker.DockerClient, image_tags: List[str]) -> bool:
    """Pulls Docker images specified in extra image tags if they aren't present.

    Args:
        client (docker.DockerClient): Docker client object.
        image_tags (List[str]): List of image tags.

    Returns:
        bool: True if successful, False otherwise.
    """

    for image_tag in image_tags:
        if client.images.list(filters={"reference": image_tag}):
            print(f"Already have docker image {image_tag}, locally, not pulling remote version")
            continue
        print(f"Pulling docker image {image_tag}")
        if not client.images.pull(image_tag):
            return False
    return True


def save_images(client: docker.DockerClient, image_tags: List[str], images_archive: Path) -> bool:
    """Saves a list of Docker images to a .tar.gz file.

    Args:
        client (docker.DockerClient): Docker client object.
        image_tags (List[str]): List of image tags.
        images_archive (Path): Path to the output archive.

    Returns:
        bool: True if successful, False otherwise.
    """

    print(f"Saving images {image_tags} to {images_archive}...")
    # Change suffix if the docker save is just an intermediate step
    if images_archive.suffix == ".tar":
        save_dest = images_archive
    elif images_archive.suffix == ".gz":
        save_dest = images_archive.with_suffix("")
    elif images_archive.suffix == ".tgz":
        save_dest = images_archive.with_suffix(".tar")
    else:
        print(f"Error: unknown suffix {images_archive.suffix} for images_archive")
        return False

    # The Docker Python SDK does not support saving multiple images, so we call the CLI
    # This will be replaced after the Docker Python SDK is updated to support saving multiple images
    cmd = ['docker', 'save'] + image_tags + ["-o", str(save_dest.absolute())]
    try:
        subprocess.run(cmd, capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError as exc:
        # Command returned a non-zero exit code
        print(f"Command '{' '.join(cmd)}' failed with exit code {exc.returncode}.")
        print("Error:")
        print(exc.stderr)

    # If the final archive needs to be gzipped (suffix was either .gz or .tgz), do that now
    if save_dest != images_archive:
        with pgzip.open(images_archive, 'wb') as gzfile, open(save_dest, "rb") as tarfile:
            shutil.copyfileobj(tarfile, gzfile)
    return True


def check_manifest(manifest_path: Path, images_archive_name: str):
    """Validates the contents of the manifest.json file.

    Args:
        manifest_path (Path): Path to the manifest.json file.
        images_archive_name (str): Name of the image archive.

    Returns:
        JSON string of updated and checked manifest data if successful, 
        False otherwise.
    """

    with open(manifest_path) as manifest_file:
        try:
            manifest_dict = json.load(manifest_file)
        except JSONDecodeError:
            print("Error: unparseable manifest.json")
            return False

    # Load docker images first, if they are included in the manifest file.
    docker_image_archives = manifest_dict[_IMAGES_MANIFEST_FIELD_NAME]
    if docker_image_archives != [images_archive_name]:
        print(
            f"Error: image archive(s) {docker_image_archives} specified in manifest.json does not match build image archive {[images_archive_name]}"
        )
        return False

    # Ensure that all required fields are present
    for field in [_VERSION_FIELD_NAME, _INSTALLATION_TARGET_FIELD_NAME, _DATE_FIELD_NAME]:
        got_error = check_is_field_present(manifest_dict, field)
        if (got_error):
            print(got_error)
            return False

    # Check that all fields are formatted properly
    format_error = check_is_formatted(manifest_dict)
    if (format_error):
        print(format_error)
        return False

    return json.dumps(manifest_dict)


def check_is_field_present(manifest_dict, field):
    if not manifest_dict.get(field, None):
        if field == _DATE_FIELD_NAME:
            # Add date if not provided
            manifest_dict[field] = datetime.now().isoformat()

        elif field == _INSTALLATION_TARGET_FIELD_NAME:
            # Default install target to Spot
            manifest_dict[field] = "spot"

        else:
            return (f"Error: manifest.json must include {field}")

    return False


def check_is_formatted(manifest_dict):
    # Check extension name format if included
    if manifest_dict.get(_EXTENSION_NAME_FIELD_, None):
        if not re.match(r'^[A-Za-z0-9_-]+$', manifest_dict[_EXTENSION_NAME_FIELD_]):
            return (
                "Error: extension_name in manifest.json can only contain alphanumeric characters, hyphens, and underscores"
            )

    # Check version format
    elif not re.match(r'^\d+\.\d+\.\d+$', manifest_dict[_VERSION_FIELD_NAME]):
        return (
            "Error: version string in manifest.json must be in format X.Y.Z where X, Y, and Z are integers"
        )

    # Check that date is parseable
    try:
        datetime.fromisoformat(manifest_dict[_DATE_FIELD_NAME])
    except:
        return ("Error: date in manifest.json not parseable, should be in ISO format")

    # Check that installation target is valid
    if manifest_dict[_INSTALLATION_TARGET_FIELD_NAME] not in ["orbit", "spot"]:
        return ("Error: installation_target in manifest.json must be [spot] or [orbit]")

    return False


def check_docker_compose_file(docker_compose_path: Path) -> bool:
    """Validate a docker compose file.

    Args:
        docker_compose_path (Path): Path to the docker compose file to validate

    Returns:
        bool: True if successful, False otherwise.
    """
    cmd = ['docker-compose', '-f', str(docker_compose_path), 'config', '-q']

    try:
        # let the output go straight to stderr/stdout
        subprocess.run(cmd, capture_output=False, check=True, text=True)
    except subprocess.CalledProcessError:
        print("Docker compose file validation failed.")
        return False
    except FileNotFoundError as error:
        if error.filename == 'docker-compose':
            print("Failed to run docker-compose to validate docker-compose.yml;")
            print("docker-compose appears to not be installed.")
            print()
            print("If docker-compose is not installed, please skip validation by")
            print("adding --skip-docker-compose-validation to the command arguments.")
        else:
            print("Docker compose file validation failed.")
        return False
    return True


def create_spx(file_directory: Path, images_archive: Path, icon: str, udev: Path, spx: Path,
               additional_files: List[str] = [], validate_docker_compose: bool = True):
    """Create a Spot Extension package by adding files to a .tar.gz archive.

    Args:
        file_directory (Path): Directory containing the manifest, docker compose, and icon assets
        images_archive (Path): Path to the Docker image archive
        icon (str): File name of icon
        spx (Path): Final output file
        additional_files (List[str]): List of additional files to include in tar

    Returns:
        True on success, False otherwise.
    """
    manifest = file_directory.joinpath('manifest.json')
    print(f"Manifest path: {manifest}")
    clean_manifest = check_manifest(manifest, images_archive.name)
    if not clean_manifest:
        return False

    tar_manifest = io.BytesIO()
    tar_manifest.write(clean_manifest.encode('utf-8'))
    tar_manifest.seek(0)
    tar_manifest_info = tarfile.TarInfo(name=manifest.name)
    tar_manifest_info.size = len(tar_manifest.getvalue())

    docker_compose = file_directory.joinpath('docker-compose.yml')
    if validate_docker_compose and not check_docker_compose_file(docker_compose):
        return False
    icon_path = file_directory.joinpath(icon)
    with tarfile.open(spx, 'w:gz') as tar:
        tar.addfile(tar_manifest_info, fileobj=tar_manifest)
        tar.add(images_archive, arcname=images_archive.name)
        tar.add(docker_compose, arcname=docker_compose.name)
        if icon_path.exists():
            tar.add(icon_path, arcname=icon_path.name)
        if additional_files:
            for filename in additional_files:
                file_path = file_directory.joinpath(filename)
                if file_path.exists():
                    tar.add(file_path, arcname=file_path.name)
                else:
                    print(f"Warn: No file {filename} in package directory {file_directory}.")
        if udev.exists():
            tar.add(udev, arcname=udev.name)
    print(f"Extension successfully built: {str(spx)}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser()

    # Required arguments
    parser.add_argument(
        '--dockerfile-paths', '-f', type=Path, nargs='*',
        help='Path to Dockerfile. Image will be build with this path as the context')
    parser.add_argument(
        '--build-image-tags', '-t', nargs='*', type=str, help=
        'Tags for docker images being built, should match arguments in --dockerfile-paths as well as the tags specified in the compose file'
    )
    parser.add_argument('--image-archive', '-i', type=Path, required=True,
                        help='Docker saved images file. Should match contents of manifest.json')
    parser.add_argument('--package-dir', '-m', type=Path, required=True,
                        help='Directory containing manifest.json, docker-compose.yml, and icon.')
    parser.add_argument('--spx', type=Path, required=True, help='Path to write the final spx to')

    # Optional arguments
    parser.add_argument(
        '--amd64', action='store_true', help=
        'If specified, the docker image is built for an amd64 architecture. Otherwise defaults to arm for running on the CORE I/O.'
    )
    parser.add_argument(
        '--extra-image-tags', nargs='*', type=str, help=
        'Additional image tags to save that do not need to be built (e.g. images pulled directly from Dockerhub)'
    )
    parser.add_argument('--icon', type=str, default='icon.png',
                        help='Path to the icon file, defaults to icon.png')
    parser.add_argument(
        '--additional-files', type=str, nargs="*",
        help='Path(s) to additional files in the package directory to include in the SPX.')
    parser.add_argument('--udev-rule', type=Path, default='udev_rule.rule',
                        help='Path to the udev rule file, defaults to udev_rule.rule')
    parser.add_argument(
        '--skip-docker-compose-validation', action='store_true',
        help='Disable validation of docker-compose.yml.  This is useful on systems '
        'in which docker-compose is not installed.')
    options = parser.parse_args()

    if (options.dockerfile_paths):
        assert len(options.dockerfile_paths) == len(
            options.build_image_tags
        ), "Error: --dockerfile-paths and --build-image-tags must be the same length!"

    # Initialize Docker daemon client
    client = docker.from_env()

    # Enable multi-arch build if building for ARM
    if not options.amd64:
        client.containers.run("multiarch/qemu-user-static", command=["--reset", "-p", "yes"],
                              privileged=True, remove=False)

    # Build images
    if (options.dockerfile_paths):
        for dockerfile_path, image_tag in zip(options.dockerfile_paths, options.build_image_tags):
            build_image(client, dockerfile_path, image_tag, options.amd64)

    # Save images
    if (options.dockerfile_paths):
        image_tags_to_save = options.build_image_tags
    else:
        image_tags_to_save = []

    if options.extra_image_tags:
        if not pull_extra_images(client, options.extra_image_tags):
            print("Error occurred when trying to pull images, exiting...")
            return -1
        image_tags_to_save += options.extra_image_tags

    if not save_images(client, image_tags_to_save, options.image_archive):
        print("Error occurred when trying to save images, exiting...")
        return -1

    if not create_spx(options.package_dir, options.image_archive, options.icon, options.udev_rule,
                      options.spx, options.additional_files,
                      not options.skip_docker_compose_validation):
        return 1

    return 0


if __name__ == '__main__':
    import sys

    result = main()
    sys.exit(result)
