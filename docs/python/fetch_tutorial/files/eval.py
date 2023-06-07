# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import warnings
import cv2
import time
import tensorflow as tf
import os
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
import pathlib

def load_image_into_numpy_array(path):
    return np.array(Image.open(path))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--image-dir', help='Directory of images to use.')
    parser.add_argument('-m', '--model', help='Path to the model', required=True)
    parser.add_argument('-l', '--label-map', help='Path to the label_map.pbtxt file.', required=True)
    parser.add_argument('-o', '--output-dir', help='Directory to write labeled images.', required=True)

    args = parser.parse_args()

    detect_fn = tf.saved_model.load(args.model)
    category_index = label_map_util.create_category_index_from_labelmap(args.label_map, use_display_name=True)
    warnings.filterwarnings('ignore')   # Suppress Matplotlib warnings


    if not os.path.exists(args.image_dir):
        print('Error: image path does not exist: ' + args.image_dir)
        return

    total = len(os.listdir(args.image_dir))
    counter = 1
    for image_path in os.listdir(args.image_dir):

        path = pathlib.Path(image_path)
        if not path.suffix == '.jpg' and not path.suffix == '.png':
            continue

        full_path = os.path.join(args.image_dir, image_path)

        print('[{counter:d}/{total:d}] Running inference for {path:s}... '.format(counter=counter, total=total, path=full_path), end='')

        image = cv2.imread(full_path, -1)

        if len(image.shape) < 3:
            # Single channel image, convert to RGB.
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        input_tensor = tf.convert_to_tensor(image)
        input_tensor = input_tensor[tf.newaxis, ...]
        detections = detect_fn(input_tensor)

        # All outputs are batches of tensors.
        # Convert to numpy arrays, and take index [0] to remove the batch dimension.
        # We're only interested in the first num_detections.
        num_detections = int(detections.pop('num_detections'))
        detections = {key: value[0, :num_detections].numpy()
                       for key, value in detections.items()}
        detections['num_detections'] = num_detections

        # detection_classes should be ints.
        detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

        boxes = detections['detection_boxes']
        box = tuple(boxes[0].tolist())

        image_np_with_detections = image.copy()
        viz_utils.visualize_boxes_and_labels_on_image_array(
              image_np_with_detections,
              detections['detection_boxes'],
              detections['detection_classes'],
              detections['detection_scores'],
              category_index,
              use_normalized_coordinates=True,
              max_boxes_to_draw=200,
              min_score_thresh=.30,
              agnostic_mode=False)

        output_path = os.path.join(args.output_dir, image_path)

        Image.fromarray(image_np_with_detections).save(output_path)

        print(' Done')
        counter += 1
    plt.show()


if __name__ == "__main__":
    main()
