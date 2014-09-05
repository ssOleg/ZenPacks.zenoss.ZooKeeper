##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################


import os
import logging
log = logging.getLogger('zen.ZooKeeperTest')

from twisted.internet.error import ConnectionRefusedError

from Products.DataCollector.ApplyDataMap import ApplyDataMap
from Products.ZenTestCase.BaseTestCase import BaseTestCase

from ZenPacks.zenoss.ZooKeeper.modeler.plugins.ZooKeeperCollector import \
    ZooKeeperCollector
from ZenPacks.zenoss.ZooKeeper.dsplugins import ZooKeeperPlugin
from ZenPacks.zenoss.ZooKeeper.tests.utils import test_device, load_data


class Mock(object):
    """Mock object for x._p_jar.

    Used to trick ApplyDataMap into not aborting transactions after adding
    non-persistent objects. Without doing this, all sub-components will
    cause ugly tracebacks in modeling tests.

    """
    def sync(self):
        pass


class ModelerPluginTestCase(BaseTestCase):

    def afterSetUp(self):
        super(ModelerPluginTestCase, self).afterSetUp()
        self.d = test_device(self.dmd, factor=1)
        self.d.dmd._p_jar = Mock()
        self.applyDataMap = ApplyDataMap()._applyDataMap

    def _loadZenossData(self):
        if hasattr(self, '_loaded'):
            return

        modeler = ZooKeeperCollector()
        modeler_results = load_data('zookeeper_data.txt')

        rel_map = modeler.process(self.d, modeler_results, log)
        self.applyDataMap(self.d, rel_map)

        self._loaded = True

    def test_ZooKeeperComponent(self):
        self._loadZenossData()
        zookeeper = self.d.zookeepers._getOb('127.0.0.1_2182')

        self.assertEquals(zookeeper.device().id, 'zookeeper_test_device')
        self.assertEquals(zookeeper.mode, ' standalone')
        self.assertEquals(zookeeper.node_count, ' 28')
        self.assertEquals(zookeeper.zxid, ' 0xc88d')


class MonitoringPluginTestCase(BaseTestCase):

    def afterSetUp(self):
        super(MonitoringPluginTestCase, self).afterSetUp()
        self.d = test_device(self.dmd, factor=1)
        self.plugin = ZooKeeperPlugin()

    def test_parse_values(self):
        data = load_data('zookeeper_data.txt')
        result = self.plugin.parse_values(data)

        self.assertEquals(result.get('latency_min'), (0.0, 'N'))
        self.assertEquals(result.get('latency_avg'), (0.0, 'N'))
        self.assertEquals(result.get('latency_max'), (925.0, 'N'))
        self.assertEquals(result.get('connections'), (5.0, 'N'))
        self.assertEquals(result.get('outstanding'), (0.0, 'N'))
        self.assertEquals(result.get('received'), (349729.0, 'N'))
        self.assertEquals(result.get('sent'), (349808.0, 'N'))

    def test_onSuccess(self):
        data = self.plugin.new_data()
        config = ds = Mock()
        ds.component = '127.0.0.1_2182'
        config.datasources = [ds]

        self.assertIn({
            'severity': 0,
            'eventClass': '/Status',
            'component': ds.component,
            'eventKey': 'zookeeper_result',
            'summary': 'Monitoring ok'
        }, self.plugin.onSuccess(data, config).get('events'))

    def test_onError(self):
        config = ds = Mock()
        ds.component = '127.0.0.1_2182'
        config.datasources = [ds]
        error = ConnectionRefusedError()

        self.assertIn({
            'severity': 4,
            'eventClass': '/Status',
            'component': ds.component,
            'eventKey': 'zookeeper_result',
            'summary': ('The modeling failed due to connection issue. '
                        'Verify the value of zZooKeeperPort and re-try')
        }, self.plugin.onError(error, config).get('events'))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ModelerPluginTestCase))
    suite.addTest(makeSuite(MonitoringPluginTestCase))
    return suite
