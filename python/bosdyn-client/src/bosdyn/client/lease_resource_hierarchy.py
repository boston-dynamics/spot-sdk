# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Helper for managing hierarchy of lease resources."""


class ResourceHierarchy:
    """Helper for managing hierarchy of lease resources."""

    def __init__(self, resource_tree_proto):
        self._resource_tree = resource_tree_proto

        # Map tracking sub hierarchies with the key: resource (string),
        # and value = ResourceHierarchy obj rooted at the key's resource.
        self._sub_hierarchies = {}

        # Set of the lease resources (strings) in this hierarchy.
        self._leaf_resources = set()

        if len(self._resource_tree.sub_resources) == 0:
            self._leaf_resources.add(self._resource_tree.resource)
            return

        for sub_tree in self._resource_tree.sub_resources:
            new_sub_hierarchy = ResourceHierarchy(sub_tree)
            self._sub_hierarchies[sub_tree.resource] = new_sub_hierarchy

            # Merge all sub resources/leaves from the new hierarchy so they are quickly accessible
            # from this hierarchy.
            for resc in new_sub_hierarchy._sub_hierarchies:
                self._sub_hierarchies[resc] = new_sub_hierarchy._sub_hierarchies[resc]
            for leaf in new_sub_hierarchy._leaf_resources:
                self._leaf_resources.add(leaf)

    def has_resource(self, resource):
        """Return a boolean indicating if the resource is in this hierarchy."""
        return resource == self._resource_tree.resource or resource in self._sub_hierarchies

    def has_sub_resources(self):
        """Return a boolean indicating whether this hierarchy has sub-trees."""
        return len(self._sub_hierarchies) > 0

    def get_resource(self):
        """Get the root resource string for this hierarchy."""
        return self._resource_tree.resource

    def get_resource_tree(self):
        """Get the resource tree protobuf message corresponding with this hierarchy."""
        return self._resource_tree

    def leaf_resources(self):
        """Get a set of all leaf resources in this tree."""
        return self._leaf_resources

    def get_hierarchy(self, resource):
        """Get the sub-tree corresponding to the specified resource.

        Args:
            resource (string): The root resource for the hierarchy.

        Returns:
            The ResourceHierarchy object corresponding with this tree, or None
            if the resource is not within this tree.
        """
        if resource == self.get_resource():
            return self
        if resource in self._sub_hierarchies:
            return self._sub_hierarchies[resource]
        return None

    def __eq__(self, other):
        return (self._resource_tree == other._resource_tree and
                self._leaf_resources == other._leaf_resources and
                self._sub_hierarchies == other._sub_hierarchies)
