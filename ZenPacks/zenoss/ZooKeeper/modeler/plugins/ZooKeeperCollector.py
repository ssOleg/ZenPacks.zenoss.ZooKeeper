##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

''' Models discovery tree for ZooKeeper. '''

import socket

import zope.component
from twisted.internet import defer, reactor
from Products.ZenUtils.Utils import prepId
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.ZenCollector.interfaces import IEventService
from ZenPacks.zenoss.ZooKeeper import MODULE_NAME
from ZenPacks.zenoss.ZooKeeper.utils import ZooKeeperClientFactory


class ZooKeeperCollector(PythonPlugin):
    '''
    PythonCollector plugin for modelling device components
    '''
    _eventService = zope.component.queryUtility(IEventService)

    deviceProperties = PythonPlugin.deviceProperties + (
        'zZooKeeperPort',
    )

    def get_result(self, host, port):
        """
        Get data from the given host and port. This function
        returns a Deferred which will be fired with the complete text of
        the ZooKeeper details or a Failure if the details could not be loaded.
        """
        d = defer.Deferred()
        factory = ZooKeeperClientFactory(d)
        reactor.connectTCP(host, port, factory)
        return d

    @defer.inlineCallbacks
    def collect(self, device, log):
        log.info("Collecting ZooKeeper data for device %s", device.id)

        res = ''
        try:
            res = yield self.get_result(
                device.manageIp, int(device.zZooKeeperPort)
            )
        except Exception, e:
            if isinstance(e, (ValueError, socket.error)):
                e = 'Check zZooKeeperPort property, port must be 0-65535'
            log.warn(e)

        defer.returnValue(res)

    def process(self, device, results, log):
        log.info(
            'Modeler %s processing data for device %s',
            self.name(), device.id
        )

        zookeeper = device.manageIp + ':' + device.zZooKeeperPort
        om = {
            'id': prepId(zookeeper),
            'title': zookeeper,
        }
        self.update_object_map(results, om)

        log.info(
            'Modeler %s finished processing data for device %s',
            self.name(), device.id
        )
        return RelationshipMap(
            relname='zookeepers',
            modname=MODULE_NAME['ZooKeeper'],
            objmaps=[ObjectMap(om)]
        )

    def update_object_map(self, data, object_map):
        """Look for attribute in configuration"""
        result = {}
        data = data.split('\n')[:-1]
        for element in data:
            if 'Zookeeper version' in element:
                result['zookeeper_version'] = element.split(':', 1)[1]
            if 'Zxid' in element:
                result['zxid'] = element.split(':', 1)[1]
            if 'Mode' in element:
                result['mode'] = element.split(':', 1)[1]
            if 'Node count' in element:
                result['node_count'] = element.split(':', 1)[1]
        if result:
            object_map.update(result)
