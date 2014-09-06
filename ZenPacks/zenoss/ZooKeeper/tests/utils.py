##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import os.path

from zope.event import notify
from Products.Zuul.catalog.events import IndexingEvent


def load_data(filename):
    path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(path, 'r') as f:
        return f.read()


def add_obj(relationship, obj):
    """
    Add obj to relationship, index it, then returns the persistent
    object.
    """
    relationship._setObject(obj.id, obj)
    obj = relationship._getOb(obj.id)
    obj.index_object()
    notify(IndexingEvent(obj))
    return obj


def test_device(dmd, factor=1):
    """
    Return an example Device with a set of example components.
    """

    from ZenPacks.zenoss.ZooKeeper.ZooKeeper import ZooKeeper

    dc = dmd.Devices.createOrganizer('/Server')

    device = dc.createInstance('zookeeper_test_device')
    device.setPerformanceMonitor('localhost')
    device.manageIp = '127.0.0.1'
    device.setZenProperty('zZooKeeperPort', '2182')
    device.index_object()
    notify(IndexingEvent(device))

    # ZooKeeper
    for zookeeper_id in range(factor):
        zookeeper = add_obj(
            device.zookeepers,
            ZooKeeper('zookeeper%s' % (zookeeper_id))
        )

    return device
