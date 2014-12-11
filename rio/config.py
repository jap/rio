import argparse
import socket

default_nodename = "rionode-%s-%%d" % socket.getfqdn()
default_priority = 7
default_rio_port = 2343 # just look at the map, 23S 43W
default_timeout = 10

def build_parser():
    parser = argparse.ArgumentParser(description='Run It Once',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-L', '--local-port', type=int,
                        default=default_rio_port,
                        help='tcp-port on which to listen for connections')
    parser.add_argument('-p', '--priority', type=int,
                        default=default_priority,
                        help='priority of this node (lower is preferred')
    parser.add_argument('-t', '--timeout', type=int,
                        default=default_timeout,
                        help='timeout (in seconds) after which inactive nodes will be considered gone')

    parser.add_argument('-n', '--nodename', type=str,
                        default=default_nodename,
                        help='nodename for identification (should be unique in a cluster)')

    parser.add_argument('nodes', type=str, nargs='+',
                        help='list of nodes to connect to (hostname:port)')

    return parser
