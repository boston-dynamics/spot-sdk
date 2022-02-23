# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import json
import matplotlib.pyplot as plot
import numpy as np
from PIL import Image

from bosdyn.api.graph_nav import map_pb2


def extract_data(filename):
    """Load a json file and extract the desired data for each action in the file:
        (seed x, seed y, action name, battery percentage, image file name)
    """
    with open(filename, 'r') as f:
        json_data = json.load(f)
    out_data = []

    for action in json_data['actions']:
        if 'web-cam-service_video0' not in action['data']:
            # Only process actions that saved to the web-cam-service_video0 channel
            continue
        image_action = action['data']['web-cam-service_video0'][0]
        action_name = image_action['data_id']['action_id']['action_name']
        image_file = image_action['filename']
        odom_location = action['metadata']['basic-position-data'][0]['data']['seed_tform_body'][
            'position']
        battery = action['metadata']['battery'][0]['data']['battery_percentage']
        out_data.append((odom_location['x'], odom_location['y'], action_name, battery, image_file))
    return out_data


def plot_data(action_data, graph: map_pb2.Graph = None, image_size=2):
    """Display the captured images and battery data (and optionally the map edges)
    onto a plot of the "seed" frame."""
    plot.axis('equal')  # Keep the x and y axes at the same scale.
    if graph:
        # Plot all edges in the map
        wp_seed = anchor_positions(graph.anchoring.anchors)
        for edge in graph.edges:
            from_wp = wp_seed[edge.id.from_waypoint]
            to_wp = wp_seed[edge.id.to_waypoint]
            plot.plot([from_wp[0], to_wp[0]], [from_wp[1], to_wp[1]])

    # Plot the image, battery level and label for each action.
    for x, y, action_name, battery_percent, filename in action_data:
        image = Image.open(args.data_dir + '/' + filename)
        aspect = image.size[1] / image.size[0]  # keep the aspect ratio the same for the image.
        sx, sy = image_size, image_size * aspect
        plot.imshow(np.asarray(image), origin='upper', extent=(x - sx, x + sx, y - sy, y + sy),
                    zorder=2)
        # Plot the action name under the image.
        plot.text(x, y - sy, action_name, ha='center', va='top', zorder=3)
        # Draw a battery gauge to the right of the image.
        draw_battery((x + sx, y), scale=sy, fraction=battery_percent / 100)
    plot.show()


def anchor_positions(anchors):
    """Returns a dict of waypoint ids to seed positions for the given anchors."""
    return {
        a.id: (a.seed_tform_waypoint.position.x, a.seed_tform_waypoint.position.y) for a in anchors
    }


# Define a simple rectangle that can be easily scaled to draw a battery image.
BOX = np.array([[0, -1], [0, 1], [0.6, 1], [0.6, -1]])


def draw_battery(origin, scale, fraction):
    """Draw a simple battery gauge."""
    box_x, box_y = BOX[:, 0] * scale, (BOX[:, 1] * fraction - (1 - fraction)) * scale
    plot.fill(box_x + origin[0], box_y + origin[1], 'g', zorder=3)
    box_x, box_y = BOX[:, 0] * scale, BOX[:, 1] * scale
    plot.plot(box_x + origin[0], box_y + origin[1], 'k', zorder=3)


def load_graph(filename):
    """Read the map file into a protobuf"""
    graph = map_pb2.Graph()
    with open(filename, 'rb') as f:
        graph.ParseFromString(f.read())
    return graph


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', required=True, help='Directory of downloaded data')
    parser.add_argument('--graph', help='Graph file of the recorded map')
    parser.add_argument('--image-size', default=2, type=float,
                        help='Size of the recorded images to display on the map (meters)')
    args = parser.parse_args()

    action_data = extract_data(args.data_dir + '/metadata.json')
    graph = None
    if args.graph:
        graph = load_graph(args.graph)
    plot_data(action_data, graph, image_size=args.image_size)
