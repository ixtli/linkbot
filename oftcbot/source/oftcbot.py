#!/usr/bin/python

# By Chris Galardi

"""
IRC Bot that logs links posted by users of a channel and some discussion about
then. 
"""

# system imports
import time
import sys
import os

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

class MessageLogger:
    """
    Logger class for recording interaction with the bot
    """

    log_file = None

    def __init__(self, f):
        self.log_file = f

    def log(self, message):
        """Log a message"""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.log_file.write('%s %s\n' % (timestamp, message))
        self.log_file.flush()

    def close(self):
        self.log_file.close()

    def __del__(self):
        self.close()


class LinkBot(irc.IRCClient):
    """A bot for logging links to a file with metadata."""

    nickname = "linkbot"
    logger = None

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        try:
            f = open(self.factory.filename, 'a')
        except IOError as err:
            print(err)
            sys.exit(2)
        self.logger = MessageLogger(f)
        self.logger.log("[connected as %s]" %
                        time.asctime(time.localtime(time.time())))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" %
                        time.asctime(time.localtime(time.time())))
        del self.logger

    # event callbacks

    def signedOn(self):
        """Called when bot has succesfully connected"""
        self.join(self.factory.channel)

    def joined(self, channel):
        """Called when bot joins channel"""
        self.logger.log("[Joined channel %s]" % channel)

    def privmsg(self, user, channel, msg):
        """Called when the bot gets any sort of message"""
        user = user.split("!", 1)[0]
        stamp = time.asctime(time.localtime(time.time()))
        self.logger.log("%s <%s> %s" % (stamp, user, msg))
        
        # Is this a /msg ?
        if channel == self.nickname:
            msg = "Thanks for contacting me personally."
            self.msg(user, msg)
            return
        
        # Otherwise it may be a message directed at me
        if msg.startswith(self.nickname + ":"):
            msg = "%s: I don't know what to do when you talk to me yet." % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

    def action(self, user, channel, msg):
        """Called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user,msg))

    def irc_NICK(self, prefix, params):
        """Called when a user changes their nick."""
        old = prefix.split("!")[0]
        new = params[0]
        self.logger.log(">>> %s is now known as %s" % (old, new))

    def alterCollidedNick(self, nickname):
        """Generate an altered version of a nick that caused a collision."""
        return nickname + '|stolen'


class LinkBotFactory(protocol.ClientFactory):
    """
    A factory for LinkBots.
    
    A new protocl instance will be created each time we connect to the server.
    """
    
    protocol = LinkBot
    
    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename
    
    def clientConnectionlost(self, connector, reason):
        """If disconnected, attempt a reconnect"""
        connector.connect()
    
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed: ", reason
        reactor.stop()


if __name__ == '__main__':
    # init logging
    log.startLogging(sys.stdout)
    
    # create factory protocol and application
    f = LinkBotFactory(sys.argv[1], sys.argv[2])
    
    # connect factory to host and port
    reactor.connectTCP("irc.oftc.net", 6667, f)
    
    # run bot
    reactor.run()

