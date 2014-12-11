import logging
import os
import socket
import sys

from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

from config import build_parser
from protocols import RioClientFactory, RioServerFactory
from rio import FileChecker, MasterChecker, RioStates

log = logging.getLogger(__name__)

rio_states = RioStates()
parser = build_parser()
print parser.parse_args(sys.argv[1:])
sys.exit(0)
lport = int(sys.argv[1])

nodename = "rionode-%s-%d" % (socket.getfqdn(), lport)
filechecker = FileChecker(rio_states, nodename, 10, "/tmp/riocheck")
masterchecker = MasterChecker(rio_states, nodename)

logging.basicConfig(level=logging.DEBUG)
log.info("Node %s starting!", nodename)

endpoint = TCP4ServerEndpoint(reactor, lport)

nodes = []
for arg in sys.argv[2:]:
    host,port = arg.split(':')
    port = int(port)
    fac = RioClientFactory(rio_states)
    reactor.connectTCP(host, port, fac)

endpoint.listen(RioServerFactory(rio_states))

def loop_check():
    filechecker.check()
    masterchecker.check()
    for nodename in rio_states.remove_outdated():
        log.info("Removed timed out node %s", nodename)
    reactor.callLater(5, loop_check)

reactor.callLater(5, loop_check)

reactor.run()
