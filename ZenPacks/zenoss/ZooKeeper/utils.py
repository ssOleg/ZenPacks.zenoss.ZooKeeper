######################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is
# installed.
#
######################################################################

from socket import error as SocketError

from twisted.internet.error import ConnectionRefusedError
from twisted.internet.protocol import Protocol, ClientFactory


class ZooKeeperProtocol(Protocol):

    result = ''

    def connectionMade(self):
        self.transport.write('stat\n')

    def dataReceived(self, data):
        self.result += data

    def connectionLost(self, reason):
        self.resultReceived(self.result)

    def resultReceived(self, result):
        self.factory.finished(result)


class ZooKeeperClientFactory(ClientFactory):

    protocol = ZooKeeperProtocol

    def __init__(self, deferred):
        self.deferred = deferred

    def finished(self, result):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.callback(result)

    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.errback(reason)


def check_error(error, key=None):
    '''
    Check if error is due to Connection or Socket Error or the value
    supplied for port is not of int type (ValueError)
    and return correct message for log or event.
    '''
    prefix = 'The ZooKeeper modeling'
    if key:
        prefix = 'The ZooKeeper monitoring'
    if isinstance(error, (ValueError, SocketError, ConnectionRefusedError)):
        return ('{} failed due to connection issue. '
                'Verify the value of zZooKeeperPort and re-try'.format(prefix))
    return str(error)
