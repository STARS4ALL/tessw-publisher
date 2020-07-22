# ----------------------------------------------------------------------
# Copyright (c) 2014 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

from __future__ import division, absolute_import

import json
import platform

# ---------------
# Twisted imports
# ---------------

from twisted.logger               import Logger
from twisted.internet             import reactor, task
from twisted.internet.defer       import inlineCallbacks, DeferredQueue, DeferredList
from twisted.internet.endpoints   import clientFromString
from twisted.application.internet import ClientService, backoffPolicy

from mqtt.error          import MQTTStateError
from mqtt.client.factory import MQTTFactory

#--------------
# local imports
# -------------

from tessw.logger import setLogLevel
from tessw        import TOPIC_ROOT, SUPVR_SERVICE

# ----------------
# Module constants
# ----------------

HOSTNAME = platform.uname()[1]

# Reconencting Service. Default backoff policy parameters

INITIAL_DELAY = 4   # seconds
FACTOR        = 2
MAX_DELAY     = 600 # seconds

# Service Logging namespace
NAMESPACE = 'mqttS'

# MQTT Protocol logging namespace
PROTOCOL_NAMESPACE = 'mqtt'

# -----------------------
# Module global variables
# -----------------------

log  = Logger(namespace=NAMESPACE)

class MQTTService(ClientService):

    # Default publish QoS
    
    QoS = 0
    

    def __init__(self, options, **kargs):
        self.options = options
        setLogLevel(namespace=NAMESPACE, levelStr=options['log_level'])
        setLogLevel(namespace=PROTOCOL_NAMESPACE, levelStr=options['log_messages'])
        self.factory     = MQTTFactory(profile=MQTTFactory.PUBLISHER)
        self.endpoint    = clientFromString(reactor, self.options['broker'])
        self.task = None
        if self.options['username'] == "":
            self.options['username'] = None
            self.options['password'] = None
        ClientService.__init__(self, self.endpoint, self.factory, 
            retryPolicy=backoffPolicy(initialDelay=INITIAL_DELAY, factor=FACTOR, maxDelay=MAX_DELAY))
        self.readings_queue = DeferredQueue()
        self.register_queue = DeferredQueue()
    
    # -----------
    # Service API
    # -----------
    
    def startService(self):
        log.info("starting MQTT Client Service")
        self.whenConnected().addCallback(self.connectToBroker)
        super().startService()


    @inlineCallbacks
    def stopService(self):
        try:
            yield ClientService.stopService(self)
        except Exception as e:
            log.failure("Exception {excp!s}", excp=e)
            reactor.stop()


    @inlineCallbacks
    def reloadService(self, options):
        setLogLevel(namespace=NAMESPACE, levelStr=options['log_level'])
        setLogLevel(namespace=PROTOCOL_NAMESPACE, levelStr=options['log_messages'])
        log.info("new log level is {lvl}", lvl=options['log_level'])
        self.options = options
      

    # -------------
    # log stats API
    # -------------


    # --------------
    # Helper methods
    # ---------------
   
    @inlineCallbacks
    def connectToBroker(self, protocol):
        '''
        Connect to MQTT broker
        '''
        self.protocol                 = protocol
        self.protocol.onPublish       = self.publish
        self.protocol.onDisconnection = self.onDisconnection
        self.protocol.setWindowSize(3)

        try:
            yield self.protocol.connect("tessw-publisher" + '@' + HOSTNAME, 
                username=self.options['username'], password=self.options['password'], 
                keepalive=self.options['keepalive'])
        except Exception as e:
            log.failure("Connecting to {broker} raised {excp!s}", 
               broker=self.options['broker'], excp=e)
        else:
            log.info("Connected to {broker}", broker=self.options['broker'])
            yield self.register()


    def onDisconnection(self, reason):
        '''
        Disconenction handler.
        Tells ClientService what to do when the connection is lost
        '''
        log.warn("tessw-publisher lost connection with its MQTT broker")
        self.task.cancel()
        self.task = None
        self.whenConnected().addCallback(self.connectToBroker)

  
    @inlineCallbacks
    def register(self):
        log.info("Entering Registering Phase")
        supvrService = self.parent.getServiceNamed(SUPVR_SERVICE)
        N = supvrService.numberOfPhotometers()
        for i in range(0,N):
            info = yield self.register_queue.get()
            msg = json.dumps(info)
            topic = "{0}/{1}".format(TOPIC_ROOT, "register")
            yield self.protocol.publish(topic=topic, qos=self.QoS, message=msg)
        reactor.callLater(0, self.publish)
        supvrService.registryDone()


    @inlineCallbacks
    def publish(self):
        log.info("Entering Data Publishing Phase")
        while True:
            try:
                reading = yield self.readings_queue.get()
                topic = "{0}/{1}/{2}".format(TOPIC_ROOT, reading['name'], "reading")
                msg = json.dumps(reading)
                yield self.protocol.publish(topic=topic, qos=self.QoS, message=msg)
            except MQTTStateError as e:
                log.error("{excp}",excp=e)
            except Exception as e:
                log.failure("Error when publishing: {excp!s}",excp=e)
            else:
                pass

    # --------------
    # Helper methods
    # --------------
