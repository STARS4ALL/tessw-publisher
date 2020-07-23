# ----------------------------------------------------------------------
# Copyright (c) 2014 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

from __future__ import division, absolute_import

import re
import datetime
import json

# ---------------
# Twisted imports
# ---------------

from twisted.logger               import Logger
from twisted.internet             import reactor
from twisted.internet.protocol    import Factory

from twisted.protocols.basic      import LineOnlyReceiver
from twisted.internet.interfaces  import IPushProducer, IConsumer
from zope.interface               import implementer

#--------------
# local imports
# -------------

import tessw.utils

# ----------------
# Module constants
# ----------------


# <fH 04606><tA +2987><tO +2481><mZ -0000>
# Unsolicited Responses Patterns
UNSOLICITED_RESPONSES = (
    {
        'name'    : 'Hz reading',
        'pattern' : r'^<fH([ +]\d{5})><tA ([+-]\d{4})><tO ([+-]\d{4})><mZ ([+-]\d{4})>',       
    },
    {
        'name'    : 'mHz reading',
        'pattern' : r'^<fm([ +]\d{5})><tA ([+-]\d{4})><tO ([+-]\d{4})><mZ ([+-]\d{4})>',       
    },
)


UNSOLICITED_PATTERNS = [ re.compile(ur['pattern']) for ur in UNSOLICITED_RESPONSES ]


# -----------------------
# Module global variables
# -----------------------


# ----------
# Exceptions
# ----------


# -------
# Classes
# -------


class TESSProtocolFactory(Factory):
    
    def __init__(self, namespace, old_firmware):
        self.namespace = namespace
        self.log = Logger(namespace=namespace)
        self.old_firmware = old_firmware

    def buildProtocol(self, addr):
        self.log.debug('Factory: Connected.')
        if self.old_firmware:
            self.log.info('Factory: Building old protocol.')
            return TESSProtocolOld(self.namespace)
        else:
            self.log.info('Factory: Building new protocol.')
            return TESSProtocolNew(self.namespace)


@implementer(IPushProducer)
class TESSProtocolBase(LineOnlyReceiver):

    # So that we can patch it in tests with Clock.callLater ...
    callLater = reactor.callLater

    # -------------------------
    # Twisted Line Receiver API
    # -------------------------

    def __init__(self, namespace):
        '''Sets the delimiter to the closihg parenthesis'''
        # LineOnlyReceiver.delimiter = b'\n'
        self.log       = Logger(namespace=namespace)
        self._consumer = None
        self._paused   = True
        self._stopped  = False


    def connectionMade(self):
        self.log.debug("connectionMade()")

    def connectionLost(self, reason):
        self.log.debug("connectionLost() {reason}", reason=reason)

    def lineReceived(self, line):
        now = datetime.datetime.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=0.5)
        line = line.decode('latin_1')  # from bytearray to string
        self.log.info("<== TESS-W [{l:02d}] {line}", l=len(line), line=line)
        handled, reading = self._handleUnsolicitedResponse(line, now)
        if handled:
            self._consumer.write(reading)
            self.log.debug("<== TESS-W : {reading}", reading=reading)
    
    # -----------------------
    # IPushProducer interface
    # -----------------------

    def stopProducing(self):
        """
        Stop producing data.
        """
        self._stopped     = False


    def pauseProducing(self):
        """
        Pause producing data.
        """
        self._paused    = True


    def resumeProducing(self):
        """
        Resume producing data.
        """
        self._paused    = False


    def registerConsumer(self, consumer):
        '''
        This is not really part of the IPushProducer interface
        '''
        self._consumer = IConsumer(consumer)



@implementer(IPushProducer)
class TESSProtocolOld(TESSProtocolBase):

       
    # --------------
    # Helper methods
    # --------------

    def _match_unsolicited(self, line):
        '''Returns matched command descriptor or None'''
        for regexp in UNSOLICITED_PATTERNS:
            matchobj = regexp.search(line)
            if matchobj:
                i = UNSOLICITED_PATTERNS.index(regexp)
                #self.log.debug("matched {pattern}", pattern=UNSOLICITED_RESPONSES[UNSOLICITED_PATTERNS.index(regexp)]['name'])
                return UNSOLICITED_RESPONSES[i], matchobj
        return None, None


    def _handleUnsolicitedResponse(self, line, tstamp):
        '''
        Handle unsolicited responses from tessw.
        Returns True if handled, False otherwise
        '''
        if self._paused or self._stopped:
            self.log.debug("Producer either paused({p}) or stopped({s})", p=self._paused, s=self._stopped)
            return False, None
        ur, matchobj = self._match_unsolicited(line)
        if not ur:
            return False, None
        reading = {}
        reading['tbox']   = float(matchobj.group(2))/100.0
        reading['tsky']   = float(matchobj.group(3))/100.0
        reading['zp']     = float(matchobj.group(4))/100.0
        reading['tstamp'] = tstamp
        if ur['name'] == 'Hz reading':
            reading['freq']   = float(matchobj.group(1))/1.0
            self.log.debug("Matched {name}", name=ur['name'])
        elif ur['name'] == 'mHz reading':
            reading['freq'] = float(matchobj.group(1))/1000.0
            self.log.debug("Matched {name}", name=ur['name'])
        else:
            return False, None
        return True, reading
        
        
#---------------------------------------------------------------------
# --------------------------------------------------------------------
# --------------------------------------------------------------------

@implementer(IPushProducer)
class TESSProtocolNew(TESSProtocolBase):

    
    # --------------
    # Helper methods
    # --------------


    def _handleUnsolicitedResponse(self, line, tstamp):
        '''
        Handle Unsolicted responses from zptess.
        Returns True if handled, False otherwise
        '''
        if self._paused or self._stopped:
            self.log.debug("Producer either paused({p}) or stopped({s})", p=self._paused, s=self._stopped)
            return False, None
        try:
            reading = json.loads(line)
        except Exception as e:
            return False, None
        else:
            if type(reading) != dict:
                return False, None
            reading['tstamp'] = tstamp
            return True, reading
        


__all__ = [
    "TESSProtocol",
    "TESSProtocolFactory",
]
