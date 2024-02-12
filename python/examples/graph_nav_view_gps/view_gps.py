# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import math
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np

from bosdyn.api import geometry_pb2
from bosdyn.api.gps.gps_pb2 import LLH
from bosdyn.api.graph_nav import map_pb2
from bosdyn.client.frame_helpers import *
from bosdyn.client.math_helpers import *

"""
This example shows how to display GPS data in a graph nav map.

"""

EARTH_RADIUS = 6378137.0  # Meters.
EARTH_FLATTENING = 1 / 298.257223563  # Bessel ellipsoid.


def ecef_to_llh(x: float, y: float, z: float, radians: bool = False) -> LLH:
    """Converts an earth-centered-earth-fixed (ECEF) frame to Latitude/Longitude/Height (LLH)."""
    e2 = 2 * EARTH_FLATTENING - EARTH_FLATTENING**2  # = Eccentricity^2
    b = math.sqrt((EARTH_RADIUS**2) * (1 - e2))
    ep = math.sqrt(((EARTH_RADIUS**2) - (b**2)) / (b**2))
    p = math.sqrt((x**2) + (y**2))
    th = math.atan2(EARTH_RADIUS * z, b * p)
    lon = math.atan2(y, x)
    lat = math.atan2((z + (ep**2) * b * (math.sin(th)**3)),
                     (p - e2 * EARTH_RADIUS * (math.cos(th)**3)))
    N = EARTH_RADIUS / math.sqrt(1 - e2 * (math.sin(lat)**2))
    height = p / math.cos(lat) - N
    # return lon in range [0,2*pi).
    lon = lon % (2 * math.pi)
    # Near poles there is some numerical instability.  Account for it:
    if x**2 + y**2 < 1:
        height = abs(z) - b
    if not radians:
        lat = math.degrees(lat)
        lon = math.degrees(lon)

    llh = LLH()
    llh.latitude = lat
    llh.longitude = lon
    llh.height = height
    return llh


def load_map(path: str) -> tuple:
    """
    Load a map from the given file path.
    :param path: Path to the root directory of the map.
    :return: the waypoints, and waypoint snapshots.
    """
    with open(os.path.join(path, 'graph'), 'rb') as graph_file:
        # Load the graph file and deserialize it. The graph file is a protobuf containing only the waypoints and the
        # edges between them.
        data = graph_file.read()
        current_graph = map_pb2.Graph()
        current_graph.ParseFromString(data)

        # Set up maps from waypoint ID to waypoints and snapshot ID to snapshots.
        current_waypoints = {}
        current_waypoint_snapshots = {}

        # For each waypoint, load any snapshot associated with it.
        for waypoint in current_graph.waypoints:
            current_waypoints[waypoint.id] = waypoint

            if len(waypoint.snapshot_id) == 0:
                continue
            # Load the snapshot. Note that snapshots contain all of the raw data in a waypoint and may be large.
            file_name = os.path.join(path, 'waypoint_snapshots', waypoint.snapshot_id)
            if not os.path.exists(file_name):
                continue
            with open(file_name, 'rb') as snapshot_file:
                waypoint_snapshot = map_pb2.WaypointSnapshot()
                try:
                    waypoint_snapshot.ParseFromString(snapshot_file.read())
                    current_waypoint_snapshots[waypoint_snapshot.id] = waypoint_snapshot
                except Exception as e:
                    print(f"{e}: {file_name}")
        print(
            f'Loaded graph with {len(current_graph.waypoints)} waypoints, {len(current_graph.edges)} edges'
        )
        return (current_waypoints, current_waypoint_snapshots)


def timestamp_to_seconds(timestamp: any) -> float:
    """
    Converts a google.protobuf.Timestamp message to a number of seconds since epoch.
    """
    return timestamp.seconds + 1.0e-9 * timestamp.nanos


def get_raw_gps_data(current_waypoint_snapshots: dict) -> list:
    """
    Returns a list of latitude/longitude coordinates in the waypoint snapshots.
    Waypoint snapshots may contain a world object called "gps_properties" that has raw measurements of latitude
    and longitude at the time of recording of that waypoint snapshot.
    This function returns a list of tuples where each tuple is a (latitude, longitude) pair, one for each waypoint snapshot.
    The latitude/longitude coordinates will be sorted by time.
    """
    raw_latitude_longitude = []
    sorted_waypoint_snapshots = list(current_waypoint_snapshots.values())
    # Sort waypoint snapshots by time.
    sorted_waypoint_snapshots = sorted(
        sorted_waypoint_snapshots,
        key=lambda a: timestamp_to_seconds(a.robot_state.kinematic_state.acquisition_timestamp))
    # Snapshots store raw GPS data in the field called "gps_properties" in the world objects.
    for snapshot in sorted_waypoint_snapshots:
        for world_object in snapshot.objects:
            if world_object.HasField('gps_properties'):
                # This is a "latitude longitude height" message.
                llh = world_object.gps_properties.registration.robot_body_location
                raw_latitude_longitude.append([llh.latitude, llh.longitude])

    return raw_latitude_longitude


def get_annotated_gps_data(current_waypoints: dict) -> list:
    """
    Returns a list of waypoint coordinates from waypoint annotations. The annotated GPS data
    may have come from an optimization process, or may have been manually annotated by an editor.
    This function returns a list of tuples where each tuple is a (latitude, longitude) pair, one for each waypoint.
    The latitude/longitude coordinates will be sorted by time.
    """
    latitude_longitude = []
    sorted_waypoints = list(current_waypoints.values())
    # Sort waypoints by time.
    sorted_waypoints = sorted(sorted_waypoints,
                              key=lambda a: timestamp_to_seconds(a.annotations.creation_time))
    for waypoint in sorted_waypoints:
        # When the waypoint annotations have gps_settings set, there is annotated GPS data in the map.
        if waypoint.annotations.gps_settings.state == map_pb2.ANNOTATION_STATE_SET:
            ecef_T_waypoint = waypoint.annotations.gps_settings.ecef_tform_waypoint
            llh_T_waypoint = ecef_to_llh(ecef_T_waypoint.position.x, ecef_T_waypoint.position.y,
                                         ecef_T_waypoint.position.z)
            latitude_longitude.append([llh_T_waypoint.latitude, llh_T_waypoint.longitude])

    return latitude_longitude


def plot_gps_web_document(raw_gps_data_array: np.array, annotated_gps_data_array: np.array):
    raw_gps_center = numpy.mean(raw_gps_data_array, axis=0)
    print(f'Plotting centered at latitude/longitude {raw_gps_center}')

    # Create a raw HTML document with an Open Street Map inside. This uses the leaflet.js library, which
    # draws primitives over an Open Street Maps tile.
    html_doc = f"""<html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
        crossorigin=""/>
    </head>
        <!-- import leaflet library -->
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
            crossorigin="">
        </script>
    <body>
        <div id="map" style="height: 1024px">
        </div>The map should be displayed above.</body>
    <script>
        // Javascript to create a map centered on the coordinates of our map.
        var map = L.map('map').setView([{raw_gps_center[0]}, {raw_gps_center[1]}], 13);""" + """
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        """

    def draw_polyline(latlongs: list, variable_name: str, color: tuple, doc: str) -> str:
        """Append a polyline with the given variable name to the html document."""
        doc += f'\nvar {variable_name} = ['
        for row in range(0, latlongs.shape[0]):
            doc += f"[{latlongs[row, 0]}, {latlongs[row, 1]}]"
            if row < latlongs.shape[0] - 1:
                doc += ','
        doc += '];'
        # Add the polyline to the map, and fit the map to it.
        doc += f'\nvar polyline_{variable_name} = L.polyline({variable_name}, {{color: \'{color}\'}}).addTo(map);'
        doc += f'\nmap.fitBounds(polyline_{variable_name}.getBounds());'
        return doc

    # Draw the raw GPS data.
    html_doc = draw_polyline(raw_gps_data_array, 'raw_gps', 'blue', html_doc)
    # Draw the annotated gps data.
    html_doc = draw_polyline(annotated_gps_data_array, 'annotated_gps', 'red', html_doc)

    # HTML/javascript footer.
    html_doc += """
    </script>
</html>
    """

    # Create a simple web server to display the data on Open Street Maps.
    class MapDisplayServer(BaseHTTPRequestHandler):

        def do_GET(self):
            """Serves the HTML when the web browser navigates to the page."""
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(html_doc, "utf-8"))

    HOST_NAME = "localhost"  # Server is hosted on the local machine.
    SERVER_PORT = 8080  # Default port to host the server at.
    web_server = HTTPServer((HOST_NAME, SERVER_PORT), MapDisplayServer)
    print(f'Server started at http://{HOST_NAME}:{SERVER_PORT}. Open a web browser to see it.')

    try:
        # Block until we are done with the server.
        web_server.serve_forever()
    except KeyboardInterrupt:
        # CTRL+C to stop the server.
        pass

    web_server.server_close()
    print("Server stopped.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=str, help='Map to draw. The map should have GPS data.')
    options = parser.parse_args()
    # Load the map from the given directory.
    (current_waypoints, current_waypoint_snapshots) = load_map(options.path)

    # Determine if there is any GPS data to display.
    raw_data = get_raw_gps_data(current_waypoint_snapshots)
    annotated_data = get_annotated_gps_data(current_waypoints)
    print(
        f'{len(raw_data)}/{len(current_waypoint_snapshots.values())} waypoint snapshot(s) have raw GPS data. {len(annotated_data)}/{len(current_waypoints.values())} waypoint(s) have annotated data'
    )

    # If there is no GPS data to display, early exit.
    if len(raw_data) == 0 and len(annotated_data) == 0:
        print('The map does not have GPS data.')
        return

    # Now we will draw the GPS data. This opens a web server to an Open Street Maps page. This blocks until
    # KeyboardInterrupt.
    plot_gps_web_document(np.array(raw_data), np.array(annotated_data))


if __name__ == '__main__':
    main()
