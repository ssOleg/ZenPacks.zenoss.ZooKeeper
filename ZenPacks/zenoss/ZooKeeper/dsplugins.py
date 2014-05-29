######################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is
# installed.
#
######################################################################

from logging import getLogger
log = getLogger('zen.ZooKeeper')

from twisted.internet import defer
from twisted.python.failure import Failure
import socket
from Products.ZenEvents import ZenEventClasses
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap


class ZooKeeperPlugin(PythonDataSourcePlugin):
    '''Monitoring plugin for ZooKeeper'''
    proxy_attributes = ('zZooKeeperPort',)

    @defer.inlineCallbacks
    def collect(self, config):
        values = {}
        events = []
        maps = []
        ds = config.datasources[0]

        socketobject = socket.socket()
        try:
            yield socketobject.connect((ds.manageIp, int(ds.zZooKeeperPort)))
        except Exception as e:
            socketobject.close()
            raise e
        result = []
        if socketobject:
            socketobject.sendall('stat\n')
            while True:
                data = socketobject.recv(4096)
                if not data:
                    break
                result.append(data)
            socketobject.close()
        if result:
            values[ds.component] = self.parse_values("".join(result))
        else:
            raise Failure(Exception('No monitoring data received'))
        defer.returnValue(dict(
            events=events,
            values=values,
            maps=maps,
        ))

    def onSuccess(self, result, config):
        component = config.datasources[0].component
        result['events'].append({
            'component': component,
            'summary': 'Monitoring ok',
            'eventClass': '/Status',
            'eventKey': 'zookeeper_result',
            'severity': ZenEventClasses.Clear,
        })
        return result

    def onError(self, result, config):
        component = config.datasources[0].component
        msg = result
        if isinstance(result, Failure):
            msg = result.value
            if isinstance(result.value, (ValueError, OverflowError)):
                msg = 'Incorrect zZooKeeperPort property entered'
            if isinstance(result.value, socket.error):
                msg = result.value.strerror
        log.error(msg)
        return {
            'vaues': {},
            'events': [{
                'component': component,
                'summary': 'error monitoring: {}'.format(msg),
                'eventClass': '/Status',
                'eventKey': 'zookeeper_result',
                'severity': ZenEventClasses.Error,
            }],
            'maps': [],
        }

    def parse_values(self, data):
        """Look for values in result"""
        result = {}
        data = data.split('\n')[:-1]
        for element in data:
            if 'Latency min/avg/max' in element:
                result['latency_min'], result['latency_avg'], \
                    result['latency_max'] = (
                        (int(x), 'N') for x in
                        element.split(':', 1)[1].split('/')
                    )
            if 'Received' in element:
                result['received'] = (int(element.split(':', 1)[1]), 'N')
            if 'Sent' in element:
                result['sent'] = (int(element.split(':', 1)[1]), 'N')
            if 'Connections' in element:
                result['connections'] = (int(element.split(':', 1)[1]), 'N')
            if 'Outstanding' in element:
                result['outstanding'] = (int(element.split(':', 1)[1]), 'N')
        return result
