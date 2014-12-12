from twisted.internet.protocol import Factory, ReconnectingClientFactory

from twisted.protocols.basic import LineOnlyReceiver

class RioProtocol(LineOnlyReceiver):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.rio_states.change_hooks.append(self.rio_states_change_hook)

    def connectionLost(self, reason):
        self.factory.rio_states.change_hooks.remove(self.rio_states_change_hook)

    def lineReceived(self, line):
        try:
            command, _, rest = line.partition(",")
        except:
            self.abortConnection()
            raise # should barf and complain

        if command == 'auth':
            pass
        elif command == 'ping':
            try:
                nodename, priority, last_update, state = rest.split(",")
            except:
                self.abortConnection()
                raise # should barf and complain
            self.factory.rio_states.update_node(nodename, priority,
                                                last_update, state)
        else:
            self.abortConnection()
            return

    def rio_states_change_hook(self, rio_states, new_state, master):
        the_line = ",".join(list(new_state))
        self.sendLine("ping,%s" % the_line)

class RioServerFactory(Factory):
    def __init__(self, rio_states):
        self.rio_states = rio_states

    def buildProtocol(self, addr):
        return RioProtocol(self)

class RioClientFactory(ReconnectingClientFactory):
    protocol = RioProtocol
    maxDelay = 30
    initialDelay = 1.0
    factor = 1.61803399

    def __init__(self, rio_states):
        self.rio_states = rio_states

    def buildProtocol(self, addr):
        self.resetDelay()
        return self.protocol(self)
