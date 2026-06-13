#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper utilities for integrating Modelkit workflows into genEPJ.

This module prepares Modelkit inputs, runs Modelkit, and converts
the resulting output back into a genEPJ-compatible object list.
"""
from subprocess import call, run, check_call, Popen, PIPE, DEVNULL
from os.path import isfile, isdir, join, getsize, basename, splitext, dirname
from shutil import which
from tempfile import mkstemp
from os import system, getcwd, environ
from sys import platform, path
import re

from string import Template

modelkit_version = "0.8.0"

log_modelkit_txt = "LOGS_Modelkit.txt"
ff = open(log_modelkit_txt, 'w')

def write_log(line):
    """Write a line to the Modelkit log file."""
    #ff.write(line+"\n")
    ff.write(line.replace("**:", "**:\n  >")+"\n")

# Find Modelkit installation
from os import environ, getenv
mk_bin='modelkit' # use short form
if which('modelkit'):
    #mk_bin='modelkit' # use short form
    mk_bin=which('modelkit') # use long form
    write_log("**ENVIRONMENT**: Found `modelkit' in PATH")
elif getenv('GEM_PATH'): # try to manually find Modelkit bin
    gem_path = environ['GEM_PATH']
    mk_bin=join( gem_path, 'bin', 'modelkit')
    write_log("**ENVIRONMENT**: Found `GEM_PATH' in PATH. Specifying `modelkit' executable manually")
# Last chance
if (not which('modelkit') and (not  getenv('GEM_PATH'))):
    home_path = environ['HOME']
    gem_path = join( '.gem','ruby','2.6.0','bin')
    mk_bin=join( gem_path, 'modelkit')
    write_log("**ENVIRONMENT**: LAST RESORT- No executable OR `GEM_PATH' found in PATH. Specifying `GEM_PATH' and `modelkit' executable manually")

# ModelKit TEMPLATES specific
#root_template='root_template.pxt'
#root_template=join('Modelkit', 'root_vav.pxt')

try:
    eplus_dir = environ['ENERGYPLUS_DIR']
    mj,md,mn=eplus_dir.split('-')[1:]
    if (int( mj ) >= 9 and int( md )>=3) or (int( mj ) >= 10) :
        nze_templ='net-zero-templatesv9'
    else:
        nze_templ='net-zero-templates'
except:
    nze_templ='net-zero-templates'

if isdir( join('Modelkit',nze_templ,'templates') ):
    template_dirs=join('Modelkit',nze_templ,'templates')
    write_log("**TEMPLATES**: Found Modelkit templates: {}".format(template_dirs))
elif isdir( join('genEPJ', 'Modelkit',nze_templ,'templates') ):
    template_dirs=join('genEPJ', 'Modelkit',nze_templ,'templates')
    write_log("**TEMPLATES**: Found Modelkit templates: {}".format(template_dirs))
elif isdir( join(nze_templ,'templates') ):
    template_dirs=join(nze_templ,'templates')
    write_log("**TEMPLATES**: Found Modelkit templates: {}".format(template_dirs))
else:
    write_log("**TEMPLATES**: NO Modelkit templates found")
    raise OSError("Modelkit: Can't find HVAC templates")

# Absolute PATHs: Fixes modelkit bug (wasn't running in sim/tmp-run- properly)
template_dirs= join( getcwd(), template_dirs)
#template_dirs= join( "/home/sb/school_phd/research/coding/eplus_epJSON/genEPJ_pkg", template_dirs)
if not isdir(template_dirs):
    write_log("**TEMPLATES**: Templates found but absolute path non-existent")
    raise OSError("Modelkit: Can't find absolute path to HVAC templates")

# Ruby command with 'W0' to suppress warnings
ruby_cmd=which('ruby')+" -W0"

#path.append('pylib')
path.append('../pylib')
from genEPJ_lib import open_IDF_file, dos2unix, get_IDF_objs_raw, combine_objects, _mystrip, recursive_strip, trim_comments, get_obj_abstract

#def mystrip(mytxt): return mytxt.strip(' ').strip('\n').strip('\r')
#
#def recursive_strip(myobj):
#    not_converged=True
#    while not_converged:
#        myobj=mystrip(myobj)
#        if myobj==mystrip(myobj):
#            not_converged=False
#        else:
#            not_converged=True
#    return myobj

