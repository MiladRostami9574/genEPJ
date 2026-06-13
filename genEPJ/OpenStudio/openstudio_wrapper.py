#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenStudio wrapper utilities used by genEPJ.

This module applies OpenStudio measures or workflows to temporary model
files and returns the modified model in genEPJ object-list format.
"""

from subprocess import call, check_call, Popen, PIPE
from os.path import isdir, isfile, join
from shutil import move, which
from tempfile import mkdtemp
from os import chdir, getcwd, getenv
from sys import path


path.append('../pylib')
from genEPJ_lib import combine_objects, get_IDF_objs_raw

openstudio_version="3.3.0+ad235ff36e"

log_openstudio_txt="LOGS_OpenStudio.txt"
ff=open(log_openstudio_txt, 'w')

def write_log(line):
    "Write details (`line`) to openstudio log file (`log_openstudio_txt`)."
    #ff.write(line+"\n")
    # TODO- add fancy formatting/colour
    ff.write(line.replace("**:", "**:\n  >")+"\n")

# Find openstudio installation
from os import environ, getenv
mk_bin='openstudio' # use short form
if which('openstudio'):
    #mk_bin='openstudio' # use short form
    mk_bin=which('openstudio') # use long form
    write_log("**ENVIRONMENT**: Found `openstudio' in PATH")
else:
    write_log("**ENVIRONMENT**: `openstudio' NOT in PATH")
    raise OSError("OpenStudio: Can't find `openstudio' in PATH")
#elif getenv('GEM_PATH'): # try to manually find openstudio bin
#    gem_path = environ['GEM_PATH']
#    mk_bin=join( gem_path, 'bin', 'openstudio')
#    write_log("**ENVIRONMENT**: Found `GEM_PATH' in PATH. Specifying `openstudio' executable manually")
## Last chance
#if (not which('openstudio') and (not  getenv('GEM_PATH'))):
#    home_path = environ['HOME']
#    gem_path = join( '.gem','ruby','2.6.0','bin')
#    mk_bin=join( gem_path, 'openstudio')
#    write_log("**ENVIRONMENT**: LAST RESORT- No executable OR `GEM_PATH' found in PATH. Specifying `GEM_PATH' and `openstudio' executable manually")


default_measures_dir="Measures"
default_workflow_dir="Workflows"
default_converter_rb="convert_file.rb"

if isdir( 'OpenStudio' ):
    measures_dir=join('OpenStudio', default_measures_dir)
    workflow_dir=join('OpenStudio', default_workflow_dir)
    converter_rb=join('OpenStudio', default_converter_rb)
    write_log("**TEMPLATES**: Found OpenStudio templates: {} and {}".format(measures_dir, workflow_dir))
elif isdir( default_measures_dir ):
    measures_dir=default_measures_dir
    workflow_dir=default_workflow_dir
    converter_rb=default_converter_rb
    write_log("**TEMPLATES**: Found OpenStudio templates: {} and {}".format(measures_dir, workflow_dir))
elif isdir( join('genEPJ', 'OpenStudio') ):
    measures_dir=join('genEPJ', 'OpenStudio', default_measures_dir)
    workflow_dir=join('genEPJ', 'OpenStudio', default_workflow_dir)
    converter_rb=join('genEPJ', 'OpenStudio', default_converter_rb)
    write_log("**TEMPLATES**: Found OpenStudio templates: {} and {}".format(measures_dir, workflow_dir))
#elif isdir( join('genEPJ', 'openstudio',nze_templ,'templates') ):
#    template_dirs=join('genEPJ', 'openstudio',nze_templ,'templates')
#    write_log("**TEMPLATES**: Found openstudio templates: {}".format(template_dirs))
#elif isdir( join(nze_templ,'templates') ):
#    template_dirs=join(nze_templ,'templates')
#    write_log("**TEMPLATES**: Found openstudio templates: {}".format(template_dirs))
else:
    write_log("**TEMPLATES**: NO OpenStudio templates found")
    raise OSError("openstudio: Can't find templates")

# Absolute PATHs: Fixes openstudio bug (wasn't running in sim/tmp-run- properly)
#template_dirs= join( getcwd(), template_dirs)
# TODO- update so this can be ported to windows
#template_dirs= join( "/home/sb/school_phd/research/coding/eplus_epJSON/genEPJ_pkg", template_dirs)
#if not isdir(template_dirs):
#    write_log("**TEMPLATES**: Templates found but absolute path non-existent")
#    raise OSError("openstudio: Can't find absolute path to HVAC templates")



# Ruby command with 'W0' to suppress warnings
ruby_cmd=which('ruby')+" -W0"

path.append('../pylib')

def _mycall(command):

    command = command.split(' ')
    return str( Popen(command, stdout=PIPE).communicate()[0]).replace('\n','')
    ### HACK: Linux/mac is a butterfly
    ## https://docs.python.org/2/library/sys.html#sys.platform (returns: win32, linux(2), cygwin, darwin, etc
    #if platform.startswith('win'):
    #    command = command.split(' ')
    #    return str( Popen(command, stdout=PIPE).communicate()[0]).replace('\n','')
    #else: # linux/mac
    #    #from pty import spawn # psuedo-tty
    #    ## openstudio/cli requires a TTY to read in options. Open one using pty.spawn()
    #    #g=open('openstudio_cmd.sh', 'w')
    #    #g.write("#!/usr/bin/env bash\n")
    #    #g.write(command+" &> openstudio_output.txt\n")
    #    #g.close()

    #    ##output=spawn(command)
    #    #check_call( "chmod +x openstudio_cmd.sh", shell=True )
    #    #output=spawn( "openstudio_cmd.sh" )

    #    return output

# SB TODO- refactor
def call_converter(myfile):
    """Convert `myfile` between IDF and OSM formats.

    Parameters:

    * `myfile`: String of file to be translated (IDF or OSM format)

    Returns:

    * `_file`: Name of new file created through OpenStudio translation (OSM or IDF format)
    """
    _file=""
    if 'osm' in myfile.lower():
        _file=myfile.replace('.osm', '.idf')
        _mycall( converter_rb + " --to-idf " + myfile )
        move(myfile, myfile.replace('.osm', '_convertbkup.osm') )
    elif 'idf' in myfile.lower():
        _file=myfile.replace('.idf', '.osm')
        _mycall( converter_rb + " --to-osm " + myfile )
        move(myfile, myfile.replace('.idf', '_convertbkup.idf') )
    return _file


# ASSUMED that measures/workflows specifies format IDF/OSM/JSON
def dispatch_openstudio(objs_all, args={}):
    """"Convert genEPJ style `obs_all` (if necessary) and apply provided measure/workflow file using OpenStudio. Convert back into genEPJ format and return modified object list.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `template`-  Either a OpenStudio measure (directory) or a workflow (file pointing to several measures)

    Returns:

    * `new_objs`: Modified genEPJ object list (Python `List`) using provided OpenStudio measure/workflow.
    """

    write_log("**Flow**: Entering `dispatch_openstudio' function")

    objs_all=get_IDF_objs_raw(objs_all)
    temp_dir=mkdtemp("_openstudio")


    # Payload is a OpenStudio Measure/Workflow in IDF/OSM/JSON format
    payload=args['template']

    if 'json' in payload.lower():
        suffix='.epjson'
    elif 'idf' in payload.lower():
        suffix='.idf'
    elif 'osm' in payload.lower():
        suffix='.osm'

    # Convert objs_all into genEPJ.idf/json (Assumed that appropriate obj config is passed)
    genEPJ_file=join(temp_dir, 'start'+suffix)
    new_file=join(temp_dir, 'postosm'+suffix)
    print("> Writing objs_all to '{}'".format(genEPJ_file))
    genEPJ_data=combine_objects(objs_all)
    with open(genEPJ_file, 'w') as f:
        f.write(genEPJ_data)
    write_log("**Flow**: Created IDF input file: {}".format(genEPJ_file))

    # Convert to OSM (if necessary
    if 'osm' in payload.lower() :
        genEPJ_file=call_converter(join( temp_dir, genEPJ_file))


# openstudio.exe measure --update /path/to/measure/
# openstudio.exe measure --compute_arguments /path/to/model.osm /path/to/measure/
# openstudio.exe measure --compute_arguments /path/to/model.idf /path/to/measure/
# openstudio.exe run --measures_only --workflow /path/to/workflow.osw

    # Make changes
    _cwd=getcwd()
    chdir(temp_dir)
    #_out= run([script, idf], capture_output=True)
    if   isdir(payload): # Is Measure
        cmd="openstudio measure --compute_arguments {} {}".format(genEPJ_file, payload)
    elif isfile(payload): # Is Workflow
        # TODO- update OR setup before starting
        # "weather_file": "srrl_2013_amy.epw",
        # "seed_file": "start.osm",
        cmd="openstudio run --measures_only --workflow {}".format(payload)
    else:
        print("Missing payload for Measure/Workflow")
        raise FileNotFoundError
    _out= _mycall( cmd )

    # Workflow or Measure?
#openstudio.exe measure --compute_arguments /path/to/model.osm /path/to/measure/

    # Convert back
    newidf_file=call_converter(join( temp_dir, genEPJ_file))
    new_objs=get_IDF_objs_raw(newidf_file)

    return new_objs


if __name__ == '__main__':
    pass
    print(measures_dir)
    print(workflow_dir)
    print(converter_rb)
    #call_converter("temp.osm")
    #call_converter("temp.idf")
    dispatch_openstudio("nomad_3RV96.idf", {'template': "Measures/OSM/WallIns"})
