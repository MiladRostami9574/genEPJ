#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"Various helper functions that are not specific to manipulations in EnergyPlus (`generate_EPJ.py`) or Templates (template{r,s}*)"

from time import time
from os.path import isfile, isdir, join, getsize, basename, splitext, dirname
from os import environ, mkdir

from shutil import copyfile, move, rmtree

from time import sleep
#from math import tan, atan, pi, sqrt
from math import atan
from random import randint
from numpy import array, abs, matrix, cos, sin, tan, arctan, sqrt, dot, loadtxt, average, pi, floor

# NaN depreciated as of NumPy 1.20
try:
    from numpy import nan as NaN
except ImportError:
    from numpy import NaN
# Shapely: Calc area of polygons, Check if Point inside a given Polygon
#from shapely.geometry import Point, Polygon
from collections import deque
from glob import glob

from subprocess import call, Popen, PIPE

# Libraries to process epJSON
import json
from collections import OrderedDict #Maintain order of modfied JSON to same as source JSON
from pathlib import Path

# tempfile to process EPPY
import tempfile

# Check for runenergyplus
from shutil import which

import re

#if to_file==None and fr_file==None:
#    raise ValueError("Must specify reference and proposed models. Use generate_IDF.py -h")

# SB: REGEX doesnt match first line without a '\n'. Ex 'Version,8.1;\n\n'
# pre 2022
#myre = re.compile(r'[\n]*[\w\t\s\d\/.{}\(\)\[\]+,\'\n%=><#*:!@-]+;[ \t\w\d\/.{}\[\]\(\)%=><#+,:\?!@-]*')

## post 2022
# Goal: grab an entire IDF object and store as a string
pattern = """
[\n]*                                     # White space at start of object (if any)
[\w\t\s\d\/.{}\(\)\[\]+,\'\n%=><#*:!@&-]+; # Grab ALL content of object (and around object) with comments (!-/!)
[ \t\w\d\/.{}\[\]\(\)%=><#+,:\?!@-]*      # Grab trailing comments around object (if any)
"""
myre = re.compile(pattern, re.VERBOSE)

# REGEX for rounding numbers
numre = re.compile(r'[-]*[\d]+\.[\deE-]{6,}')
# SB: Don't round numbers with e^N or E^N
#numre = re.compile(r'[-]*[\d]+\.[\d-]{6,}')


def rad2deg(myrad):
    "Convert radians to degrees"
    return myrad*180./pi
def deg2rad(mydeg):
    "Convert degrees to radians"
    return mydeg*pi/180.

def zeroIfNone(myval):
    "Return `0` if supplied `myval` is type `None`, else return supplied value."
    if myval==None: return 0
    else: return myval

def roundNumbers(txtdat):
    "Round numbers found in genEPJ object. Round to nearest six decimals. Fixes poor practices found in OpenStudio (up to 15 decimals)."
    nums=numre.findall(txtdat)
    do_rnd=True
    for n in nums:
        try:
            # SB: Test to ensure small exponents arent rounded (less than 8 decimals)
            if 'e' in n.lower():
                num_exp= abs( float( n.lower().split('e')[1] ) )
                if num_exp<8 :
                    do_rnd=False
            if do_rnd:
                # %.5f: Was erasing some HVAC data. Better to go to 6 sigfigs
                #txtdat=txtdat.replace(n,'%.5f'%(float(n)))
                #print('roundNumbers: Rounding %s to %s'%(mkcolor(n,'yellow'), mkcolor('%.5f'%(float(n)),'green')))
                # SB: Remove '-'  if -0.000 == 0.000
                n_orig=n
                if ( (float( '%.6f'%(float(n))) == abs(float( '%.6f'%(float(n))))) and (n[0] == '-') ):
                    print("Found neg number which can be rounded", n)
                    n=n.replace('-','',1) # Replace first negative sign
                txtdat=txtdat.replace(n_orig,'%.6f'%(float(n)))
            else: # Flag found: Dont round this number
                txtdat=txtdat.replace(n,n)
        except ValueError: # Catches: 90-1, 189-1, etc
            txtdat=txtdat.replace(n,n)
    return txtdat

def join_lists(a,b):
    "Join `Lists` (a,b) together and return merged list."
    c=[]
    c.extend(a)
    c.extend(b)
    return c

def removeWhiteTrailSpaces(txtdat):
    "Remove trailing spaces from provided text blob. Substitute and return modified text blob."
    r = re.compile(r"\s+$", re.MULTILINE)
    return r.sub("", txtdat)

def rotate2D(theta):
    "Return a rotation matrix for angle, theta"
    return matrix([[cos(theta), -sin(theta)],
                   [sin(theta),  cos(theta)],])

def mkmatrix(a,b):
    "Convert coordinates (a,b) into a matrix."
    mat= matrix([a, b])
    return mat.transpose()

def cross3D(a, b):
    "Perform a cross product multiplication on a,b coordinates."
    c = [a[1]*b[2] - a[2]*b[1],
         a[2]*b[0] - a[0]*b[2],
         a[0]*b[1] - a[1]*b[0]]
    return array(c)

def len3D(a):
    "Return length of vector."
    return sqrt( a[0]**2 + a[1]**2 + a[2]**2 )

def norm3D(a):
    "Normalized length of vector a."
    return a/len3D(a)

# NOTE- mark for deletion
def adv_nl_split(mystr):
    "Advanced newline split function (Windows/Unix)."
    lines=mystr.split('\n')
    if len(lines)<1 :
        return mystr.split('\r')
    else: return lines

textColors = {
    'blue' : '\033[94m',
    'green' : '\033[92m',
    'black': '\033[95m',
    'yellow': '\033[93m',
    'red': '\033[91m',
    'default': '\033[0m',
    }

def printc(s,color='default'):
    "Print function but with colour (to Linux commandline)"
    print(textColors[color] + s + textColors['default'])

def mkcolor(mytxt,color='default'):
    "Return string of `mytxt` but with colour (intended for Linux commandline)"
    return textColors[color] + mytxt + textColors['default']

def dos2unix(mystr):
    "Convert Window EoL ('\r') to Unix EOL"
    return mystr.replace('\r','')

def removeNonAscii(s):
    "Remove non-ascii characters from provided string (`s`) and return modified string."
    return "".join(i for i in s if ord(i)<128)

def recursive_strip(myobj):
    "Recursively strip whitespace/newline objects until none are left"
    not_converged=True
    while not_converged:
        myobj=_mystrip(myobj)
        if myobj==_mystrip(myobj):
            not_converged=False
        else:
            not_converged=True
    return myobj

def _mystrip(mytxt): return mytxt.strip(' ').strip('\n').strip('\r')
def _mystrip2(mytxt): return mytxt.strip('\n').strip('\r')
#def mystrip(mytxt): return mytxt.strip('\n').strip(' ')
#def mystrip(mytxt): return mytxt.strip('\n').strip(' ').strip('\r')

def is_in(myarray, val):
    "Return `True` if whole/part of a value recorded in `myarray` is found in `val`. Else, return `False`."
    for myval in myarray:
        if myval in val: return True
        #if str( myval ) in str( val ): return True
    return False

def is_in2(myarray, val):
    "Return `True` if part/whole of `val` is found in any value recorded in `myarray`. Else, return `False`."
    for myval in myarray:
        if val in myval: return True
        #if str(val) in str(myval): return True
    return False

def is_not_in(myarray, val):
    "Return `False` if whole/part of a value recorded in `myarray` is found in `val`. Else, return `True`."
    for myval in myarray:
        if myval not in val: return True
    return False

def try2get(getfn, data):
    "Attempt executing `getfn` on `data[0]`. Return `None` if no data is found."
    if data:
        res=getfn(data[0])
    else:
        res=None
    #try:
    #    res=getfn(data[0])
    #except:
    #    res=None
    return res

# Filter using raw text only
def filter_IDF_objs_raw(objs, mytype):
    "genEPJ filter function which returns E+ objects with type `mytype`. Use to manipulate text only in certain objects (Windows/Walls/ etc)"
    return [obj for obj in objs if get_obj_type(obj)==mytype]

def identity(objs):
    "Return genEPJ `List` provided with no manipulations."
    return objs

#==============================
# EnergyPlus Specific Utilities
#============================== {{{


def get_eplus_version( myfile ):
    "Return E+ version as specified by user provided file (from E+ `Version` object)."

    objs_all=get_IDF_objs_raw(myfile)
    obj_version=filter_IDF_objs_raw(objs_all, 'Version')[0]
    version=get_obj_abstract(obj_version,1)

    return version.replace(';','')

def call(command):
    "Open a UNIX pipe and execute command `cmd`."
    command = command.split(' ')
    #return Popen(command, stdout=PIPE).communicate()[0].replace('\n','')
    return str( Popen(command, stdout=PIPE).communicate()[0]).replace('\n','')

#def presim(myfn):
#    # Run a simulation using the given IDF file (-t)
#    # Create an intermedary name '_presim"
#    # Run sim for 1 day, Copy sim data back (sql only)
#
#    new_idf=abstract_add_objs2file(myfn, to_file, 'presim')
#    print("New IDF for presim: ", new_idf)
#    #new_idf=to_file.replace('.idf','_presim.idf')
#
#    new_objs=get_IDF_objs_raw(new_idf)
#    obj_idx = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='RunPeriod'][0]
#    new_objs[obj_idx] = new_objs[obj_idx].replace('12,','1,',).replace('31','2')
#    f=open(new_idf, 'w')
#    f.write( combine_objects(new_objs) )
#    f.close()
#
#    ## EnergyPlus simulation
#    printc("Starting EnergyPlus Simulation",'blue')
#    start_t=time()
#    wfile='/home/sb/energyplus/EnergyPlus-8-1-0/WeatherData/CAN_ON_London.716230_CWEC.epw'
#    cmd='../EnergyPlus-8-1-0/runenergyplus %s %s'%(new_idf, wfile)
#    call(cmd)
#    stop_t=time()
#    print('E+ call took %0.3f msec' %((stop_t-start_t)*1e6))
#
#    sql_file=to_file.replace('idf','sql').replace('data_temp/','data_temp/Output/')
#    presim_sql_file=new_idf.replace('idf','sql').replace('data_temp/','data_temp/Output/')
#    # Should be good to go! All data is copied over
#    copyfile(presim_sql_file, sql_file)
#
#    return True

def create_data_dir(fnm):
    "Create temporary directory `data_temp` and copy specified building into it."

    data_dir='data_temp'
    fnm=basename(fnm)
    myfile=join(data_dir, fnm)
    if not isdir(data_dir):
        mkdir(data_dir)
        copyfile(fnm, myfile)
    elif not isfile(myfile):
        copyfile(fnm, myfile)
    else: # File and data_dir are their already
        #printc('Nothing to do', 'green')
        pass
    return myfile

def try2getsize(f):
    "Attempt to get/return size of file. If `None`, return 0.0."
    try:
        return getsize(f)
    except:
        return 0.0

# lambda FNs to join paths
_join_ep = lambda x: join(eplus_dir, x) # Join with EnergyPlus source directory
_join_epw = lambda x: join( join(eplus_dir, 'WeatherData'), x) # Join with EnergyPlus source directory
_join_dt = lambda x: join('data_temp', x) # Join with data_temp directory
wfile_dir = environ['ENERGYPLUS_WEATHER']
eplus_dir = environ['ENERGYPLUS_DIR']
_get_prefix = lambda x: splitext( basename(x) )[0]

_get_eplus_version = lambda x: [int(y) for y in x.split('-')[1:4]] # Return E+ version, eg. [9, 5, 0] for input 'EnergyPlus-9-5-0'
#get_version = lambda x: list( map(int, x.split('-')[1:4]) ) # Return E+ version, eg. [9, 5, 0] for input 'EnergyPlus-9-5-0'

def convertJSON2IDF(f):
    "Convert epJSON/IDF to IDF/epJSON."
    # Convert
    printc("'convertJSON2IDF': Converting epJSON to IDF.", 'green' )
    #cmd='%s --convert --output-directory %s --output-prefix %s %s'%(_join_ep('energyplus'), _join_dt('Output'), _get_prefix(f), f )


    # E+ version information [major, minor, micro] versioning
    ma,mi,mc = _get_eplus_version( eplus_dir )
    if ma>=9 and mi>=4 : # E+ added a new command option in >9.4.0
        cmd='%s --convert-only %s'%(_join_ep('energyplus'), f )
    else: # Version 9.0.0
        cmd='%s --convert %s'%(_join_ep('energyplus'), f )

    print(cmd)
    try: # Expect E+ to fail
        call(cmd)
    except:
        pass

    def _try_to_move(fname):
        try:
            move( new_name, join('data_temp', new_name))
        except FileNotFoundError:
            raise NameError("E+ was unable to convert IDF<->epJSON. Version numbers in file must be identical to your default version of EnergyPlus")


    if '.idf' in f:
        # Move .epJSON to .IDF
        new_name=basename(f).replace('.idf', '.epJSON')
        _try_to_move( new_name )
    elif '.epJSON' in f:
        # Move .IDF to .epJSON
        new_name=basename(f).replace('.epJSON', '.idf')
        _try_to_move( new_name )
    else:
        printc("'convertJSON2IDF': File '%s' not supported. Nothing to do!"%(f), 'yellow' )
        return f
    return join('data_temp', new_name)

def extract_comments_from_JSON_schema():
    "Extract all default comments from JSON schema. Used to add comments back to IDF after converting to/from epJSON."
    # $ENERGYPLUS_DIR/Energy+.schema.epJSON
    schema_file = join(eplus_dir, 'Energy+.schema.epJSON')
    #json_data = get_JSON_objs_raw(schema_file, ordered=1) # Keeps order in JSON as compared to IDF (can iterate later)
    json_data = get_JSON_objs_raw(schema_file)
    #print(json_data)
    comments={}
    return comments

    return json_data

# Move to Building()?
def find_JSON(search_parameter="opti_inputs"):
    "Return the input parameter file to specify optimization task list in genEPJ."
    try:
        #myjson=glob('%s*json'%(search_parameter))
        #json_str=open_JSON_file(myjson[0])
        myjson='%s.json'%(search_parameter)
        json_str=open_JSON_file(myjson)
    except:
        try:
            myjson=glob('%s*json'%(search_parameter))
            json_str=open_JSON_file(myjson[0])
        except:
            myjson=glob('sim_variables.txt')
            json_str=open_JSON_file(myjson[0])
    json_input = json.loads( json_str )
    return json_input


def run_energyplus(mybldg):
    "Conduct E+ simulation on a building."
    start_t=time()
    task=mybldg.next_task
    f=mybldg.task_filenames[task]
    wfile=mybldg.weather
    printc("Running energyplus on task '{}'".format(task))

    try:
        type(mybldg)
    except:
        raise NameError("'run_energyplus' needs to be passed a Building object with input, and a weather file specified. Input specified using 'mybldg.next_task'")

    cmd='%s --expandobjects --weather %s --output-directory %s --output-suffix C --output-prefix %s %s'%(_join_ep('energyplus'), _join_epw(wfile), _join_dt('Output'), _get_prefix(f), f )
    print(cmd)
    call(cmd)
    stop_t=time()
    print('E+ call took %0.1f min' %((stop_t-start_t)/60.))


#def maybe_call_eplus(f, wfile, force_resim=True, convert=False):
def maybe_call_eplus(f, wfile, force_resim=True, run_eplus=True, convert=False):
    "Run E+ on a building only if previous result files aren't found (or a force run flag is specified)."

    start_t=time()

    if convert:
        f=convertJSON2IDF(f)

    #ext=Path(f).suffix
    #sql_file= join( join('data_temp', 'Output'), basename(myfile).replace(ext,'.sql') ) # See energyplus --output-suffix (Capital -> .sql)

    #--output-suffix C: use *Table.htm
    if '.idf' in f:

        # if runenergyplus in path, use it, else use energyplus
        if which('runenergyplus'):
            cmd='%s %s %s'%(join(eplus_dir, 'runenergyplus'), f, wfile )
            sql_file= join( _join_dt('Output'), basename(f).replace('.idf','.sql') )
        else:
            # ./energyplus doesn't work with linked paths (ln -s /MetalMan/Output)
            cmd='%s --expandobjects --weather %s --output-directory %s --output-suffix C --output-prefix %s %s'%(_join_ep('energyplus'), _join_epw(wfile), _join_dt('Output'), _get_prefix(f), f )

            sql_file= join( _join_dt('Output'), basename(f).replace('.idf','out.sql') ) # See energyplus --output-suffix (Legacy -> out.sql)
    else: #JSON, use cmd 'runenergyplus' doesn't work...
        cmd='%s --expandobjects --weather %s --output-directory %s --output-suffix C --output-prefix %s %s'%(_join_ep('energyplus'), _join_epw(wfile), _join_dt('Output'), _get_prefix(f), f )
        sql_file= join( _join_dt('Output'), basename(f).replace('.epJSON','out.sql') ) # See energyplus --output-suffix (Legacy -> out.sql)

    try:
        #if ( (not isfile(sql_file)) or (try2getsize(sql_file)<10.0) or force ) :
        # SB- 2021-08-02 20:40:13: eplus always runs with the above version. DONT run no matter what if force=False
        #if ( (not isfile(sql_file) or force) or (try2getsize(sql_file)<10.0 or force) ):
        #print("run_eplus state: ",force)
        #print("IF statment state: ",(not isfile(sql_file) or force) or (try2getsize(sql_file)<10.0 or force) )
        if force_resim:
            print(cmd)
            if run_eplus: call(cmd)
        # Determines if we should run_eplus if force_resim isn't set
        elif  (not isfile(sql_file)) or (try2getsize(sql_file)<10.0) :
            print(cmd)
            if run_eplus: call(cmd)
        else:
            print("Force Resim flag NOT SET and Found previous SQL file '%s' with filesize: %.3f byte. Do nothing"%(sql_file, try2getsize(sql_file)) )
            #if run_eplus: call(cmd)
            print(cmd)
        stop_t=time()
        #print('E+ call took %0.3f msec' %((stop_t-start_t)*1e6))
        print('E+ call took %0.1f min' %((stop_t-start_t)/60.))
        return True
    #except TypeError:
    #    command = cmd.split(' ')
    #    Popen(command, stdout=PIPE)
    #    return True
    except:
        return False

def abstract_add_objs2file(myfn, to_file, suffix='newobj'):
    """Wrapper function to execute function `myfn` (genEPJ manipulation function) and output to file.

    Parameters:

    * `myfn`: genEPJ function to execute on file `to_file`
    * `to_file`: file to manipulate
    * `suffix`: new file suffix name (based on `to_file` basename)

    Returns:

    * `fname`: new saved file name with genEPJ manipulation
    """
    objs_all=get_IDF_objs_raw(to_file)
    if len(objs_all)<1 :
        ValueError("Unable to find objects in file %s"%(to_file))
    #print(objs_all)

    new_objs=myfn(objs_all)
    # NO repeat objects
    #new_objs=list(set(new_objs))
    #print(new_objs)

    #Finally, splice in copied objects and write to file
    newfile=to_file.replace(".","_%s."%(suffix))
    fname=write_file(new_objs, newfile)

    return fname

def abstract_add_JSONobjs2file(myfn, to_file, suffix='newobj'):
    """Wrapper function to execute function `myfn` (genEPJ JSON manipulation function) and output to file.

    Parameters:

    * `myfn`: genEPJ function to execute on file `to_file`
    * `to_file`: file to manipulate
    * `suffix`: new file suffix name (based on `to_file` basename)

    Returns:

    * `fname`: new saved file name with genEPJ manipulation
    """

    ext=Path(to_file).suffix

    try:
        objs_all=get_JSON_objs_raw(to_file)
    except:
        objs_all=get_IDF_objs_raw(to_file)

    if len(objs_all)<1 :
        ValueError("Unable to find objects in file %s"%(to_file))
    #print(objs_all)

    # Can return IDF list **OR** JSON dict
    new_objs=myfn(objs_all)

    newfile=to_file.replace(".","_%s."%(suffix))
    fname=write_file(new_objs, newfile)

    return fname, new_objs

#def run_eplus_and_createIDF(myfn, file_name, wfile, suffix, run_eplus=False, force=False):
#
#    # "force" creation of IDF/JSON even if results exist AND run E+
#    # "run_eplus" run EPLUS even if results exist
#
#    # BASEFILE: Check if given base filename hasn't been run (needed for creation of 'prep' file)
#    # Don't rerun basename if results already exists
#    myfile=join('data_temp', basename(file_name) )
#    newfile=myfile.replace(".idf","_%s.idf"%(suffix))
#    ## BASEFILE: Check if given base filename hasn't been run (needed for creation of 'prep' file)
#    #sql_file= join( join('data_temp', 'Output'), basename(file_name).replace('.idf','.sql') )
#    ##if not isfile(sql_file):
#    ##if run_eplus:
#    ##    # Run E+ first or the next steps below do not execute properly
#    maybe_call_eplus(myfile, wfile)
#
#    sql_file_res= join( join('data_temp', 'Output'), basename(newfile).replace('.idf','.sql') )
#    if ( ( isfile(newfile) ) and (isfile(sql_file_res)) and (not force) ):
#        printc('File "%s" previously created and force flag not set. Nothing to do!'%(newfile), 'yellow' )
#    else:
#        printc('\nFile "%s" will be created'%(newfile), 'yellow' )
#        abstract_add_objs2file(myfn, to_file=myfile, suffix=suffix)
#
#    #if run_eplus:
#    maybe_call_eplus(newfile, wfile, allow_eplus_run=run_eplus, force_run=force)
#
#    return newfile

## SB: new UPDATE TO JSON
## TODO- remove convert flag. Use swap_IDFJSON instead. Tue Jan 22 08:45:50 EST 2019
#def run_eplus_and_createJSON(myfn, file_name, wfile, suffix, run_eplus=False, force=False, convert=False):
#    #ext='.epJSON'
#    ext=Path(file_name).suffix
#    new_objs=[]
#    print("TEST: option given to run_eplus_and_createJSON. run_eplus= ",run_eplus)
#
#    myfile=join('data_temp', basename(file_name) )
#
#    # BASEFILE: Check if given base filename hasn't been run (needed for creation of 'prep' file)
#    #sql_file= join( join('data_temp', 'Output'), basename(myfile).replace(ext,'out.sql') ) # See energyplus --output-suffix (Legacy -> out.sql)
#    #sql_file= join( join('data_temp', 'Output'), basename(myfile).replace(ext,'.sql') ) # See energyplus --output-suffix (Capital -> .sql)
#    #if ( (not isfile(sql_file)) and (run_eplus) ):
#    # Don't rerun if file already exists
#    #if ( (not isfile(sql_file)) and (run_eplus) ):
#    #if run_eplus:
#        # Run prep file if sql files don't exist hasn't been run
#    maybe_call_eplus(myfile, wfile, convert=convert)
#
#    # REF/PROP/OPTI
#    # Manipulate IDF/JSON and run energyplus
#    # * Was file created previously?
#    newfile=myfile.replace(ext,"_%s"%(suffix+ext))
#    #sql_file_res= join( join('data_temp', 'Output'), basename(newfile).replace(ext,'out.sql') ) # See energyplus --output-suffix (Legacy -> out.sql)
#    sql_file_res= join( join('data_temp', 'Output'), basename(newfile).replace(ext,'.sql') ) # See energyplus --output-suffix (Capital -> .sql)
#    if ( ( isfile(newfile) ) and (isfile(sql_file_res)) and (not force) ):
#        printc('File "%s" previously created and force flag not set. Nothing to do!'%(newfile), 'yellow' )
#    else:
#        printc('\nFile "%s" will be created'%(newfile), 'yellow' )
#        newfile,new_objs=abstract_add_JSONobjs2file(myfn, to_file=myfile, suffix=suffix)
#
#    maybe_call_eplus(newfile, wfile, convert)
#
#    return new_objs

def run_eplus_and_createEPlusInput(myfn, file_name, wfile, suffix, force=False, run_eplus=True, convert=False):
    """Specify the genEPJ workflow for `prep` and `ref/prop/opti` building creation.

    Steps:

    1. Run E+ on base building (aka. `prep` building *if no results found*). Required to create SQL files for later information queries and manipulations.
    2. Check for results for (`prop`/`ref`/`opti` buildings). If `force_create` flag is set, conduct genEPJ `task_list`. If no flags are set, then run genEPJ only if no results are found.
    3. Run E+ if a new building was created (unless `force_resim` flag is set to `False`)
    """
    #ext='.epJSON'
    ext=Path(file_name).suffix
    new_objs=[]
    #print("TEST: option given to run_eplus_and_createEPlusInput. force_resim= ",force)

    myfile=join('data_temp', basename(file_name) )

    # BASEFILE: Check if given base filename hasn't been run (needed for creation of 'prep' file)
    #sql_file= join( join('data_temp', 'Output'), basename(myfile).replace(ext,'out.sql') ) # See energyplus --output-suffix (Legacy -> out.sql)
    #sql_file= join( join('data_temp', 'Output'), basename(myfile).replace(ext,'.sql') ) # See energyplus --output-suffix (Capital -> .sql)
    #if ( (not isfile(sql_file)) and (run_eplus) ):
    # Don't rerun if file already exists
    #if ( (not isfile(sql_file)) and (run_eplus) ):
    #if run_eplus:
        # Run prep file if sql files don't exist hasn't been run
    #if run_eplus:
    maybe_call_eplus(myfile, wfile, force_resim=False, run_eplus=True, convert=convert)

    # REF/PROP/OPTI
    # Manipulate IDF/JSON and run energyplus
    # * Was file created previously?
    newfile=myfile.replace(ext,"_%s"%(suffix+ext))
    #sql_file_res= join( join('data_temp', 'Output'), basename(newfile).replace(ext,'out.sql') ) # See energyplus --output-suffix (Legacy -> out.sql)
    sql_file_res= join( join('data_temp', 'Output'), basename(newfile).replace(ext,'.sql') ) # See energyplus --output-suffix (Capital -> .sql)
    if ( ( isfile(newfile) ) and (isfile(sql_file_res)) and (not force) ):
        printc('File "%s" previously created and force flag not set. Nothing to do!'%(newfile), 'yellow' )
    else:
        printc('\nFile "%s" will be created'%(newfile), 'yellow' )
        newfile,new_objs=abstract_add_JSONobjs2file(myfn, to_file=myfile, suffix=suffix)

    #printc("TEST from run_eplus_and_createEPlus: Length of created objects %d\n"%(len(new_objs)), 'yellow')

    maybe_call_eplus(newfile, wfile, force_resim=force, run_eplus=run_eplus, convert=convert)

    return new_objs

def trim_comments(myobj): #Trim comments from an eplus object
    """Remove E+ comments ('!-') from an IDF object.

    Example input of myobj:

    ```
    SimulationControl,
    No,                      !- Do Zone Sizing Calculation
    No,                      !- Do System Sizing Calculation
    No,                      !- Do Plant Sizing Calculation
    No,                      !- Run Simulation for Sizing Periods
    Yes;                     !- Run Simulation for Weather File Run Periods
    ```

    Example function output:

    ```
    SimulationControl,
    No,
    No,
    No,
    No,
    Yes;
    ```
    """

    # Strip off comments on a given line (occurs before e+ objects)
    re_nocom=re.compile("^[ ]*!.*?\n")
    #myobj=myobj.strip('\n')
    myobj=recursive_strip(myobj)
    #print("UNMODIFIED OBJECT")
    #print(myobj)
    #if 'no glass' in myobj:
    #    print("UNMODIFIED OBJECT")
    #    print(myobj)
    #    print("Matches: ",re_nocom.findall(myobj))
    myobj=re.sub(re_nocom, '', myobj)
    myobj=recursive_strip(myobj)
    #print("MODIFIED OBJECT")
    #print(myobj)
    #if 'no glass' in myobj:
    #    print("MODIFIED OBJECT")
    #    print(myobj)
    obj_lst = [ln.split('!-')[0].strip(' ') for ln in myobj.split('\n')]
    return '\n'.join(obj_lst)

def rm_unused_objs(myobjs):
    "Purge unused objects found in genEPJ `List`. Examples are E+ `Material`/`Construction` objects that are specified but not used anywhere else in the Building."
    # Examples of potential unused objects:
    # 1. Materials
    # 2. Construction
    # 3. Curves

    obj_txt="".join(myobjs)
    new_objs=list(myobjs)

    purge_list=[
                'Curve',
                'Material',
                'Glazing',
                'Construction',
                'Schedule:',
                'ScheduleTypeLimits',
                #'Lights', # SB NOTE: Only one Lights obj is referenced (refers to a ZoneList)
                #'People', # SB NOTE: Only one People obj is referenced (refers to a ZoneList)
                'LifeCycleCost:',
               ]

    for i,myobj in enumerate(myobjs):
        # NOTE: Add ',' to make sure matches are unique
        # Ex. name: 'Therm zone 1' will also match 'Therm zone 1 control' (not wanted)
        obj_type=get_obj_type(myobj)+','
        obj_name=get_obj_name(myobj)+','
        #NOTE: Need to comment out certain symbols in the regular expression that might be used in names
        obj_name=obj_name.replace('[','\[').replace(']','\]').replace('*','\*').replace('(','\(').replace(')','\)').strip('\n')
        # NOTE: reg-expression needs to match ',' or ';' for object type
        # Ex. Constructions can be only two lines long
        #print("RE Ex: %s"%(obj_name.replace(',','[,|;]')))
        # NOTE: EnergyPlus is CASE INSENTIVE for names
        namere=re.compile(obj_name.replace(',','[,|;]'),re.IGNORECASE)

        #Test to identify if '\[' and '\]' is working properly
        #if 'WindowMaterial:Glazing' in obj_type:
        #    #print("\tFound object '%s' with name '%s'"%(obj_type,obj_name))
        #    print("\tCounted object '%s' with name '%s', %d times"%(obj_type,obj_name, len(namere.findall(obj_txt))))

        for nm in purge_list:
            if (nm in obj_type) and (len(namere.findall(obj_txt))==1):
                # Match, remove the object
                print("Purging object '%s' with name '%s'"%(mkcolor(obj_type,'yellow'),mkcolor(obj_name,'yellow')))
                new_objs[i]=""
                #new_objs.remove(new_objs[i])

    new_objs=[myobj for myobj in new_objs if myobj!=""]

    return new_objs

# SB TODO- Need a sorted set. set(objs) changes the order
#  OR keep
# fn which sorts back to first provided myobjs
#def rm_repeat_objs(myobjs):
def rm_repeat_objs(myobjs, args={} ):
    "Remove duplicate genEPJ objects."
    old_objs = list(myobjs)
    new_objs = list(myobjs)
    diff_objs = []
    for obj in old_objs :
        if ( (obj.count( obj )>1) and (obj not in diff_objs) ) :
            diff_objs.append(obj)
            new_objs.remove(obj)
    if len(diff_objs)>0 :
        printc("Removed %d Duplicate objects!\n"%(len(diff_objs), 'blue'), 'yellow')
    return list(new_objs)

def rm_obj_by_type(obj_type, myobjs):
    "Remove genEPJ object if it matches supplied E+ type (`obj_type`). Return genEPJ `List` with objects removed."
    # Old way look for exact matches
    #return [obj for obj in myobjs if get_obj_type(obj)!=obj_type]

    # New statement allows for pseudo glob statements
    return [obj for obj in myobjs if obj_type not in get_obj_type(obj)]

# FN now used with Modelkit exclusively
def rm_all_HVAC_IDF(myobjs, args={}):
    "Remove all HVAC type objects. Return genEPJ `List` with HVAC objects removed."
    # Function removes all HVAC elements from the objs list

    # NOTE: to see what *NAME* matches:
    # 1. open of E+.idd
    # 2. in vim, :v/^\w/d (delete all text except titles)
    # 3. in vim, :g/.*HVAC/d (delete all text with HVAC in it)
    # 4. use HVAC rm list to get the rest

    # Glob searches to grab HVAC objects
    rm_hvac=[
               ##### Glob specification of objects to be removed ####
               'HVAC',
               'Coil', #Warning: grabs 'AirflowNetwork:Distribution:Component:Coil'
               'COIL', #Warning: grabs 'AirflowNetwork:Distribution:Component:Coil'
               'AirTerminal',
               'HeatPump',
               'HeatExchanger',
               'Boiler',
               'Chiller',
               'EvaporativeCooler', #Free cooling from towers
               'CoolingTower',
               'AirLoop',
               'CondenserLoop',
               'PlantLoop',
               'SetpointManager',
               'Refrigeration',
               'EquipmentList', #Warning: Don't use 'Equipment', ElecEquip is gains to zone
               'Pump',
               'Fan', #Warning: grabs 'AirflowNetwork:Distribution:Component:Fan'
               'District',
               'Connector', #Grabs Mixer, Splitter, ConnectorList
               ##### Explicit specification of objects to be removed ####
               'NodeList',
               'ZoneTerminalUnitList',
               'OutdoorAir:Node',
               'OutdoorAir:Mixer',
               'OutdoorAir:NodeList',
               #'DesignSpecification:OutdoorAir', # Vent sizing for OA (DSOA obj)
               #'Sizing:Zone', # Zone air specs for each zone (refer to DSOA obj)
               'ThermostatSetpoint:DualSetpoint',
               'ZoneControl:Thermostat',
               'AirConditioner:VariableRefrigerantFlow',
               'Curve:Biquadratic', # TEST: Used for VRF coil/unit properties
               'Curve:Cubic', # TEST: Used for VRF coil/unit properties
               'Curve:Quadratic', # TEST: Used for VRF coil/unit properties
               'CURVE:QUADRATIC', # TEST: Used for VRF coil/unit properties
               'Curve:Linear', # TEST: Used for VRF coil/unit properties
               # Added for Modelkit
               'ZoneHVAC:EquipmentConnections',
               'CoilSystem',
               'AirLoopHVAC',
               'Pipe:Adiabatic',
               'WaterUse:Connections',
               'WaterUse:Equipment',
               'WaterHeater:Sizing',
               'Sizing:Plant',
               'Sizing:Zone',
               'Sizing:System',
               'PlantEquipment',
               'AvailabilityManagerAssignmentList',
               'AvailabilityManager:NightCycle',
               'AvailabilityManager:Scheduled',
               'DesignSpecification:OutdoorAir',
               'BranchList',
               'Branch',
               'WaterHeater:Mixed',
               'Controller:OutdoorAir',
               'Controller:MechanicalVentilation',
              ]

    new_objs= list(myobjs)

    for nm in rm_hvac:
        new_objs= rm_obj_by_type(nm, new_objs)

    #nvhavc_objs_name=list(map(get_obj_name, new_objs))
    #rmd_objs=[ob for ob in myobjs if get_obj_name(ob) not in nvhavc_objs_name]

    #for obj in rmd_objs:
    #    obj_type=get_obj_type(obj)
    #    obj_name=get_obj_name(obj)
    #    print("Purging HVAC object '%s' with name '%s'"%(mkcolor(obj_type,'yellow'),mkcolor(obj_name,'yellow')))

    return new_objs


def rm_all_HVAC_simple(myobjs, args):
    "Remove a limited set of HVAC type objects. Return genEPJ `List` with HVAC objects removed."

    new_objs= list(myobjs)
    len_all=len(myobjs)

    # Keep Sizing:Parameters (rm_all_HVAC removes this...)
    new_objs= [obj for obj in new_objs if 'hvactemplate' not in get_obj_type(obj).lower()]
    new_objs= [obj for obj in new_objs if 'sizing:zone'  not in get_obj_type(obj).lower()]
    new_objs= [obj for obj in new_objs if 'zonecontrol:thermostat' not in get_obj_type(obj).lower()]
    # Remove unneccesary outputs added by OpenStudio for IdealLoads
    new_objs= [obj for obj in new_objs if not ('output:variable,*,zone air system sensible cooling rate' in obj.lower())]
    new_objs= [obj for obj in new_objs if not ('output:variable,*,zone air system sensible heating rate' in obj.lower())]
    # Removed for DOE Archetype HighRise
    new_objs= [obj for obj in new_objs if 'zonehvac:equipmentconnections' not in get_obj_type(obj).lower()]

    printc("Removed %d HVAC objects!\n"%(len_all-len(new_objs)), 'yellow')

    return new_objs

def deploy_if_function_list(idf_objs, myfnlist):
    """Abstract away the execution of fns and if statements. Used by make_ref, make_prop"""

    new_objs=idf_objs
    redstar=mkcolor('**', 'red')

    #==========
    # EXECUTION
    #==========
    #for myif,myfn,myargs in myfnlist:
    for myfn,myif,myargs in myfnlist:
        if myif:
            yellargs=mkcolor(str(myargs), 'yellow')
            print(redstar + mkcolor("Executing function: %s with args: "%(myfn.__name__), 'blue') + yellargs + redstar )
            new_objs = myfn(new_objs, myargs)

    return new_objs

# SB Want to separate this out from write_file
#  Some objects are in string blocks (multiple objects in one string object)
#  Combining and resplitting can fix this
#  SB: Originally an issue with copying
def combine_objects(objs_all):
    "Combine genEPJ `List` objects into a string that can be written to file."
    # dos2unix: get rid of pesky '\r' objects
    return dos2unix("\n\n".join(objs_all))

from eppy.modeleditor import IDF
def write_file(objs_all, nm):
    "Write genEPJ List/JSON to file `nm`. Function determines if the provided objects are `JSON` or a `List`. Return new file name."

    # Check/repair discrepancies in objs_all type and naming convention. Fix if found
    # SB: Duplicate code in maybe_call_eplus
    ext=Path(nm).suffix
    if ( (isinstance(objs_all, list)) and ('json' in nm.lower())): # extension changed in deploy_if_function_list. Rename as epJSON
        newfile=nm.replace(ext, '.idf')
    elif ( (isinstance(objs_all, dict)) and ('.idf' in nm.lower())): # extension changed in deploy_if_function_list. Rename as IDF
        newfile=nm.replace(ext, '.epJSON')
    elif ( (type(objs_all)==IDF) and ('.json' in nm.lower())): # extension changed in deploy_if_function_list. Rename as IDF
        newfile=nm.replace(ext, '.idf')
    else:
        newfile=nm

    printc("Saving new file to: %s"%(newfile), 'green')

    if '.idf' in newfile.lower():
        # Add eppy file format
        if type(objs_all)==IDF :
            idfstr= IDF.idfstr( objs_all )
            objs_all = get_IDF_objs_raw(idfstr)

        while  objs_all!=[_mystrip2(obj) for obj in objs_all]:
            objs_all=[_mystrip2(obj) for obj in objs_all]

        f=open(newfile, 'w')
        f.write( combine_objects(objs_all) )
        f.close()
    if 'json' in newfile.lower():
        with open(newfile, 'w') as f:
            json.dump(objs_all, f, indent=4, separators=(',', ': ')) # separators removes whitespace

    return newfile


def open_IDF_file(file):
    "Open E+ IDF File (`file`) and perform simple text substitions (remove non-ascii characters, round numbers). Return `String` of all text in file."
    mydata = open(file, 'r').read()
    # Align IDF objects
    #objs = align_IDF_objs(objs)
    # Remove all non-ascii characters
    mydata=removeNonAscii(mydata)
    mydata=roundNumbers(mydata)
    # Execute twice: once to round -1e-23, second to reformat -0.000
    mydata=roundNumbers(mydata)
    return mydata


def test_if_json(mydata):
    "Return `True` if provided data (`mydata`) is a json object. Else, return `False`."
    if isfile(mydata):
        try:
            json_object = json.load(mydata)
        except Exception:
            return False
    elif isinstance(mydata, str):
        try:
            json_object = json.loads(mydata)
        except Exception:
            return False
    return True

# SB TODO: Add improvements (rounding, etc)
# Sun Dec 30 12:15:18 EST 2018
def open_JSON_file(file):
    "Open E+ JSON File (`file`) and perform simple text substitions (remove non-ascii characters, round numbers). Return `String` of all text in file."
    mydata = open(file, 'r').read()
    test_if_json(mydata)
    # Align IDF objects
    #objs = align_IDF_objs(objs)
    # Remove all non-ascii characters
    #mydata=removeNonAscii(mydata)
    #mydata=roundNumbers(mydata)
    ## Execute twice: once to round -1e-23, second to reformat -0.000
    #mydata=roundNumbers(mydata)
    return mydata

# buildraw: text only. Doesnt build objects from text like build_IDF_obj fn
def get_IDF_objs_raw(data):
    "Convert supplied data (`data`) into a genEPJ `List` which is returned to user. Data can be type `List`, `File`, or `String`."
    if isinstance(data, list):
        print("Data is of type List: Joining and converting to DOS")
        mydata=dos2unix("\n\n".join(data))
    elif isfile(data):
        print("Data is a File: Opening and processing to type String")
        mydata=open_IDF_file(data)
    elif isinstance(data, str):
        # Nothing to do
        print("Data is of type String: Nothing to do")
        mydata=data
    else:
        raise ValueError("get_IDF_objs_raw: Unknown data type or non-existant file :"+data)
    # SB NOTE: mydata must be type string at this point
    objs = myre.findall(mydata)
    # Strip leading \n on objs
    objs=[obj.strip('\n') for obj in objs]
    return objs

def get_JSON_objs_raw(data, ordered=1):
    "Same as utility as `gen_IDF_objs_raw` but for `JSON` objects (not genEPJ `List` objects)."
    if isinstance(data, list):
        print("Data is of type List: Joining and converting to DOS")
        mydata=dos2unix("\n\n".join(data))
    elif isfile(data):
        #print("Data is a File: Opening and processing to type String")
        mydata=open_JSON_file(data)
    elif isinstance(data, str):
        # Nothing to do
        print("Data is of type String: converting to JSON")
        mydata=json.loads(data)
    else:
        raise ValueError("get_JSON_objs_raw: Unknown data type or non-existant file :"+data)
    # SB NOTE: mydata must be type string at this point
    #objs = myre.findall(mydata)
    # NOTE: objs is a DICT not a LIST as before
    with open(data) as f:
        if ordered:
            objs = json.load(f, object_pairs_hook=OrderedDict) # Perserve order in original JSON (useful for later diffs)
        else:
            objs = json.load(f)

    # Strip leading \n on objs
    #objs=[obj.strip('\n') for obj in objs]
    return objs

# SB: Mark for deletion
#def remove_IDF_objs(obj, oldfile):
#    ""
#    newfile=oldfile.replace(".","_mod.")
#    print("Saving new file to: ",newfile)
#    pass

def print_IDF_objs(file):
    "Print E+ JSON File (`file`) and perform simple text substitions (remove non-ascii characters, round numbers). Return `String` of all text in file."
    mydata = open(file, 'r').read()
    mydata=removeNonAscii(mydata)
    mydata=roundNumbers(mydata)
    objs = myre.findall(mydata)
    # SB: used to test subsets of objects that weren't matching from OpenStudio
    #objs = objs[230:]
    #objs = objs[430:500]
    for f in objs:
        print(f)
        #sleep(2)
        sleep(1)

def extract_nms_from_zonelist(objs_zonlist, chk_nm):
    "Extract names from E+ `ZoneList` if provided string `chk_nm` matches. Return `List` of `Zones` specified in `ZoneList`."
    zns=[obj for obj in objs_zonlist if chk_nm in get_obj_name(obj).lower()]
    if not zns:
        return []
    #print("TEST: %s (%s): Found Zones to extract Names"%(get_obj_name(obj), chk_nm),zns)
    strip_obj = trim_comments( zns[0] ).replace(';','')
    raw_lst= strip_obj.split(',')
    # Fixes previous bug: had '\r\n' which I wasnt able to split using ',\n'
    #raw_lst = map( recursive_strip, raw_lst )
    raw_lst = list(map( recursive_strip, raw_lst ))
    #print("Found info",raw_lst)
    # Skip Object Type and Object Name, Rest is ZoneNames
    zones_lst=raw_lst[2:]

    return zones_lst

# SB TODO: Use abstract class for 8 below functions
def get_obj_abstract(myobj, idx, args={'trim_comments': True}):
    "Return value found in position `idx` of provided genEPJ object."
    # Hack. Best to use trim_comments() first
    #return myobj.split(',')[0].strip('\n')
    if args['trim_comments']==True:
        no_com = trim_comments(myobj)
    else: # JSON conversion
        no_com = myobj
    # TODO: use unix2dox
    if (('BuildingSurface:Detailed' in myobj) or ('FenestrationSurface:Detailed' in myobj)): # the object uses corrdinates
        sp_ln=no_com.replace(';','').split(',\n')
        #print("Want idx: ", idx)
        #print("Len myobj: ", len(sp_ln))
        #print(sp_ln)
        myln=no_com.replace(';','').split(',\n')[idx]
        return myln
        #swap_sep = no_com.replace(',', '!', myln.count(',')-1)
        #return myln.replace('!',',')
    else:
        return no_com.split(',')[idx].strip(' ').strip('\r').strip('\n').replace(';','')

def get_obj_type(myobj):
    "Return genEPJ object type."
    # Hack. Best to use trim_comments() first
    #return myobj.split(',')[0].strip('\n')
    no_com = trim_comments(myobj)
    # TODO: use unix2dox
    return no_com.split(',')[0].strip(' ').strip('\r').strip('\n')

def get_obj_name(myobj):
    "Return genEPJ object name."
    no_com = trim_comments(myobj)
    # Why extra strip: E+ allows for IDs with spaces b4/after name
    return no_com.split(',')[1].strip(' ').strip('\r').strip('\n')

def get_surf_type(myobj):
    "Return `BuildingSurface:Detailed` type (Roof/Wall/etc)."
    # TODO: Write test to make sure myobj is type 'BuildingSurface:Detailed'
    no_com = trim_comments(myobj)
    #print(no_com)
    return no_com.split(',')[2].strip(' ').strip('\r').strip('\n')

def get_surf_cons_name(myobj):
    "Return name of `Construction` specified in `BuildingSurface:Detailed` object."
    # TODO: Write test to make sure myobj is type 'BuildingSurface:Detailed'
    no_com = trim_comments(myobj)
    #print(myobj)
    return no_com.split(',')[3].strip(' ').strip('\r').strip('\n')

def get_surf_zone(myobj):
    "Return name of `Zone` specified in `BuildingSurface:Detailed` object."
    # TODO: Write test to make sure myobj is type 'BuildingSurface:Detailed'
    no_com = trim_comments(myobj)
    #print(myobj)
    return no_com.split(',')[4].strip(' ').strip('\r').strip('\n')

def _get_cons_name(myobj):
    # TODO: Write test to make sure myobj is type 'Construction'
    no_com = trim_comments(myobj)
    #print(myobj)
    return no_com.split(',')[1].strip(' ').strip('\r').strip('\n')

def get_cons_name_from_type(cons_objs,surf_objs,cons_type):
    "Extract E+ `Construction` name from specified `Construction` type. Used to substitute new E+ `Constructions`/`Materials`."
    # SB: Should only be one here in template file. Give warning if more.
    #print( [_get_cons_name(obj1) for obj1 in cons_objs] )
    #print( [get_surf_cons_name(obj2) for obj2 in surf_objs] )
    cons_names = [_get_cons_name(obj1) for obj1 in cons_objs for obj2 in surf_objs if _get_cons_name(obj1)==get_surf_cons_name(obj2)]
    #print(cons_names)
    if len(cons_names)<1 :
        printc("Warning: No Construction objects found in template file for type %s"%(cons_type),'red')
        return None
    else: # len(cons_names)>=1 :
        printc("Warning: More than one construction object found in template file for type %s"%(cons_type),'red')
        printc("Warning: Using first object found! %s"%(cons_names[0]),'red')
        return cons_names[0]

def set_obj_abstract(myobj, new_val, pos):
    "Modify genEPJ object value in position `pos` to supplied value `new_val`. Return modified genEPJ object."
    old_val=get_obj_abstract(myobj, pos)
    #print(old_val)
    old_ln=myobj.split('\n')[pos]
    #try:
    #    old_ln=myobj.split('\n')[pos]
    #except IndexError,e:
    #    old_ln=myobj.split('\r')[pos]

    if ';' in old_ln: sep=';'
    else: sep=','
    new_ln=old_ln.replace(old_val+sep, str(new_val)+sep)
    #print(old_ln)
    #print(new_ln)
    #print(old_val)
    printc("Modifying object '%s': name: '%s', line content: '%s' to '%s'"%(mkcolor(get_obj_type(myobj), "blue"),
                                                        mkcolor(get_obj_name(myobj), "blue"),
                                                        mkcolor(old_ln, "blue"),
                                                        mkcolor(str(new_val), "blue")), "yellow")
    return myobj.replace(old_ln, new_ln)

def set_surf_name(myobj,surf_name):
    "Replace E+ `Construction` name in specified surface `surf_name`. Return modified genEPJ object."
    old_sf_cons_name=get_surf_cons_name(myobj)
    surf_obj_nm=get_obj_name(myobj)
    print("Replacing Construction Name '%s' with '%s' in surface '%s'"%(mkcolor(old_sf_cons_name,'yellow'),mkcolor(surf_name,'yellow'), mkcolor(surf_obj_nm,'yellow')))
    return myobj.replace(old_sf_cons_name, surf_name)

def set_simcontrl_sizing(myobj,state='Yes'):
    "Set `SystemSizing` in E+ `SimulationControl` object to `Yes`. Return modified genEPJ object."
    myobj=myobj.strip() # Bug fix: Strip any \r\n\r nonsense from myobj
    old_state=get_obj_abstract(myobj, 2)
    old_ln=myobj.split('\n')[2]
    new_ln=old_ln.replace(old_state, state)
    printc("SimulationControl: Turning ON SystemSizing", "yellow")
    myobj= myobj.replace(old_ln, new_ln)
    printc("SimulationControl: Turning ON PlantSizing", "yellow")
    # Turn on Plant Sizing as well
    old_ln=myobj.split('\n')[2]
    new_ln=old_ln.replace(old_state, state)
    myobj= myobj.replace(old_ln, new_ln)
    myobj= myobj.replace(old_ln, new_ln)
    return myobj

def set_simcontrl_run4sizing(myobj,state='No'):
    "Set `SizingPeriod` in E+ `SimulationControl` object (Yes/No). Return modified genEPJ object."
    myobj=myobj.strip() # Bug fix: Strip any \r\n\r nonsense from myobj
    old_state=get_obj_abstract(myobj, 4)
    old_ln=myobj.split('\n')[4]
    new_ln=old_ln.replace(old_state, state)
    printc("SimulationControl: Turning OFF Run for SizingPeriod", "yellow")
    myobj= myobj.replace(old_ln, new_ln)
    return myobj

def set_simcontrl_remove_run4sizing(objs_all, args={} ):
    "Remove `SizingPeriod` in E+ `SimulationControl` object to `No`. Return modified genEPJ object `List`."

    new_objs=list(objs_all)
    obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='SimulationControl']
    if obj_idxs:
        # MODIFY SimulationControl
        objs_simcontrl=filter_IDF_objs_raw(objs_all, 'SimulationControl')[0]
        new_objs[obj_idxs[0]]=set_simcontrl_run4sizing(objs_simcontrl, 'No')

    return new_objs

def set_obj_PowerDensity(myobj,frac=0.5):
    "Multiply PowerDensity in E+ `Light`/`ElectricalEquipment` object by fraction. If `frac=0.8`, then power density is reduced by 20%."
    #TODO: Check that objs is type 'Lights'
    #TODO: Check that objs is units 'Watts/Area'
    li_name=get_obj_name(myobj)
    try:
        old_li_lpd=get_obj_abstract(myobj,6)
        new_li_lpd=frac*float(old_li_lpd)
        print("Replacing PowerDensity of '%s' from '%s' to '%s'"%(mkcolor(li_name,'yellow'), mkcolor(old_li_lpd,'yellow'), mkcolor(str(new_li_lpd),'yellow')))
        myobj= myobj.replace(old_li_lpd, "%.5f"%(new_li_lpd))
    except:
        print("Error replacing LPD of '%s'"%(mkcolor(li_name,'yellow')))
    return myobj

def set_obj_Power(myobj,frac=0.5):
    "Multiply Power in E+ `Light`/`ElectricalEquipment` object by fraction. If `frac=0.8`, then power density is reduced by 20%."
    li_name=get_obj_name(myobj)
    try:
        old_li_power=get_obj_abstract(myobj,5)
        new_li_power=frac*float(old_li_power)
        print("Replacing Power of '%s' from '%s' W to '%s' W"%(mkcolor(li_name,'yellow'), mkcolor(old_li_power,'yellow'), mkcolor(str(new_li_power),'yellow')))
        myobj= myobj.replace(old_li_power, "%.5f"%(new_li_power))
    except:
        print("Error replacing power of '%s'"%(mkcolor(li_name,'yellow')))
    return myobj

def set_objs_PowerDensity(myobjs,frac=0.5):
    "Apply power density changes to genEPJ `List` using `set_obj_PowerDensity`."
    objs= [set_obj_PowerDensity(o,frac) for o in myobjs]
    return objs

def set_obj_Infil(myobj,frac=0.5):
    "Modify airtightness value in Infiltration object. If `frac=0.8`, then `Flow`/`Airchanges` is reduced by 20%."
    nm=get_obj_name(myobj)
    tp=get_obj_abstract(myobj,4)
    if 'FLOW/EXTERIORAREA' in tp.upper():
        idx=7
    elif 'AIRCHANGES' in tp.upper():
        idx=8
    else:
        printc("WARNING! Type '%s' not recognized for infil obj: %s"%(mkcolor(tp, "blue"), mkcolor(nm, "red")), "yellow")
        return myobj
    try:
        old_infil=get_obj_abstract(myobj,idx)
        #print("TEST:", old_infil)
        new_infil=frac*float(old_infil)
        #print("TEST:", new_infil)
        print("Replacing Infil of '%s' from '%s' to '%s'"%(mkcolor(nm,'yellow'), mkcolor(old_infil,'yellow'), mkcolor(str(new_infil),'yellow')))
        if idx==7 : # Flow/Area requires more sigfigs
            myobj= myobj.replace(old_infil, "%.6f"%(new_infil))
        else:
            myobj= myobj.replace(old_infil, "%.3f"%(new_infil))
    except:
        print("Error replacing Infil of '%s'"%(mkcolor(nm,'yellow')))
    return myobj




#******************************* }}}


#********************
# Simulation Features {{{
#********************
# Values to read in from simulation
def get_features(myfile):
    "Read in simulation feature list. If no feature list is found, use preset defaults."
    feat_dict={}
    try:
        fname="features.csv"
        f=open(fname,'r')
        feat_data=loadtxt(f, usecols=[0], skiprows=1)
        f=open(fname,'r')
        lns=f.readlines()[1:]
        def cleanline(ln):
            return ln.split('%')[1].split(',')[0]
        feat_vars= [ cleanline(ln) for ln in lns ]
        feat_dict=dict( zip(feat_vars, feat_data) )
        f.close()
        printc("Sucessfully Loaded Feature Data", 'green')
    #except Exception, e:
    #    printc("Loading Cost Data. Encountered Error: %s. Using preset costing data"%(e), 'red')
    except Exception:
        printc("Loading Cost Data. Encountered Error: Using preset costing data", 'red')
        feat_dict={
                   "use_humid_cap": 1,
                   "use_therm_mass": 1,
                   "use_win7": 0, # Use LBNL Window 7 Spectra
                   "use_condfd": 0, # Use conduction finite difference
                   "use_daylight": 1, # Use daylighting in zones
                   "pv_model": 1, # Which PV model to use 1: Simple; 2: One-Diode; 3: Sandia
                   "pv_couple": 1, # Use PV thermal coupling
                   "grnd_bc": 1, # 1; Use Wilkinson model for basement heat loss, 2 :
                   "enforce_ashrae62": 1,
                   "timestep": 4,
                   "solardistribution": 1, # Solar Distribution Solver: 1- FullExterior; 2- FullInteriorAndExterior
                  }
    print("Using Features Dictionary: %s"%(feat_dict))
    return feat_dict
#******************** }}}

#if __name__ == '__main__':
#    _myf='data_temp/RefBldgSmallOfficeNew2004_Chicago_prep.epJSON'
#    print( convertJSON2IDF(_myf) )
