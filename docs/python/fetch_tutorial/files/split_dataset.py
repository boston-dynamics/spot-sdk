# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Split our dataset into test and train sets."""

import argparse
import sys
import os
import pathlib
from shutil import copyfile
import random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--ratio', help='Test/train ratio.', default=0.9)
    parser.add_argument('-l', '--labels-dir', help='Path to the directory of labels', required=True)
    parser.add_argument('-o', '--output-dir', help='Path to the output where we create test and train folders', default='.')

    args = parser.parse_args()

    test_path = os.path.join(args.output_dir, 'test')
    train_path = os.path.join(args.output_dir, 'train')

    # Make test and train folders
    if not os.path.exists(test_path):
        os.makedirs(test_path)
        print('Created path: ' + test_path)

    if not os.path.exists(train_path):
        os.makedirs(train_path)
        print('Created path: ' + train_path)

    # Make sure the test and train directories are empty.
    if len(os.listdir(test_path)) > 0:
        print(test_path + ' directory is not empty, aborting.')
        return

    if len(os.listdir(train_path)) > 0:
        print(train_path + ' directory is not empty, aborting.')
        return

    output = []

    for label in os.listdir(args.labels_dir):
        path = pathlib.Path(label)
        if path.suffix == '.xml':
            output.append(label)

    train_count = 0
    test_count = 0
    for this_file in output:
        is_train = random.uniform(0, 1) < float(args.ratio)

        if is_train:
            train_count += 1
            out_path = train_path
        else:
            test_count += 1
            out_path = test_path

        copyfile(os.path.join(args.labels_dir, this_file), os.path.join(out_path, this_file))

    print('Copied ' + str(train_count) + ' XML files to ' + train_path)
    print('Copied ' + str(test_count) + ' XML files to ' + test_path)


if __name__ == "__main__":
    main()
