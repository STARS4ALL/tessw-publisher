# ----------------------------------------------------------------------
# Copyright (c) 2014 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


#--------------------
# System wide imports
# -------------------

from __future__ import division, absolute_import

import os
import os.path
import sys

# ---------------
# Twisted imports
# ---------------

from twisted  import __version__ as __twisted_version__

#--------------
# local imports
# -------------

from ._version import get_versions

# ----------------
# Module constants
# ----------------

__version__ = get_versions()['version']

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

VERSION_STRING = "{0} on Twisted {1}, Python {2}.{3}".format(__version__, __twisted_version__, sys.version_info.major, sys.version_info.minor)

PHOTOMETER_SERVICE = 'Photometer Service'
MQTT_SERVICE       = 'MQTT Service'
SUPVR_SERVICE      = 'Supervisor Service'

TSTAMP_FORMAT      = "%Y-%m-%dT%H:%M:%SZ"

# Photoemter models
TESSW = "TESS-W"


# Default config file path
if os.name == "posix":
    CONFIG_FILE = os.path.join("/", "etc", "tessw", "config.ini")
    PORT_PREFIX = "/dev/ttyUSB"
else:
    print("ERROR: unsupported OS {name}".format(name = os.name))
    sys.exit(1)
 
# -----------------------
# Module global variables
# -----------------------

del get_versions
