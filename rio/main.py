import logging
import os
import socket
import sys
import time

from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

from config import build_parser, run_parser
from protocols import RioClientFactory, RioServerFactory
from rio import FileChecker, MasterChecker, RioStates, STATE_KO

log = logging.getLogger(__name__)

def main():
    parser = build_parser()
    options = run_parser(parser, sys.argv[1:])

    rio_states = RioStates(options.nodename, options.priority, options.timeout)
    filechecker = FileChecker(options.check_file)
    masterchecker = MasterChecker(rio_states, options.state_file)

    logging.basicConfig(level=logging.DEBUG)
    log.info("Node %s starting!", options.nodename)

    endpoint = TCP4ServerEndpoint(reactor, options.local_port)

    nodes = []
    for arg in options.nodes:
        host,port = arg.split(':')
        port = int(port)
        fac = RioClientFactory(rio_states)
        reactor.connectTCP(host, port, fac)

    endpoint.listen(RioServerFactory(rio_states))
    reactor.callLater(5, do_the_check(rio_states, filechecker, masterchecker))
    reactor.run()

def do_the_check(rio_states, checker, masterchecker):
    def loop_check():
        state = checker.check()
        if not state:
            state = STATE_KO
        rio_states.update_self(str(time.time()), str(state))
        masterchecker.check()
        for nodename in rio_states.remove_outdated():
            log.info("Removed timed out node %s", nodename)
        reactor.callLater(5, loop_check)
    return loop_check

