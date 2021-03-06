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

from twisted.internet import defer, reactor
from twisted.python.failure import Failure
from Products.ZenEvents import ZenEventClasses
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSourcePlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap
from ZenPacks.zenoss.ZooKeeper.utils import ZooKeeperClientFactory, check_error


class ZooKeeperPlugin(PythonDataSourcePlugin):
    '''Monitoring plugin for ZooKeeper'''
    proxy_attributes = ('zZooKeeperPort',)

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
    def collect(self, config):
        data = self.new_data()
        ds = config.datasources[0]

        result = yield self.get_result(ds.manageIp, int(ds.zZooKeeperPort))
        if result:
            data['values'][ds.component] = self.parse_values(result)
        else:
            raise Failure(Exception('No monitoring data received'))

        defer.returnValue(data)

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
        data = self.new_data()

        msg = check_error(result)
        if isinstance(result, Failure):
            msg = check_error(result.value, True)

        log.error(msg)
        data['events'].append({
            'component': component,
            'summary': msg,
            'eventClass': '/Status',
            'eventKey': 'zookeeper_result',
            'severity': ZenEventClasses.Error,
        })
        return data

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
