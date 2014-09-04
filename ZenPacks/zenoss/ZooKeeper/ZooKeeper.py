######################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is
# installed.
#
######################################################################
from zope.component import adapts
from zope.interface import implements

from Products.ZenModel.ManagedEntity import ManagedEntity
from Products.ZenModel.ZenossSecurity import ZEN_CHANGE_DEVICE
from Products.ZenRelations.RelSchema import ToManyCont, ToOne

from Products.Zuul.decorators import info
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t

from .ZooKeeperComponent import ZooKeeperComponent


class ZooKeeper(ZooKeeperComponent):
    meta_type = portal_type = "ZooKeeper"

    mode = None
    node_count = None
    zookeeper_version = None
    zxid = None

    _properties = ZooKeeperComponent._properties + (
        {'id': 'mode', 'type': 'string'},
        {'id': 'node_count', 'type': 'string'},
        {'id': 'zookeeper_version', 'type': 'string'},
        {'id': 'zxid', 'type': 'string'},
    )

    _relations = ZooKeeperComponent._relations + (
        ('zookeeper_host', ToOne(
            ToManyCont, 'Products.ZenModel.Device.Device', 'zookeepers')),
    )

    def device(self):
        return self.zookeeper_host()


class IZooKeeperInfo(IComponentInfo):
    '''
    API Info interface for ZooKeeper.
    '''
    mode = schema.TextLine(title=_t(u'Mode'))
    node_count = schema.TextLine(title=_t(u'Node Count'))
    zookeeper_version = schema.TextLine(title=_t(u'ZooKeeper Version'))
    zxid = schema.TextLine(title=_t(u'Zxid'))


class ZooKeeperInfo(ComponentInfo):
    '''
    API Info adapter factory for ZooKeeper.
    '''
    implements(IZooKeeperInfo)
    adapts(ZooKeeper)

    mode = ProxyProperty('mode')
    node_count = ProxyProperty('node_count')
    zookeeper_version = ProxyProperty('zookeeper_version')
    zxid = ProxyProperty('zxid')
