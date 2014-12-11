from collections import defaultdict, namedtuple
from hashlib import md5
import logging
import os
import time

from cached_property import cached_property

log = logging.getLogger(__name__)

NodeState = namedtuple('NodeState', 'nodename priority update state')

STATE_GONE = 0
STATE_KO = 2
STATE_OK = 3

class MasterChecker(object):
    time = time.time
    master = None

    def __init__(self, rio_states, nodename):
        self.rio_states = rio_states
        self.nodename = nodename

    def check(self):
        new_master = getattr(self.rio_states.master, 'nodename', None)

        if self.master == new_master:
            return
        if self.nodename == self.master:
            log.info("Stepping down as master! (new master: %s)",
                     new_master)

        if self.nodename == new_master:
            log.info("Stepping up as master! (old master: %s)",
                     self.master)
        else:
            if not new_master:
                log.warning("No more master available!")
            log.info("New master (not us): %s", new_master)

        self.master = new_master

class FileChecker(object):
    time = time.time

    def __init__(self, rio_states, nodename, priority, filename="/tmp/riocheck"):
        self.rio_states = rio_states
        self.nodename = nodename
        self.priority = priority
        self.filename = filename

    def check(self):
        try:
            r = os.stat(self.filename)
            if r:
                return self.rio_states.update_node(self.nodename, str(self.priority),
                                                   str(self.time()), str(STATE_OK))
        except:
            pass
        return self.rio_states.update_node(self.nodename, str(self.priority),
                                           str(self.time()), str(STATE_KO))


class RioStates(object):
    time = time.time
    threshold = 10

    def __init__(self):
        self.nodes = {}
        self.change_hooks = []

    def update_node(self, nodename, priority, last_update, state):
        # check that the input data is valid
        _ = int(priority)
        _ = float(last_update)
        _ = int(state)

        new_state = NodeState(nodename, priority, last_update, state)
        last_state = self.nodes.get(nodename, None)

        if last_state == new_state:
            #log.debug("No change, duplicate message?")
            return

        if float(last_update) < self.time() - self.threshold or \
           (last_state and float(new_state.update) <= float(last_state.update)):
            log.debug("Ignoring outdated report %r", new_state)
            return


        if hasattr(self, 'master'):
            del self.master # cached_property magic

        self.nodes[nodename] = new_state
        if hasattr(self, 'master'):
            del self.master  # cached_property magic

        for hook in self.change_hooks:
            hook(self, new_state, self.master)

        # schedule timeouts

    @cached_property
    def master(self):
        nodes_by_prio = defaultdict(list)
        for nodename, node in self.nodes.iteritems():
            if int(node.state) == STATE_OK:
                nodes_by_prio[int(node.priority)].append(node)
        if not nodes_by_prio:
            return

        best_ones = reversed(sorted(nodes_by_prio.items())).next()[1]
        if len(best_ones) == 1:
            return best_ones[0]
        else:
            md5_nodes = [ (md5("%s%s"% (node.nodename, node.priority)).digest(), node)
                          for node in best_ones ]
            best_one = sorted(md5_nodes)[0][1]
            return best_one

    def remove_outdated(self):
        threshold = self.time() - self.threshold
        for nodename, node in self.nodes.items():
            if float(node.update) < threshold:
                del self.nodes[nodename]
                yield nodename


def main():
    logging.basicConfig(level=logging.DEBUG)
    rns = RioStates()
    def print_updates(rns, new_state, master):
        log.debug("After updating %s, new master is %s", new_state, master)
    rns.change_hooks.append(print_updates)
    rns.update_node("aap",1,2,2)
    rns.update_node("noot",2,3,3)
    rns.update_node("aap",1,3,3)
    rns.update_node("mies",2,4,2)
    rns.update_node("mies",2,4,2)
    rns.update_node("mies",2,5,3)
    rns.update_node("noot",2,6,3)
    log.debug("Calling remove gives %r", list(rns.remove_outdated(4.5)))
    log.debug("Calling remove gives %r", list(rns.remove_outdated(4.5)))
    log.debug("States now is %r, %r", rns.nodes, rns.master)
