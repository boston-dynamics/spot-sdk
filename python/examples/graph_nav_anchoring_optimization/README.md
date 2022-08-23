<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Graph Nav Anchoring Optimization Example

This example demonstrates how to use the map processing service to align a graph nav map to a blueprint. This assumes that you have a running robot connected to the client.

## Setup Dependencies

These examples require the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

The example also requires matplotlib. Depending on your system you may need to set up a [backend](https://matplotlib.org/stable/tutorials/introductory/usage.html#what-is-a-backend) for it to display properly. One possible backend to use is Qt5: `python3 -m pip install pyqt5` and set the environment variable `MPLBACKEND` to `qt5agg`.

## Running the Example

Run the example using:

```
python3 -m graph_nav_anchoring_optimization ROBOT_IP
```

This will load the example map from the data directory, upload it to your robot, and then align it to the provided blueprint.

When the example has finished running, it will display an image. The image shows a blueprint. Drawn on top of the blueprint there will be a series of red lines and a series of green lines.

The red lines are the anchoring of the map before optimization (this is the default anchoring). The green lines are the anchoring of the map after optimization. The green lines should line up with the hallway in the middle of the blueprint.

After the example runs, a new map will have been saved to the data folder containing the optimized anchoring associated with the blueprint.

## Understanding the Example Code

### Background on Anchorings and Metric Consistency

Graph Nav maps are a collection of waypoints and edges. Waypoints define named locations in the world, and edges define how to get from one waypoint to another. Normally, there is no requirement that Graph Nav maps have what is called "metric accuracy," or "metric consistency." That is, there is actually no fixed reference frame that Graph Nav maps can be displayed in.

For example, let's suppose we have three waypoints w1 and w2, and w3 connected by the edges (w1, w2), (w2, w3) and (w1, w3). Topologically, this is a triangle:

```
w1 - w2
  \  |
    w3
```

Now, let's suppose the edge (w1, w2) is defined as

```
from_tform_to = (x = 1, y = 0, z = 0, rotation = identity)
```

and let's suppose the edge (w1, w3) is:

```
from_tform_to = (x = 1, y = 1, z = 0, rotation = identity)
```

And (w2, w3) is:

```
from_tform_to = (x = -0.1, y = 1.5, z = 0, rotation = identity)
```

Now, let's suppose we want to determine where all the waypoints are in some fixed reference frame. If we only know about the edge transformations, and arbitrarily assign `w1` to be the origin of our fixed reference frame, we can follow w1 through (w1, w2) to determine that (w2) is at `x=1, y=0, z=0`. But what about w3? The answer actually depends on whether we take the path through (w2, w3) or (w1, w3)!

If we take the first path, we would find that w3's coordinates are `x=0.9, y=1.5`. If we take the second path, we find that w3's coordinates are `x = 1, y = 1`. This is because the graph shown above is _metrically inconsistent_.

Graph Nav maps normally become metrically inconsistent due to _odometry drift_ and inaccurate measurements between waypoints. This is normally okay -- the robot can tolerate a large amount of metric inconsistency while localizing and navigating. However, if you wish to use a Graph Nav map for visualization or creating a high quality map, or registering to existing data, metric inconsistency can make this task very difficult.

To solve this problem, Graph Nav provides a concept called _anchorings_. Anchorings are a mapping from waypoint to its pose in a metrically consistent reference frame. A graph may have many anchorings, for example to a blueprint, BIM model, or point cloud. By providing an anchoring to a graph nav graph, you can more easily display and manipulate Graph Nav maps for your specific application.

### Anchoring Optimization

The _Map Processing Service_ can be used to find metrically consistent anchorings using anchoring optimization, and can be used to align Graph Nav maps to other data sources such as blueprints.

In this example, we will show how to use the _Anchoring Optimization Service_ to align graph nav maps to a blueprint. Graph Nav maps can be aligned to any data source so long as we have good guesses for where either an April Tag or a specific waypoint is with respect to that data. In this example, we will align an April Tag to a blueprint, and use that as a hint for anchoring optimization -- but you could also align individual waypoints to a blueprint, or use another data source such as a digital twin or BIM model.

#### Step 1: setting up a connection to the robot

The Map Processing Service runs on the robot. Therefore, we will need a connection to the robot, and a lease.

```python
    # Setup and authenticate the robot.
    sdk = bosdyn.client.create_standard_sdk('Anchoring Optimization Example')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    _lease_client = robot.ensure_client(LeaseClient.default_service_name)

    # We need a lease for the robot to access the map services. This prevents multiple
    # clients from fighting over the map data.
    _lease_wallet = _lease_client.lease_wallet
    with LeaseKeepAlive(_lease_client, return_at_exit=True):

        # Create clients for graph nav and map processing.
        graph_nav_client = robot.ensure_client(GraphNavClient.default_service_name)
        map_processing_client = robot.ensure_client(MapProcessingServiceClient.default_service_name)

```

#### Step 2: loading and uploading a graph_nav graph and data

The map processing service requires us to upload a graph nav graph and associated snapshot data. The service uses these data to create a metrically consistent anchoring. Maps are stored in the graph nav service, which requires a graph nav client connection. Once inside the graph nav service, maps are accessible to the map processing service.

```python
        # ... Inside the LeaseKeepAlive context manager
        # Load the graph from the disk and upload it to the robot.
        (graph, waypoint_snapshots, edge_snapshots) = load_graph_and_snapshots(options.input_map)
        upload_graph_and_snapshots(graph_nav_client, graph, waypoint_snapshots, edge_snapshots)

```

#### Step 3: Defining the optimization problem

Now that we have a connection to the robot and have loaded the graph and snapshots, we can tell the map processing service to optimize the graph's anchoring.

We can provide _parameters_ for the optimizer and _hints_. Parameters control how many iterations the optimizer will run, and what data sources it will use for optimization. If no parameters are provided, the optimizer will use reasonable defaults. Hints tell the optimizer information about the anchoring -- for example where a particular April Tag is, or a particular waypoint. If we provide no hints at all, the Map Processing Service will choose an arbitrary waypoint to be the origin.

In this case, we will provide a single hint to the service -- the location of a fiducial (April Tag).

```python
def optimize_anchoring(opt_info, client):
    """
    Sends an RPC to the robot which optimizes the anchoring and links it to the position of the
    fiducial in the blueprint.
    :param opt_info: info needed for the optimization.
    :param client: the map processing client.
    :return: the response to the process_anchoring rpc.
    """
    initial_hint = map_processing_pb2.AnchoringHint()
    object_hint = initial_hint.world_objects.add()
    object_hint.object_anchor.id = str(opt_info.fiducial_id)
    object_hint.object_anchor.seed_tform_object.CopyFrom(opt_info.get_fiducial_origin())
```

To get the location of a fiducial, we start with a blueprint image (an example is provided in this example at `data/house_plans.png`). We need to know the relationship between pixels and meters in the image. In this case, the blueprint provides a helpful ruler that tells us the scale -- approximately 49.2 pixels per meter. Once we know this, and we know the location of the fiducial on the blueprint, we can calculate the pose of the fiducial in our desired anchoring frame. NOTE: we will assume that the fiducial is mounted vertically against a wall, with the fiducial "number" upright.

```python

    def get_fiducial_origin(self):
        """
        Get an SE3Pose proto defining the origin of the fiducial in the world frame.
        The world frame starts at the bottom left of the image, with positive y up, positive x
        to the right, and positive z out of the page.
        :return: the SE3Pose proto defining the fiducial in this origin.
        """
        theta = np.deg2rad(self.fiducial_rotation)
        # Fiducial frame:
        # Assume x is up, and z points out. The rotation matrix
        # therefore has x pointed directly out of the page, and
        # the zy vectors pointing to the left and up respectively.
        # Note that the image origin has z pointing out of the page,
        # y up and x to the right.
        # Therefore, the z axis is equal to (cos(t), sin(t)) and the y axis is
        #  (sin(t), -cos(t)).
        rot_matrix = np.array([[0, np.sin(theta), np.cos(theta)],
                               [0, -np.cos(theta),  np.sin(theta)],
                               [1, 0, 0]])
        world_tform_fiducial = SE3Pose(rot=Quat.from_matrix(rot_matrix),
                                       x=self.fiducial_position[0]/self.pixels_per_meter,
                                       y=self.fiducial_position[1]/self.pixels_per_meter,
                                       z=0)
```

By convention, we will assume that the origin of the anchoring is the bottom left of the image, and that the `x` axis is to the right, with the `y` axis up. We will also assume the `z` height of the fiducial is fixed at `z = 0`. From there, we can determine the position and orientation of the fiducial in 3D space w.r.t the anchoring.

We pass this in as an initial hint to the anchoring optimizer, which it will use to align our map to the blueprint (and to ensure that it is metrically consistent).

### Running the optimization and interpreting the results

We can now send a ProcessAnchoringRequest to the Map Processing Service with our initial guess, and get a result back.

```python
    return client.process_anchoring(params=map_processing_pb2.ProcessAnchoringRequest.Params(
                                        optimize_existing_anchoring=BoolValue(value=False)
                                    ),
                                    modify_anchoring_on_server=False,
                                    stream_intermediate_results=False,
                                    initial_hint=initial_hint)
```

We will choose not to `optimize_existing_anchoring`, `modify_anchoring_on_server` or `stream_intermediate_results` in this example. `modify_anchoring_on_server` changes the anchoring that the robot has internally, `optimize_existing_anchoring` uses the anchoring on the server as an initial guess, and `stream_intermediate_results` will send back partial results at each iteration of the optimization for debugging and visualization purposes.

The type of the result is `ProcessAnchoringResponse`. It has a status code, number of iterations, and final cost. If the optimizer failed, or the initial hints were malformed, the optimizer will return a failed status code with some information about why it failed.

If optimization succeeds the optimizer returns a new `Anchoring`.

```python
    # Extract the anchoring from the RPC response.
    optimized_anchoring = map_pb2.Anchoring()
    for wp in anchoring_response.waypoint_results:
        optimized_anchoring.anchors.add().CopyFrom(wp)
    for obj in anchoring_response.world_object_results:
        optimized_anchoring.objects.add().CopyFrom(obj)
```

As we can see, an `Anchoring` just consists of a set of waypoints and world objects (for the time being, just April Tags), and the optimized SE3Pose of those waypoints and objects in the anchoring reference frame (in this case, the position/orientation with respect to the lower left corner of the blueprint image).

We can now draw the anchorings on the blueprint using `matplotlib`.

The image in `data/optimized_anchoring.png` shows the anchoring before optimization (red), and after (green) as a set of lines. Each line is just a line between individual waypoints in the graph which have an edge between them. The fiducial is also shown as two axes, its `z` axis (blue) and its `y` axis (green). We can see it is on the closet door of the upper left bedroom.

Note that in the optimized anchoring, the apparent path of the robot is from the upper left bedroom into the living room on the lower right, and then back.

### Other ways of viewing anchorings

The `view_map.py` example now takes in an argument `-a`, which can be used to draw a map in its anchoring frame. We can also draw the newly optimized map in the anchoring frame after saving it by calling from this directory:

`view_map -a ./data/blueprint_example_optimized.walk`

An example can be seen in the image stored in this example: `data/optimized_anchoring_viewer.png`, where we can see the point clouds of the map drawn in the anchoring frame.

When `-a` is not passed as an argument, the map is shown by chaining edges together starting from an arbitrary origin. As discussed in the first section, this results in an inconsistent drawing.

The difference is subtle -- in the unoptimized map, we can see that there is significant height drift between the robot's initial path from the upper left bedroom to the living room and back. This is made most apparent by looking at fiducial 319, which appears in multiple places (with different heights) depending on which waypoint is observing it. In the optimized anchoring, this drift is totally corrected.
