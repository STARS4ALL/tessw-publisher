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

from twisted.logger              import Logger
from twisted.internet            import reactor
from twisted.application.service import IService

#--------------
# local imports
# -------------

from tessw             import VERSION_STRING
from tessw.application import application
from tessw.logger      import sysLogInfo

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = Logger(namespace='global')

# ------------------------
# Module Utility Functions
# ------------------------

# ====
# Main
# ====

serv = IService(application)

log.info('{program} {version}', program=serv.name, version=VERSION_STRING) 
sysLogInfo("Starting {0} {1} Linux service".format(serv.name, VERSION_STRING ))
serv.startService()
reactor.run()
sysLogInfo("{0} {1} Linux service stopped".format(serv.name, VERSION_STRING))
