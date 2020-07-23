# ----------------------------------------------------------------------
# Copyright (c) 2014 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

from __future__ import division, absolute_import

import sys
import math

from collections import deque

# ---------------
# Twisted imports
# ---------------

from twisted.logger               import Logger
from twisted.internet             import reactor, task, defer
from twisted.internet.defer       import inlineCallbacks, returnValue
from twisted.internet.serialport  import SerialPort
from twisted.internet.interfaces  import IPushProducer, IPullProducer, IConsumer
from zope.interface               import implementer

#--------------
# local imports
# -------------

from tessw                    import TESSW
from tessw.logger             import setLogLevel
from tessw.utils              import chop
from tessw.config             import read_options
from tessw.service.reloadable import Service


# -----------------------
# Module global variables
# -----------------------


# ----------
# Exceptions
# ----------



# -------
# Classes
# -------

@implementer(IConsumer)
class CircularBuffer(object):

    def __init__(self, size, log):
        self._buffer = deque([], size)
        self._producer = None
        self._push     = None
        self.log       = log

    # -------------------
    # IConsumer interface
    # -------------------

    def registerProducer(self, producer, streaming):
        if streaming:
            self._producer = IPushProducer(producer)
        else:
            raise ValueError("IPullProducer not supported")
        producer.registerConsumer(self) # So the producer knows who to talk to
        producer.resumeProducing()

    def unregisterProducer(self):
        self._producer.stopProducing()
        self._producer = None

    def write(self, data):
        self._buffer.append(data)

    # -------------------
    # buffer API
    # -------------------

    def getBuffer(self):
        return self._buffer

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class PhotometerService(Service):

    BUFFER_SIZE = 1

    def __init__(self, options, label):

        self.options   = options
        self.label     = label
        self.namespace = self.label.upper()
        setLogLevel(namespace=self.namespace,  levelStr=options['log_messages'])
        setLogLevel(namespace=self.label,      levelStr=options['log_level'])
        self.log       = Logger(namespace=self.label)
        self.factory   = self.buildFactory()
        self.protocol  = None
        self.serport   = None
        self.buffer    = CircularBuffer(self.BUFFER_SIZE, self.log)
        self.counter   = 0
        # Handling of Asynchronous getInfo()
        self.info = None
        self.info_deferred = None
        if options['old_firmware']:
            self.info = {
                'name'  : self.options['name'],
                'mac'   : self.options['mac_address'],
                'calib' : self.options['zp'],
                'rev'   : 2,
                }
        
        # Serial port Handling
        parts = chop(self.options['endpoint'], sep=':')
        if parts[0] != 'serial':
            self.log.critical("Incorrect endpoint type {ep}, should be 'serial'", ep=parts[0])
            raise NotImplementedError
          
    
    def startService(self):
        '''
        Starts the photometer service listens to a TESS
        Although it is technically a synchronous operation, it works well
        with inline callbacks
        '''
        self.log.info("starting {name}", name=self.name)
        self.connect()
       


    def stopService(self):
        self.log.warn("stopping {name}", name=self.name)
        self.protocol.transport.loseConnection()
        self.protocol = None
        self.serport  = None
        #self.parent.childStopped(self)
        return defer.succeed(None)

    #---------------------
    # Extended Service API
    # --------------------

    @inlineCallbacks
    def reloadService(self, new_options):
        '''
        Reload configuration.
        Returns a Deferred
        '''
        options = options[self.label]
        setLogLevel(namespace=self.label,     levelStr=options['log_level'])
        setLogLevel(namespace=self.namespace, levelStr=options['log_messages'])
        self.options = options
        return defer.succeed(None)
      
    # -----------------------
    # Specific photometer API
    # -----------------------

    def handleInfo(self, reading):
        if self.info_deferred is not None:
            self.info = {
                'name'  : reading.get('name', None),
                'calib' : reading.get('ZP', None),
                'mac'   : self.options['mac_address'],
                'rev'   : 2,
            }
            self.log.info("Photometer Info: {info}", info=self.info)
            self.info_deferred.callback(self.info)
            self.info_deferred = None


    def curate(self, reading):
        '''Readings ready for MQTT Tx according to our wire protocol'''
        reading['seq'] = self.counter
        self.counter += 1
        self.last_tstamp = reading.pop('tstamp', None)
        if self.options['old_firmware']:
            reading['mag']  = round(self.options['zp'] - 2.5*math.log10(reading['freq']),2)
            reading['rev']  = 2
            reading['name'] = self.options['name']
            reading['alt']  = 0.0
            reading['azi']  = 0.0
            reading['wdBm'] = 0
            reading.pop('zp', None)
        else:
            reading['mag']  = round(reading['ZP'] - 2.5*math.log10(reading['freq']),2)
            self.info = {
                'name'  : reading.get('name', None),
                'calib' : reading.get('ZP', None),
                'mac'   : self.options['mac_address'],
                'rev'   : 2,
            }
            reading.pop('udp', None)
            reading.pop('ain', None)
            reading.pop('ZP',  None)
        return reading

    
    def getInfo(self):
        '''Asynchronous operations'''
        if not self.options['old_firmware'] and self.info is None:
            deferred = defer.Deferred()
            deferred.addTimeout(60, reactor)
            self.info_deferred = deferred
        else:
            self.log.info("Photometer Info: {info}", info=self.info)
            deferred = defer.succeed(self.info)
        return deferred

    # --------------
    # Helper methods
    # ---------------

    def connect(self):
        parts = chop(self.options['endpoint'], sep=':')
        endpoint = parts[1:]
        self.protocol = self.factory.buildProtocol(0)
        try:
            self.serport  = SerialPort(self.protocol, endpoint[0], reactor, baudrate=endpoint[1])
        except Exception as e:
            self.log.error("{excp}",excp=e)
            self.protocol = None
        else:
            self.gotProtocol(self.protocol)
            self.log.info("Using serial port {tty} @ {baud} bps", tty=endpoint[0], baud=endpoint[1])
    
    
    def buildFactory(self):
        self.log.debug("Choosing a {model} factory", model=TESSW)
        import tessw.tessw
        factory = tessw.tessw.TESSProtocolFactory(self.namespace, self.options['old_firmware'])
        return factory


    def gotProtocol(self, protocol):
        self.log.debug("got protocol")
        self.buffer.registerProducer(protocol, True)
        self.protocol  = protocol


__all__ = [
    "PhotometerService",
]
