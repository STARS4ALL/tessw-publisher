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
import os
import os.path
import argparse
import errno
import configparser as ConfigParser


# ---------------
# Twisted imports
# ---------------


#--------------
# local imports
# -------------

import tessw.utils

from tessw import CONFIG_FILE, VERSION_STRING, TESSW

# ----------------
# Module constants
# ----------------





# -----------------------
# Module global variables
# -----------------------


# ------------------------
# Module Utility Functions
# ------------------------



def cmdline():
    '''
    Create and parse the command line for the tess package.
    Minimal options are passed in the command line.
    The rest goes into the config file.
    '''
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser = argparse.ArgumentParser(prog=name)
    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, VERSION_STRING))
    parser.add_argument('-k' , '--console', action='store_true', help='log to console')
    parser.add_argument('--config',   type=str, default=CONFIG_FILE, action='store', metavar='<config file>', help='detailed configuration file')
    parser.add_argument('--log-file', type=str, default=None,    action='store', metavar='<log file>', help='log file path')
    return parser.parse_args()




def loadCmdLine(cmdline_options):
    '''
    Load options from the command line object formed
    Returns a dictionary
    '''
    options = {}
    options['global'] = {}
    options['global']['console']   = cmdline_options.console
    options['global']['config']    = cmdline_options.config
    options['global']['log_file']  = cmdline_options.log_file       
    return options


def loadCfgFile(path):
    '''
    Load options from configuration file whose path is given
    Returns a dictionary
    '''

    if path is None or not (os.path.exists(path)):
        raise IOError(errno.ENOENT,"No such file or directory", path)

    options = {}
    parser  = ConfigParser.RawConfigParser()
    # str is for case sensitive options
    #parser.optionxform = str
    parser.read(path)

    options['global'] = {}
    N = options['global']['nphotom'] = parser.getint("global","nphotom")
    options['global']['T']           = parser.getint("global","T")
    options['global']['log_level']   = parser.get("global","log_level")

    for i in range(1,N+1):
        section = 'phot'+ str(i)
        if not parser.has_section(section):
            raise Exception("Missing section " + section)
        options[section] = {}
        options[section]['old_firmware'] = parser.getboolean(section,"old_firmware")
        options[section]['mac_address']  = parser.get(section,"mac_address")
        options[section]['name']         = parser.get(section,"name")
        options[section]['zp']           = parser.getfloat(section,"zp")
        options[section]['endpoint']     = parser.get(section,"endpoint")
        options[section]['log_level']    = parser.get(section,"log_level")
        options[section]['log_messages'] = parser.get(section,"log_messages")
    
    options['mqtt'] = {}
    options['mqtt']['broker']        = parser.get("mqtt","broker")
    options['mqtt']['username']      = parser.get("mqtt","username")
    options['mqtt']['password']      = parser.get("mqtt","password")
    options['mqtt']['keepalive']     = parser.getint("mqtt","keepalive")
    options['mqtt']['log_level']     = parser.get("mqtt","log_level")
    options['mqtt']['log_messages']  = parser.get("mqtt","log_messages")

    return options


def read_options():
    # Read the command line arguments and config file options
    options = {}
    cmdline_obj  = cmdline()
    cmdline_opts = loadCmdLine(cmdline_obj)
    config_file  =  cmdline_obj.config
    
    file_opts  = loadCfgFile(config_file)
    for key in file_opts.keys():
        options[key] = tessw.utils.merge_two_dicts(file_opts[key], cmdline_opts.get(key,{}))
    
    return options, cmdline_obj

__all__ = ["VERSION_STRING", "read_options"]
