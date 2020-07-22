# ----------------------------------------------------------------------
# Copyright (c) 2014 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

from __future__ import division, absolute_import

# ---------------
# Twisted imports
# ---------------

from twisted.logger         import Logger
from twisted.internet       import reactor, task
from twisted.internet.defer import inlineCallbacks,  DeferredList

#--------------
# local imports
# -------------

from tessw                    import VERSION_STRING, MQTT_SERVICE, PHOTOMETER_SERVICE, SUPVR_SERVICE
from tessw.logger             import setLogLevel
from tessw.service.reloadable import MultiService

# ----------------
# Module constants
# ----------------

# Service Logging namespace
NAMESPACE = 'supvr'

# -----------------------
# Module global variables
# -----------------------

log  = Logger(namespace=NAMESPACE)

class SupervisorService(MultiService):


    def __init__(self, options, **kargs):
        MultiService.__init__(self)
        setLogLevel(namespace=NAMESPACE, levelStr=options['log_level'])
        self.options    = options
        self.photometers = []   # Array of photometers
        self.task = None        # Periodic task to poll Photometers
        self.i = 0              # current photometer being sampled
        self._registryDone = False
        
    # -----------
    # Service API
    # -----------

    def startService(self):
        log.info('starting {name}', name=SUPVR_SERVICE)
        self.mqttService    = self.parent.getServiceNamed(MQTT_SERVICE)
        N = self.options['nphotom']
        for i in range(1, N+1):
            label = 'phot'+str(i)
            self.photometers.append(self.getServiceNamed(PHOTOMETER_SERVICE + ' ' + str(i)))
        super().startService()
        self.task = reactor.callLater(0, self.getInfo)


    @inlineCallbacks
    def reloadService(self, options):
        '''
        Reload service parameters
        '''
        log.warn("{version} reloading config", version=VERSION_STRING)
        try:
            options, cmdline_opts  = yield deferToThread(read_options)
        except Exception as e:
            log.error("Error trying to reload: {excp!s}", excp=e)
        else:
            log.warn("{version} config reloaded ok.", version=VERSION_STRING)
            self.options = options['global']
            setLogLevel(namespace=self.label,     levelStr=self.options['log_level'])
            setLogLevel(namespace=self.namespace, levelStr=self.options['log_messages'])
            yield super().reloadService(options=options)
            
    # --------------
    # Photometer API
    # --------------

    def numberOfPhotometers(self):
        return self.options['nphotom']

    def registryDone(self):
        self._registryDone = True

    def childStopped(self, child):
        log.warn("Will stop the reactor asap.")
        try:
            reactor.callLater(0, reactor.stop)
        except Exception as e:
            log.error("could not stop the reactor")


    def getInfo(self):
        '''Get registry info for all photometers'''
        log.info("Getting info from all photometers")
        N = self.options['nphotom']
        self.task = task.LoopingCall(self.poll)
        self.task.start(self.options['T']//N, now=False)
        dli = [photometer.getInfo() for photometer in self.photometers]
        for deferred in dli:
            deferred.addCallback(self._addInfo)
        dli = DeferredList(dli, consumeErrors=True)
        dli.addCallback(self._info_complete)
        self.kk = dli
        return dli


    def poll(self):
        i = self.i
        try:
            sample = self.photometers[i].buffer.getBuffer().popleft()   
        except IndexError as e:
            log.error("Photometer[{i}] {e}", e=e, i=i)
        else:
            # Take out uneeded information
            sample = self.photometers[i].curate(sample)
            log.info("Photometer[{i}] = {sample}", sample=sample, i=i)
            if self._registryDone:
                self.mqttService.readings_queue.put(sample)
            else:
                log.warn("Not yet registered. Ignoring sample from Photometer[{i}]",i=i)
        finally:
            self.i = (i + 1) % len(self.photometers)

    # --------------
    # Helper methods
    # --------------

    def _addInfo(self, photometer_info):
        log.info("Passing {name} photometer info to register queue", name=photometer_info['name'])
        self.mqttService.register_queue.put(photometer_info)

    def _info_complete(self, *args):
        log.info("Finished getting info from all photometers")


