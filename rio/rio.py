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
    state_file = None

    def __init__(self, rio_states, state_file):
        self.rio_states = rio_states
        self.state_file = state_file

    def check(self):
        new_master = getattr(self.rio_states.master, 'nodename', None)
        nodename = self.rio_states.nodename

        if self.master == new_master:
            if self.master == nodename:
                # we're still the master!
                self.touch_file()
            return

        if nodename == self.master:
            log.info("Stepping down as master! (new master: %s)",
                     new_master)
            try:
                os.unlink(self.state_file)
            except:
                log.exception("Failure unlinking state_file")

        if nodename == new_master:
            log.info("Stepping up as master! (old master: %s)",
                     self.master)
            self.touch_file()
        else:
            if not new_master:
                log.warning("No more master available!")
            log.info("New master (not us): %s", new_master)

        self.master = new_master

    def touch_file(self):
        try:
            with file(self.state_file, "w") as f:
                pass
        except:
            log.exception("Failure creating state_file")


class FileChecker(object):
    time = time.time

    def __init__(self, filename="/tmp/riocheck"):
        self.filename = filename

    def check(self):
        try:
            r = os.stat(self.filename)
            return STATE_OK
        except:
            return STATE_KO


class RioStates(object):
    time = time.time

    def __init__(self, nodename, priority, timeout):
        self.nodes = {}
        self.change_hooks = []
        self.nodename = nodename
        self.priority = str(priority)
        self.timeout = timeout

    def update_self(self, time, state):
        return self.update_node(self.nodename, self.priority,
                                time, state)

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

        if float(last_update) < self.time() - self.timeout or \
           (last_state and float(new_state.update) <= float(last_state.update)):
            log.debug("Ignoring outdated report %r", new_state)
            log.debug("Now-timeout: %s LU: %s", (self.time()-self.timeout),
                      float(last_update))
            log.debug("New state: %r", new_state)
            log.debug("Old state: %r", last_state)

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
        threshold = self.time() - self.timeout
        for nodename, node in self.nodes.items():
            if float(node.update) < threshold:
                del self.nodes[nodename]
                yield nodename
