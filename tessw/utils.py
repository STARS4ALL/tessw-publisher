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
import datetime
import argparse
import re

# ---------------
# Twisted imports
# ---------------

#--------------
# local imports
# -------------

from tessw import PORT_PREFIX

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# setSystemTime function variable
setSystemTime = None

# ------------------------
# Module Utility Functions
# ------------------------

def merge_two_dicts(d1, d2):
    '''Valid for Python 2 & Python 3'''
    merged = d1.copy()   # start with d1 keys and values
    merged.update(d2)    # modifies merged with d2 keys and values & returns None
    return merged


def chop(value, sep=None):
    '''Chop a list of strings, separated by sep and 
    strips individual string items from leading and trailing blanks'''
    chopped = [ elem.strip() for elem in value.split(sep) ]
    if len(chopped) == 1 and chopped[0] == '':
        chopped = []
    return chopped



__all__ = [
    "chop",
    "merge_two_dicts"
]
