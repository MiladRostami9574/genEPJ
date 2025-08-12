#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"Wrapper to use OpenStudio CLI ([link](https://nrel.github.io/OpenStudio-user-documentation/reference/command_line_interface/)) inside of genEPJ."

# Steps
# * fn: apply measure
# openstudio.exe measure --update /path/to/measure/
# openstudio.exe measure --compute_arguments /path/to/model.osm /path/to/measure/
# openstudio.exe measure --compute_arguments /path/to/model.idf /path/to/measure/
# * fn: apply workflow: The -m or --measures_only switch runs the OpenStudio Model and EnergyPlus Measures but does not run the EnergyPlus simulation or OpenStudio Reporting Measures in an OSW file:
# openstudio.exe run --measures_only --workflow /path/to/workflow.osw

# SB- Need to write the following in JSON
#  "seed_file": "baseline.osm",
#  "weather_file": "USA_CO_Golden-NREL.724666_TMY3.epw",

from subprocess import call, run, check_call, Popen, PIPE, DEVNULL
from os.path import isfile, isdir, join, getsize, basename, splitext, dirname
from shutil import which, move, copytree, copy
from tempfile import mkstemp, mkdtemp
from os import system, getcwd, environ, remove
from sys import platform, path # win/linux?

from os import system, getcwd, environ, getenv, chdir, getcwd

path.append('../pylib')
from genEPJ_lib import open_IDF_file, get_IDF_objs_raw, combine_objects, get_obj_abstract, get_eplus_version, get_obj_type, write_file

# TODO- get from PATH using "openstudio --version"
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

#path.append('pylib')
path.append('../pylib')
from genEPJ_lib import open_IDF_file, dos2unix, get_IDF_objs_raw, combine_objects, _mystrip, recursive_strip, trim_comments, get_obj_abstract

#openstudio convert_file.rb --to-idf temp.osm
#openstudio convert_file.rb --to-osm temp.idf

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
    """"Convert `myfile` to/from IDF/OSM (OpenStudio format)

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

#def _count_lines(myfile): return sum(1 for line in open(myfile))
#
#
#def run_openstudio(myfile, payload, ismeasure=True):
#    "Run openstudio on the provided file. Write steps to a logfile. Return the created openstudio output (`outputfile`)."
#
#    # Given a dictionary (epJSON) or list (genIDF), swap to the alternative format and return a list or dictionary
#    outputfile=mkstemp(suffix='_tempopenstudio.idf')[1]
#    print("Creating openstudio temp output file: {}".format(outputfile))
#    #write_file(data, tempfnm)
#
#    cmd='{ruby} {openstudio} template-compose --output {output} --dirs {mktemp}  {root}'.format(ruby=ruby_cmd, openstudio=mk_bin, output=outputfile, mktemp=template_dirs, root=root )
#    print('> '+cmd)
#    write_log("**CMD**: `{}'".format(cmd))
#
#    # Quality assurance
#    write_log("**QA**: #lines in provided file: {} ({})".format( _count_lines(myfile), myfile ))
#
#    call_output=_mycall(cmd)
#    #call_output=call(cmd, shell=True)
#    #call_output=check_call(cmd, shell=True)
#    write_log("**QA**: `openstudio' subprocess returned `{}'".format(call_output) )
#
#    # QA continued... post cmd execution
#    write_log("**QA**: #lines in openstudio output (b4 dos2unix): {}".format( _count_lines(outputfile), outputfile ))
#
#    if which('dos2unix'):
#        print('>Converting openstudio output to Unix file extensions')
#        #call('dos2unix {}'.format( outputfile ), shell=True)
#        call( ['dos2unix', outputfile] )
#        # QA continued... post unix2dos execution
#        write_log("**QA**: `dos2unix' in PATH. #lines in openstudio output (post dos2unix): {}".format( _count_lines(outputfile), outputfile ))
#    else:
#        write_log("**QA**: `dos2unix' in not found PATH")
#
#    if isfile(outputfile) and _count_lines(outputfile)>0 :
#        print(">openstudio was successful")
#        write_log("**QA**: `openstudio' was sucessful")
#        return outputfile
#    elif isfile(outputfile) and _count_lines(outputfile)==0 :
#        print(">openstudio was NOT successful. Output file created but with NO content.")
#        write_log("**QA**: `openstudio' was NOT sucessful. ZERO lines created in `{}'".format(outputfile) )
#        #system( cmd ) # Try again
#        #write_log("**QA**: TRY AGAIN #lines in openstudio output: {}".format( _count_lines(outputfile), outputfile ))
#        return outputfile
#    else:
#        print(">openstudio failed")
#        write_log("**QA**: `openstudio' FAILED")
#        #return None
#        raise ValueError("openstudio"+data)
#
#
#    return False



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
    #run_openstudio(1)
    #dispatch_openstudio([],{})
    print(measures_dir)
    print(workflow_dir)
    print(converter_rb)
    #call_converter("temp.osm")
    #call_converter("temp.idf")
    dispatch_openstudio("nomad_3RV96.idf", {'template': "Measures/OSM/WallIns"})
