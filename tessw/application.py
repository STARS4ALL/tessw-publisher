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

#from twisted.application.service import IServiceCollection, Application
from twisted.application.service import IServiceCollection


#--------------
# local imports
# -------------

from tessw                    import MQTT_SERVICE, SUPVR_SERVICE, PHOTOMETER_SERVICE
from tessw.logger             import startLogging
from tessw.config             import read_options
from tessw.supervisor         import SupervisorService
from tessw.photometer         import PhotometerService
from tessw.mqttservice        import MQTTService
from tessw.service.reloadable import Application


# ====
# Main
# ====

options, cmdline_opts = read_options()
startLogging(console=cmdline_opts.console, filepath=cmdline_opts.log_file)

# ------------------------------------------------
# Assemble application from its service components
# ------------------------------------------------

application = Application("tessw")
serviceCollection = IServiceCollection(application)

supvrService = SupervisorService(options['global'])
supvrService.setName(SUPVR_SERVICE)
supvrService.setServiceParent(serviceCollection)

mqttService = MQTTService(options['mqtt'])
mqttService.setName(MQTT_SERVICE)
mqttService.setServiceParent(serviceCollection)

# All Photometers under the Supewrvisor Service
N = options['global']['nphotom']
for i in range(1, N+1):
    label = 'phot'+str(i)
    tesswService = PhotometerService(options[label], label)
    tesswService.setName(PHOTOMETER_SERVICE + ' ' + str(i))
    tesswService.setServiceParent(supvrService)


__all__ = [ "application" ]