"""
`generate_EPJ` orchestrates template changes, modifications and additions.
The inputs to functions should be a `list` (if using genEPJ templates), `json` (if using genEPJ to make changes directly or if using external tools, such as `eppy` or `OpenStudio`, the identical required format.
Functions are named consistently to suggest what the goal is: #1 verb, #2 description, #3. Input/output format (JSON, eppy, OSM, etc).
Naming conventions should start with a verb which outlines the intention of the function, .
For example:

* `rm`->removes information from the E+ object list
* `mod`-> modifies information within the model
* `add`-> adds templates to the model
* `...`-> XXX

Version 1.0 of `genEPJ` includes over 200 E+ templates by default (58 addition templates, 55 modification, 99 ModelKit)

Parameters:

* `eso`: the path to the eso file

Returns:

* `new_objs`: genEPJ object list (Python `List`)

The default input format is genEPJ (a Python list) and is assumed if not specified in the function.
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Where to focus refactoring? See below word count of functions
# ~/bin/python_fn_wordcount.sh | grep -E "[0-9]{3}" | sort -nr -k 3
# ~/bin/python_fn_wordcount.sh | grep -E " [0-9]{2}$" | sort -nr -k 3

#=====================
# TODO- Refactors
#=====================
# def mod_ERV_specs_file(to_file=to_file):
#remove all if statements: SiftonHQ, BID, etc
#def extract_schedules(objs_all):
#
#
# Decorators to perform fnname_file()
# Add Floor multiplier
# get frac schedules (lighting, occupancy, etc). Show Vasken how to use this...

# TODO: Decorators
# 1. set a version lock over a function
#   Only execute if the appropriate eplus versions is set
#   ex. battery controllers


genEPJ_vers = 1.0
version_color='red'
#genEPJ_vers = 1.1
#version_color='yellow'
#genEPJ_vers = 1.2
#version_color='green'

import sys


# convertJSON2IDF
from os.path import basename, join
from glob import glob
from os import remove

from time import time
from os.path import isfile
from os import environ, system, getcwd, getenv, chdir, getcwd

sys.path.append( join( 'genEPJ', 'pylib') )
sys.path.append('pylib')
sys.path.append('templateGenerator_epJSON')

# IDF
from templater import verbose, template_dict
from templater import templater as idf_templater


## epJSON
#from epJSON_templater import templater, verbose, template_dict, get_template_defaults_required, load_json_template
from epJSON_templater import templater, template_dict, get_template_defaults_required, load_json_template
#epJSON_template="genEPJ_pkg/templateGenerator_epJSON/templates_9.0.1.json"
epJSON_template="genEPJ/templateGenerator_epJSON/templates_9.0.1.json"
if not isfile(epJSON_template):
    epJSON_template="templateGenerator_epJSON/templates_9.0.1.json"
#epJSON_template="templates_9.0.1.json"
json_temp = load_json_template( epJSON_template )
epJSON_keys= json_temp.keys()

#import templates_v8_5 as templ
#templ=Configuration()
#global templ
#import templates_v8_1 as templ
import templates_v9_0 as templ
from genEPJ_lib import *

from tempfile import mkstemp, mkdtemp

# Thermostats common between all mechanical systems (by building type)
thermo_nm="All Zones10"
heatsp_nm="Htg-SetP-Sch10"
coolsp_nm="Clg-SetP-Sch10"

def show_welcome(eplus_vers):
    "Welcome text image when starting up genEPJ"
    # > figlet genEPJ (linux command)
    # TODO: change color with every major version
    # f: f-string
    # r: raw ascii art
    msg=fr"""
__________________________________________________
    You are using...
                  _____ ____     _
  __ _  ___ _ __ | ____|  _ \   | |
 / _` |/ _ \ '_ \|  _| | |_) |  | |  Version {genEPJ_vers}
| (_| |  __/ | | | |___|  __/ |_| |     WITH
 \__, |\___|_| |_|_____|_|   \___/   EnergyPlus {eplus_vers}
 |___/
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
    """
    print( mkcolor( msg , version_color))
    sleep(1.0)
    return None

# Class enables import of E+ switches from building
# OOP needed since we are dealing with state
class Configuration:
    "`Configuration` class sets E+ and quality of life parameters (verbose substitution, flag to run E+ within genEPJ)"
    def __init__(self):
        self.version = "25.1.0"
        self.verbose_substitute = False
        #self.allowed_versions=["8.1", "8.5"]
        #self.allowed_versions=["8.1", "8.5", "9.0.1", "9.4.0"]
        #self.allowed_versions=["8.1", "8.5", "9.0.1", "9.4.0", "9.5.0", "9.6.0", "22.1.0", "22.2.0"]
        self.force_recreate = False # DONT resimulate if SQL results found
        self.run_eplus = False
    def set_verbose_substitute(val):
        "Enable verbose substitute for genEPJ functions and parameter specification"
        verbose.verbose_set( val )
        self.verbose_substitute = val
    def eplus_version_set(self, vers):
        "Set E+ versions which specifies which genEPJ template to use and specific E+ PATH"
        #if vers not in self.allowed_versions:
        #    raise TypeError("Provided version '{0}' not permitted. Allowed versions: {1}".format( vers, self.allowed_versions ))
        #else:
        self.version = vers
        #if vers == "8.1":
        #    import templates_v8_1 as templ
        #elif vers == "8.5":
        #    import templates_v8_5 as templ
        #else: # Assume >v9
        #    import templates_v9_0 as templ
        #global templ
        show_welcome(vers)
    def eplus_version_get(self): return self.version

config = Configuration()

## Used to output modifications to a file with extension specifed
## SB: If 'condition' is set then call function with the decorator
#class conditional_decorator(object):
#    def __init__(self, dec, condition):
#        self.decorator = dec
#        self.condition = condition
#
#    def __call__(self, func):
#        if not self.condition:
#            # Return the function unchanged, not decorated.
#            return func
#        return self.decorator(func)
#
#@conditional_decorator(timeit, True)
#def foo():
#    time.sleep(2)

# Set building type
# AND set verbose switch on genEPJ print outs?
# Intended to be set inside the building model (ex. SiftonHQ.py)
class Building:
    "Building specific settings such as location (primary energy factors), type (commercial vs residential vs etc), weather file, task (genEPJ functions)."
    def __init__(self):
        self.allowed_types=["commercial", "multi-residential", "supermarket"]
        self.allowed_locations = ["Ontario", "Quebec"]
        self.type = "comm"
        self.location = "Ontario"
        self.weather = None
        self.to_file = None
        self.tasks = {}
        self.task_filenames = {}
        self.task_suffix = {}
        self.config = config
        self.next_task = "prep"
        self.IDFS = {}
        self.epJSON = {}
        #self.verbose_substitute = False
        #self.type = "resi"

    def type_set(self, mytype):
        "Set building type and check for allowed types"
        if mytype not in self.allowed_types:
            raise TypeError("Provided type '{0}' not permitted. Allowed types: {1}".format( mytype, self.allowed_types ))
        else:
            self.type = mytype
    def location_set(self, mylocation):
        "Set location and check for allowed types"
        if mylocation not in self.allowed_locations:
            raise locationError("Provided location '{0}' not permitted. Allowed locations: {1}".format( mylocation, self.allowed_locations ))
        else:
            self.location = mylocation
    def file_set(self, myfile):
        "Set E+ file to load in and start making changes to."
        self.to_file = myfile

    #def set_tasks(self, myjson):
    #    ""
    #    pass

    def set_thermostats(self, heat_thermo, cool_thermo, return_modelkit=False, args={}):
        "Set global thermostat on building (residential/commercial/industry specific). If using ModelKit, return this schedule so it can be specified in Ruby root file."
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool

        # Same as:
        # method_to_call = getattr(foo, 'bar')
        # result = method_to_call()

        txt_thermsch_global_heat, tempsch_def_heat = getattr(templ, heat_thermo)()
        txt_thermsch_global_cool, tempsch_def_cool = getattr(templ, cool_thermo)()
        # Added for Mohammad. Fri Jul 30 08:03:59 PM EDT 2021
        #    pass
        #else: 
        #if 'cool_setback' in args :
        #    pass
        #else: 
        #txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi() # Use defaults
        #txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi() # Use defaults

        # return statement required for ModelKit integration
        # NOTE: Tested Modelkit outputs using: vim `ls -rt /tmp/tmp* | tail -n 3 | tr -s '\n' ' '`
        if return_modelkit:
            if 'heat_setback' in args :
                _heatsp = idf_templater({"name": heatsp_nm, "setback": args['heat_setback']}, txt_thermsch_global_heat, tempsch_def_heat)
            else: _heatsp = idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat)
            if 'cool_setback' in args :
                _coolsp = idf_templater({"name": coolsp_nm, "setback": args['cool_setback']}, txt_thermsch_global_cool, tempsch_def_cool)
            else: _coolsp = idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool)
            #_wrap_str= lambda x: "'"+x+"'"
            _wrap_str= lambda x: '"'+x+'"'
            _strip_twolines= lambda x: _wrap_str( "\n".join( x.split('\n')[5:] ) )
            #_strip_twolines= lambda x:  '\n'.join( x.split('\n')[4:] )
            return _strip_twolines(_heatsp), _strip_twolines(_coolsp)

    def set_filenames(self):
        "Specify filename by adding file suffix as specified in `task_suffix` variable. By default, filenames are based on the `prep` filename"
        #mybldg.task_suffix= {

        if not self.task_suffix:
            raise NameError("Need to specify file suffix using 'mybldg.task_suffix= {'prep': '...'}'")
        elif not self.basename:
            raise NameError("Need to specify basename for file using 'mybldg.basename=string'")

        ep_extension='.'+self.basename.split('.')[-1]
        prep_suffix=self.task_suffix[0]
        prepfile = self.basename.replace(ep_extension, "_" + prep_suffix + ep_extension)

        # 'to_file' used for get_sql_database. Set to prep file
        global to_file
        to_file = prepfile

        self.task_filenames[prep_suffix]=prepfile
        _fn = lambda fnm, replace: fnm.replace(ep_extension, "_" + replace + ep_extension)
        remaining_tasks = list( self.task_suffix )
        remaining_tasks.pop(0) # prep is already named above. Use as basis for naming below
        for j,task in enumerate( remaining_tasks ):
              _ts=self.task_suffix[j+1]
              self.task_filenames[_ts ] = _fn(prepfile, _ts)

    def __abstract_model(self, objs_all):

        # TODO- deploy_if_function_list takes JSON OR [] directives
        new_objs = deploy_if_function_list( objs_all, self.tasks[self.next_task] )
        return new_objs

    #def generate(self, force_recreate=False, run_eplus=False):
    def generate(self, force_recreate=False, run_eplus=True):
        """"Generate genEPJ output (IDF/epJSON) as specified via task list.

        Parameters:

        * `force_recreate`: Force recreation of genEPJ output (IDF/epJSON) as specified in task list. If not set, no output will be create is a result file is found (SQL).
        * `run_eplus`: Allow E+ to be run on genEPJ output (IDF/epJSON).

        Returns:

        * `None`
        """
        #if __name__ == '__main__' and not callable(globals().get("get_ipython", None)):
        if run_eplus:
            print("Warning: 'run_eplus' is depreciated and will be removed in a future version")

        self.set_filenames()
        create_data_dir(self.basename)

        for k,task in self.tasks.items():
            if "prep" in k: nm= self.basename
            else:           nm= self.task_filenames["prep"]
            self.next_task= k
            #new_objs = run_eplus_and_createJSON(self.__abstract_model, nm, self.weather, suffix  = k,  run_eplus=self.config.run_eplus or run_eplus, force = self.config.force_recreate or force_recreate)
            new_objs = run_eplus_and_createEPlusInput(self.__abstract_model, nm, self.weather, suffix  = k, force = self.config.force_recreate or force_recreate, run_eplus= self.config.run_eplus or run_eplus)
            self.idf_objs=new_objs

            #if isinstance(new_objs, list):
            #    self.IDFS[k]= new_objs
            #elif isinstance(new_objs, dict):
            #    self.epJSON[k]= new_objs

    # All scenarios handled by generate(). Mark for deletition
    #def generate_opti(self, force_recreate=False, run_eplus=False ):

    #    print("TEST: option given to 'generate_opti'. run_eplus= ",run_eplus)
    #    if "opti" not in self.tasks:
    #        printc("'opti' tasks not defined. Nothing to do!", 'red')
    #    else:
    #        self.next_task= 'opti'
    #        __abstract_add_objs2file(self.__abstract_model, to_file=self.task_filenames["prep"], suffix='opti')
    #        if run_eplus: run_energyplus(self)



#======================================================
## Show all print/warning/sub statements from templater
#======================================================
#verbose.verbose_set(False) # This is the default behaviour
#verbose.verbose_set(True)
#verbose.verbose_set( mybldg.verbose_substitute )


#Search for last Uncommented line
#********************************
#G?^\s*[a-z]\+
#  SB: Very useful for generate_IDF script where I had several options commented out
# SB: Remapped to <Leader>uc

# TODO:
#Warning: Assumes that titles are identical
#  - No lower case/upper case comparisons

# TODO- Test UFAD and DV (Works with/without HVACTemplates? Works with IdealLoads?)


# TODO- Added function when writing objs to file
#  Remove IDENTICAL objects (if present)
#  WHY? Possible that when modifying window types that I may add multiple Material objects (ex. Argon gas)

# TODO- Add WINDOW 7 spectral properties to Window Template files

# TODO: Fix object match, Match all leading !-/! to the below object (including building descriptions)
# ^(!|!-)?.* !?!? Check is greedy or not. Want to match multiple lines with this

# TODO: mod_WWR is messing up following entries in FenestrationSurface:Detailed:
#, !- Multiplier
#, !- Number of Vertices

# TODO- Clean up SQL_FILE statements scattered over file. JUST HAVE ONE

# TODO- Input Options
# 1. ShadowCalculation object
# 2. Sepoint not met criteria: 1.0 C
# 3. Add FullInteriorWithReflections
# 4. Site:GroundTemperature:BuildingSurface
# 5. Site:GroundReflectance
# 6. ZoneCapacitanceMultiplier:ResearchSpecial == 10!?
# 7. Set infiltration from walls
#    - Set to loss per surface area

# TODO- Overhang Shading
#  * Still only works for South facing surfaces
#    - Want +- to control where shading is added
#    - Need unit directional vectors AWAY from wall

# Optimization Hooks:
#  * As a final step, add optimization fns to vary key parameters
#  * Ex. Mech system option
#  * Inputs: 1) Existing model, 2) CSV of variables

# TODO- Add BIPV/T instead of PV
# 1. Hook up directly into air/water loop (heat exchanger)
# 2. Run through a HP coil (can be a set COP using EMS to start)

# TODO- Add Solar thermal (residential cases only)

# TODO- Convert HVACTemplate Heatpump objects to use a GroundLoop (Convert ASHP to GSHP)
#  - Option 1: post-process the ExpandedIDF file
#    * Swap out air source condensor loop for ground source loop
#    * Expect better preformance than air loop
#    * JS wants: determine the yearly heat imbalance. What about non-typical heat/cooling years?

# TODO- Add Daylighting objects to each zone
#  * Control via opposing wall sensor (from window)
#    - Find exterior surface name. Find Wall exactly opposite from it
#    - Put sensor in the middle? of this wall (4ft up, in center?)

# TODO- Output Post-Processing
# 1. Heating/Cooling balance points
# 2. Other ASHRAE 14 calibrations
# 3. Hours spent at part load figure

# TODO- Residential Home Version
# Synopsis: Similar approach to before, but functionally implement various tech on a home
# Other Features
# 1. Automated zoning: where are the sweet spots? (savings from basement control different than loft control)
# 2. DHW savings: Keep in mind of co-incidental loads (system only works when tank is refill/charging)

# TODO- Quality Assurance
# 1. Annual EUI
#   * Compare is building (reference and proposed to existing buildings in Canadian building stock)
#   * Comparison: annual, base load, peak load
#   * Expect: savings in retirement to be proportional (EUI on existing retirement is so much higher than commercial. If EUI on proposed retirement is lower than proposed commercial-- You have a big issue)
# 2. Balance point of building
# 3. Spreadsheet estimates: Use EEI techniques to confirm savings
#    - Integrate with ESIM results to fill in spread sheets
#    - Work occurs in IPython, outputs to Excel (as an option)

# TODO- Implement Edge Cases
#  1. Attic Ins Construction, Type Ceiling, on other side of ExtRoof (Ex. Ventilated Attic)
#  2. Air leakage loss in duct work

# TODO- Features
# 4. Window Frames and Win7 objects

# TODO- Order IDF objects
# Refer to: idd_order_v81.py
# HOW2REBUILD: open idd file, :v/^\w.*,/d, save (DONE!)

from optparse import OptionParser

from shutil import copyfile, move, rmtree, copy, which

from time import sleep
from math import tan, atan, pi, sqrt
from random import randint, sample
from numpy import array, abs, matrix, cos, sin, tan, arctan, sqrt, dot, loadtxt, average, pi, floor
# Shapely: Calc area of polygons, Check if Point inside a given Polygon
#from shapely.geometry import Point, Polygon
from collections import deque
import sqlite3

from string import Template
from sys import exit, platform, path, argv # win/linux?

from subprocess import call, Popen, PIPE, run
from pathlib import Path

import re


parser = OptionParser()

# Work Flow:
# Scripted approach:
# 1. Build geometry in OpenStudio (manual)
# 2. Upgrade file to newest EPlus version (manual)
# 3. Copy/paste geometry into new template
# 4. Match/replace material definitions
# 5. Build equipment lists/nodes for various mech systems
#    Ex. CCASHP with earth tubes

# TODO:
# Ensure proper window constructions are used (WINDOW 6 output)
# 1. Remove unused schedules

parser.add_option("-t", "--toFile", dest="to_file",
    action="store", type="string",
    help="Templated IDF file to put geometry information into")

parser.add_option("-f", "--fromFile", dest="from_file",
    action="store", type="string",
    help="IDF file to take geometry information from")

parser.add_option("-D", "--debugall", dest="debugall",
    action="store_true",
    help="Set ALL debug flags and create additional Outputs during model creation.")

parser.add_option("-H", "--debughvac", dest="debughvac",
    action="store_true",
    help="Set HVAC debug flags and create additional Outputs during model creation.")

parser.add_option("-T", "--debugthermal", dest="debugtherm",
    action="store_true",
    help="Set Thermal debug flags and create additional Outputs during model creation.")

parser.add_option("-l", "--debuglight", dest="debuglight",
    action="store_true",
    help="Set Daylighting debug flags and create additional Outputs during model creation.")

parser.add_option("-e", "--debugelec", dest="debugelec",
    action="store_true",
    help="Set Electrical (Lights/Equipment) debug flags and create additional Outputs during model creation.")

parser.add_option("-p", "--debugpv", dest="debugpv",
    action="store_true",
    help="Set PV debug flags and create additional Outputs during model creation.")

parser.add_option("-s", "--debugshade", dest="debugshade",
    action="store_true",
    help="Set Shading debug flags and create additional Outputs during model creation.")

parser.add_option("-d", "--debugdhw", dest="debugdhw",
    action="store_true",
    help="Set DHW debug flags and create additional Outputs during model creation.")

parser.add_option("-E", "--debugenduse", dest="debugenduse",
    action="store_true",
    help="Set End-Use debug flags and create additional hourly Outputs during model creation.")

(options, args) = parser.parse_args()

# Done with options parsing
#parser.destroy()

to_file=options.to_file
fr_file=options.from_file


def set_debugall(flag):
    "Set all debug flags to `flag`"

    printc("\nDebugAll flag set. Creating outputs for reporting", "yellow")
    sleep(1.0)
    if flag:
        options.debughvac=True
        options.debugtherm=True
        options.debuglight=True
        options.debugelec=True
        options.debugpv=True
        options.debugshade=True
        options.debugenduse=True
        #print(args)
        #args['output_vars']=None
        #args['timestep']=None

    return True

if options.debugall:
    options.debughvac=True
    options.debugtherm=True
    options.debuglight=True
    options.debugelec=True
    options.debugpv=True
    options.debugshade=True
    options.debugenduse=True


# TODO: Added to cost_dict
use_suite_mtr = 1

# SIMULATION FEATURES
feat_dict=get_features("features.csv")

# Added to make genEPJ compatible with Charrette reporting
# Ex. ./diagnostics/diagnostic_plot_enduse_breakdown_hourly.py
if not to_file:
    to_file = ''

sql_file=to_file.replace('idf','sql').replace('data_temp/','data_temp/Output/')
conn = sqlite3.connect(sql_file)
c = conn.cursor()

# SB: Updated for use with JSON and Window/Unix/Mac friendly
def get_sql_database(myfile):
    """Helper function which takes inputted IDF filename and returns SQL file. Used to perform queries on geometry, orientations, volumes/areas, etc.

    Parameters:

    * `myfile`: input IDF used to create original genEPJ object list (Python `String`)

    Returns:

    * `c`: SQL cursor object for queries
    """
    if not myfile: myfile=to_file

    #sql_file=myfile.replace('idf','sql').replace('data_temp/','data_temp/Output/')
    ext=Path(myfile).suffix
    _bn=basename(myfile)
    _sn=_bn.replace(ext,'.sql')
    _path=join('data_temp','Output')
    sql_file= join(_path,  _sn)

    if (not isfile(sql_file)) and isfile( join('Output', _sn) ):
        sql_file= join('Output', _sn)

    if not isfile(sql_file):
        # Try again using '*out.sql' convention (post E+ 8.9)
        sql_file= join(_path,  _bn.replace(ext,'out.sql'))

    if isfile(sql_file):
        printc("> get_sql: Found database: %s"%(sql_file), 'green' )
        conn = sqlite3.connect(sql_file)
        c = conn.cursor()
        return c
    else: raise NameError("Invalid SQL File Specified!")

# SB- Historically 'to_file' supplied by: generate_IDF.py -t data_temp/*.idf
def guessdb_ifnot_found():
    """Attempts to find local database connection and return to user

    Parameters: None

    Returns:

    * `c`: SQL cursor object for queries
    """
    myfile=try2get(str, glob('*prep.idf') )
    #if not myfile:
    #if not isfile(myfile):
    if not myfile:
        myfile=try2get(str, glob(join('data_temp','*prep.idf') ))
    if not myfile:
        myfile=try2get(str, glob('*.idf') )
    if not myfile:
        myfile=try2get(str, glob(join('data_temp','*.idf') ))
    print("Trying SQL file: ", myfile)
    global c
    c = get_sql_database(myfile)
    return c


def add_capacitance_multi_file(to_file=to_file):
    """Modified version of `add_capacitance_multi` which creates an IDF output for testing purposes. File output uses suffix `_zoneCaps.idf` by default."""
    return __abstract_add_objs2file(add_capacitance_multi, to_file=to_file, suffix='zoneCaps')

def add_capacitance_multi(new_objs, args={}):
    """Add `ZoneCapacitanceMultiplier:ResearchSpecial` to air node with a default value.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with Air Capacitance specified (Python `List`)
    """

    #=========================
    # Template Zone Capacitors
    #=========================
    temp_zonecap, defs_zonecap = templ.zone_capacitance_research()

    obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='ZoneCapacitanceMultiplier:ResearchSpecial,']
    if len(obj_idxs)==0 :
        printc("\nInserting 'ZoneCapacitanceMultiplier:ResearchSpecial,'", "green")
        new_objs.insert(-1, idf_templater({}, temp_zonecap, defs_zonecap) )

    else:# Pre-existing object found, do nothing?
        printc("\nNOT Inserting 'ZoneCapacitanceMultiplier:ResearchSpecial' (Previously Found)", "yellow")
        # SB: Improve this substitute (do it my line?)
        #new_objs[obj_idx] = new_objs[obj_idx].replace('12,','1,',).replace('31','2')

    return new_objs

def change_run_period_file(to_file=to_file):
    """Modified version of `change_run_period` which creates an IDF output for testing purposes. File output uses suffix `_modrunperiod.idf` by default."""
    return __abstract_add_objs2file(change_run_period, to_file=to_file, suffix='modrunperiod')

# SB: Works only if start date is 1,1 and end data is 12,31
def change_run_period(new_objs, args={'end_mnth':12, 'end_day':31, 'start_mnth':1, "start_day":1}):
    """Modify E+ `RunPeriod` to shorten end Month and Day for simulation.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `end_month`/`end_day` Date to stop simulation at

    Returns:

    * `new_objs`: genEPJ object list with modified `RunPeriod` (Python `List`)
    """

    new_objs= list(get_IDF_objs_raw(new_objs))

    start_mnth = str(args['start_mnth'])
    start_day  = str(args['start_day'])
    end_mnth   = str(args['end_mnth'])
    end_day    = str(args['end_day'])
    #printc("Start date: %s/%s"%(start_day,start_mnth), 'yellow')
    #printc("End date: %s/%s"%(end_day,end_mnth), 'green')

    obj_idx = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='RunPeriod'][0]
    # SB: Improve this substitute (do it my line?)
    runperiod_obj=new_objs[obj_idx]
    #print(runperiod_obj)
    runperiod_lns=runperiod_obj.split('\n')
    runperiod_lns[2]=runperiod_lns[2].replace('1,', start_mnth+',') #!- Begin Month"
    runperiod_lns[3]=runperiod_lns[3].replace('1,', start_day+',') #!- Begin Day of Month"
    # idx+1 due to 'Begin Year' line (added in E+ v9)
    runperiod_lns[5]=runperiod_lns[5].replace('12,', end_mnth+',') #!- End Month
    runperiod_lns[6]=runperiod_lns[6].replace('31,', end_day+',') #!- End Day of Month
    runperiod_obj='\n'.join(runperiod_lns)
    #print(runperiod_obj)

    new_objs[obj_idx]=runperiod_obj
    #if start_mnth!=1 :
    #    pass
    #else:
    #    new_objs[obj_idx] = new_objs[obj_idx].replace('12,',str(end_mnth)+',',).replace('31',str(end_day))
    return new_objs

def swap_IDFJSON_file(to_file=to_file):
    """Modified version of `swap_IDFJSON` which creates an IDF output for testing purposes. File output uses suffix `_swapJSON.idf` by default."""
    return __abstract_add_objs2file(swap_IDFJSON, to_file=to_file, suffix='swapJSON')

# Given a dictionary (epJSON) or list (genIDF), swap to the alternative format and return a list or dictionary
def swap_IDFJSON(data, args={}): # pass IDF name through ARGS
    "Swap between epJSON/genEPJ formats"
    _fnm=mkstemp('_genEPJ')[1]
    printc("**swap_IDFJSON: Given format '%s'"%( str(type(data))), 'green')
    if isinstance(data, list): #E+ IDF (want epJSON)
        # SB: E+ will translate idf->epJSON during 'energyplus --convert' cmd call
        tempfnm=_fnm+'.idf' # new IDF name
        printc("**Writing IDF data for translation with len: %s"%(len(data)), 'green')
        write_file(data, tempfnm)
        new_tempfnm=convertJSON2IDF(tempfnm)
        new_data=get_JSON_objs_raw(new_tempfnm)
        #new_data=get_JSON_objs_raw(new_tempfnm, ordered=1)
        # TODO- SAVE IDF to tempdir (reread for object order and comments later)
    elif isinstance(data, dict): #E+ epJSON (want IDF)
        # SB: E+ will translate epJSON->idf during 'energyplus --convert' cmd call
        tempfnm=_fnm+'.epJSON' # new JSON name
        printc("**Writing epJSON for translation data with len: %s"%( len(data)), 'green')
        write_file(data, tempfnm)
        new_tempfnm=convertJSON2IDF(tempfnm)
        new_data=get_IDF_objs_raw(new_tempfnm)
        # Add back comments
        #new_data=add_comments_to_IDF(json_objs=data, idf_objs=new_data)

    printc("**swap_IDFJSON: Translated to format '%s'"%( str(type(new_data))), 'green')

    ## Clean up
    #bs_nm=basename(_fnm)
    ##cleanup /tmp/*EPJ*     ./*tmp*EPJ*   ./eplus*  ./data_temp/*tmp*EPJ
    #_files=[     _fnm+'*',  '*'+bs_nm+'*', 'eplus*', join('data_temp', '*'+bs_nm+'*'), 'sqlite.err' ]
    #_glob_files=[]
    #[_glob_files.extend( glob(_f) ) for _f in _files]
    #[ remove(_f) for _f in _glob_files ]

    # TODO- add comments back if JSON2IDF. Load order of objects from prep IDF!? Keep file during first translation?

    return new_data

def _is_all_strs(mylist):
    t=[ type(l)==str for l in mylist ]
    return all(t)


import tempfile
from eppy.modeleditor import IDF
def swap_EPPYIDF_file(to_file=to_file):
    """Modified version of `swap_EPPYIDF` which creates an IDF output for testing purposes. File output uses suffix `_swapEPPY.idf` by default."""
    return __abstract_add_objs2file(swap_EPPYIDF, to_file=to_file, suffix='swapEPPY')

def swap_EPPYIDF(data, args={}):
    """Translate provided data from eppy/genEPJ to genEPJ/eppy

    Parameters:

    * `data`: genEPJ object list (Python `List`) OR eppy object
    * `args`: optional arguments (not used)

    Returns:

    * `new_data`: genEPJ/eppy data
    """

    if 'IDD' in args :
        iddfile = args['IDD']
        IDF.setiddname(iddfile)
    else:
        printc("EPPY needs IDD file. Guessing from environment variables.", 'yellow')
        eplus_dir = environ['ENERGYPLUS_DIR']
        iddfile=join( eplus_dir, 'Energy+.idd' )
        if isfile(iddfile):
            printc("Found IDD: %s"%(iddfile), 'green')
        IDF.setiddname(iddfile)

    # eppy file. Want genEPJ
    if type(data)==IDF:
        idfstr= IDF.idfstr( data )
        new_data = get_IDF_objs_raw(idfstr)

    # genEPJ file. Want eppy
    elif ( isinstance(data, list) and _is_all_strs(data) ): # genIDF/EPJ
        idfstr = combine_objects( data )
        temp = tempfile.NamedTemporaryFile()
        #temp.write( bytes(idfstr, 'utf-8') ) # OR mystring.encode('utf-8')
        temp.write( idfstr.encode('utf-8') ) # OR mystring.encode('utf-8')
        new_data= IDF(temp.name)
        temp.close()

    printc("**swap_EPPYIDF Translated to format '%s'"%( str(type(new_data))), 'green')

    return new_data


# HACK- rewrite using recursion. MARK for refactor
# https://stackoverflow.com/questions/14692690/access-nested-dictionary-items-via-a-list-of-keys
def set_nested_JSON(myjson, mykeys, myval):
    "Set JSON object up to five layers deep. Mark for refactor to consider JSON modifications up to N deep."

    if len(mykeys)==2 :
        myjson[ mykeys[0] ][ mykeys[1] ] = myval
    elif len(mykeys)==3 :
        myjson[ mykeys[0] ][ mykeys[1] ][ mykeys[2] ] = myval
    elif len(mykeys)==4 :
        myjson[ mykeys[0] ][ mykeys[1] ][ mykeys[2] ][ mykeys[3] ] = myval
    elif len(mykeys)==5 :
        myjson[ mykeys[0] ][ mykeys[1] ][ mykeys[2] ][ mykeys[3] ][ mykeys[4] ]  = myval
    elif len(mykeys)==6 :
        myjson[ mykeys[0] ][ mykeys[1] ][ mykeys[2] ][ mykeys[3] ][ mykeys[4] ][ mykeys[5] ]  = myval

    return True
    #return myjson


# SB: Improved but still buggy- Sat 07 Dec 2019 01:38:43 PM EST
#import json
#def to_json(d):
#    "Convert dict() to JSON"
#    return json.dumps(d)
#
#def is_json(myjson):
#    try:
#        json_object = json.loads(myjson)
#    except ValueError as e:
#        return False
#    return True
#
#def nested_set(d, keys, value):
#    for key in keys[:-1]:
#        d = d.setdefault(key, {})
#    d[keys[-1]] = value
#
## Set nested JSON values. Allows for wild cards using '*' (iterate over JSON and sub ALL values)
#def set_nested_JSON(myjson, mykeys, myval):
#    "Set nested JSON values. Allows for wild cards using '*' (iterate over JSON and sub ALL values)"
#    return to_json( nested_set(myjson, mykeys, myval) )

def mod_JSON_file(to_file=to_file):
    """Modified version of `mod_JSON` which creates an IDF output for testing purposes. File output uses suffix `_modJSON.idf` by default."""
    return __abstract_add_objs2file(mod_JSON, to_file=to_file, suffix='modJSON')

# Modify objects present list of objects
#      [ mod_JSON, True, {'obj': 'Building', 'key': 'north_axis', 'val': '10.0' } ],
def mod_JSON(objs_all, args={} ):
    """Modifies generic JSON key-value pairs to epJSON

    Parameters:

    * `objs_all`: genEPJ JSON (Python `json`)
    * `args`: valid epJSON key-pair (can be several key-pairs) (Python `dict`)

    Returns:

    * `new_objs`: genEPJ JSON (Python `Dict`)
    """
    # TODO- Is object present? If not, return unmodified objs_all

    pre_objs=objs_all

    #if 'obj' in args:
    #else:
    try:
        obj_nm=list(args.keys())[0]
        print(obj_nm)
    except:
        printc("Object name not supplied in args: %s"%(str(args)), 'red' )
        return pre_objs

    # convert to JSON if wrong file type
    # Allows for testing using IDF format via script genEPJ/standalone/run_genEPJ_functions.sh
    if isinstance(objs_all, list) :
        objs_all=swap_IDFJSON(objs_all)

    new_objs=objs_all

    # iterate over all provided options
    for _key,_val in args[obj_nm].items():

        # Two paths:
        # 1. object is immediately accessible at layer 0
        if '>' not in obj_nm:
            _obj=new_objs[ obj_nm ]
            #print(_obj)
            payload={ _key: _val}

            # TODO- Take first entry OR iterate over all in future?
            mykey=list( _obj.keys()  )[0]
            print("Modifying '%s':'%s' object: '%s' (id: %s)"%( _key, _val, obj_nm, mykey ) )
            _obj[mykey].update(payload)
        # 2. object is deeply embedded ('>' in _key)
        else:
            _keys=obj_nm+'>'+_key
            printc("Modifying '%s': %s"%( _keys, _val), 'green' )
            set_nested_JSON( new_objs, _keys.split('>'), _val)

            # SB: Stopped due to complexity. Want to sub multiple matches of '*' or just *one*?
            #def key_wild_card(_json, _keys_str):
            #    _keys=_keys_str.split('>')

            #    # No wild cards to match
            #    if '*' not in _keys_str: return _keys

            #    else: # SB: Need to match '*', '*ExtWall*Insul', etc
            #        _keys= _keys_str.split('>')
            #        new_keys= list(_keys)
            #        _d=_json #json dictionary at highest level
            #        _i=0
            #        for _k in _keys:
            #            _d=_d[_k]
            #            if ((_i == len(keys)-1) and ('*' in _d)) :
            #                if '*' in str(_d): printc("set_JSON ERROR: Can't set values using wild cards: {}".format(_keys_str), 'red')
            #            elif ( ('*' in _k) and () ): pass
            #            else: # need to go deeper...
            #                d=d[_k]
            #            _i=_i+1
            #    ## SB: Test for more than one match. Throw error

            #new_objs=set_nested_JSON( new_objs, key_wild_card(_keys), _val)

    return new_objs

def add_JSON_file(to_file=to_file):
    """Modified version of `add_JSON` which creates an IDF output for testing purposes. File output uses suffix `_addJSON.idf` by default."""
    return __abstract_add_objs2file(add_JSON, to_file=to_file, suffix='addJSON')

# Add an entirely new object to list of objects
def add_JSON(objs_all, args={} ):
    """Adds generic JSON key-value pairs to epJSON

    Parameters:

    * `objs_all`: genEPJ JSON (Python `json`)
    * `args`: valid epJSON key-pair (can be several key-pairs) (Python `dict`)

    Returns:

    * `new_objs`: genEPJ JSON (Python `Dict`)
    """
    pre_objs=objs_all

    #if 'obj' in args:
    #    obj_nm=list(args.keys())[0]
    #    print(obj_nm)
    #else:
    #   printc("Object name not supplied in args: %s"%(str(args)), 'red' )
    #   return pre_objs
    try:
        obj_nm=list(args.keys())[0]
        print(obj_nm)
    except:
        printc("Object name not supplied in args: %s"%(str(args)), 'red' )
        return pre_objs

    # convert to JSON if wrong file type
    # Allows for testing using IDF format via script genEPJ/standalone/run_genEPJ_functions.sh
    if isinstance(objs_all, list) :
        objs_all=swap_IDFJSON(objs_all)

    new_objs= objs_all

    #ep_obj_nm=args['obj']
    try:
        ep_obj_nm=list(args.keys())[0]
    except AttributeError: # handle failure if passed {'EP_OBJ_NAME'} without key/value pair, ie: {'EP_OBJ_NAME': {}}
        ep_obj_nm=args.pop()

    def _is_in(mykey,mydict):
        try:
            mydict[mykey]
            return True
        except:
            return False


    # Check that object doesnt already exist
    if _is_in(ep_obj_nm, objs_all):
        #printc("Error: '%s' already exists in epJSON. Do Nothing"%(ep_obj_nm), 'red')
        #return objs_all
        printc("Warning: '%s' already exists in epJSON. Default behaviour is to OVERRIDE"%(ep_obj_nm), 'yellow')

    #args.pop('obj') #remove EP_obj_nm
    try:
        payload=args[ep_obj_nm]
    except TypeError: # handle failure if passed {'EP_OBJ_NAME'} without key/value pair, ie: {'EP_OBJ_NAME': {}}
        payload={}
    template,defaults,required=get_template_defaults_required(ep_obj_nm)
    if _is_in('defaults', payload):
        defaults=payload['defaults']
    if _is_in('template', payload):
        template=payload['template']

    new_template=templater( {}, template, defaults )

    #Finally, add template to epJSON dict
    #nm_conv= ep_obj_nm.replace(':',' ')+" 1"  # REQUIRED E+ naming convention of objects. TODO- iterate over all additions
    nm_conv= ep_obj_nm+" 1"  # REQUIRED E+ naming convention of objects. USE SAME OF E+ Devs
    #print(nm_conv)
    print({ep_obj_nm: {nm_conv: new_template} })
    new_objs.update({ep_obj_nm: {nm_conv: new_template} })
    return new_objs


## TODO-
#def append_JSON_data(objs_all, args={} ):
#   """Append JSON obj to a pre-existing JSON object "data": [...] structure. For example: Schedule:Compact"""
#   pass
#
## TODO-
#def append_JSON(objs_all, args={} ):
#    """Append JSON obj to a pre-existing JSON name object. For example: "Zone": { "nm1": ..., "nm2": ...}"""
#    new_objs= objs_all
#    return new_objs

#********************************** }}}

def add_test_OutputTables_file(to_file=to_file):
    """Modified version of `add_OutputTables` which creates an IDF output for testing purposes. File output uses suffix `_HTMLkWh.idf` by default."""
    return __abstract_add_objs2file(mod_OutputTables, to_file=to_file, suffix='HTMLkWh')

def mod_OutputTables(objs, args={} ):
    """Modify E+ `OutputControl:Table:Style` to use evil units (kWh, kWh/m2).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with modified `OutputControl:Table:Style` to kWh (Python `List`)
    """
    new_objs=list(objs)
    tbl_objs=filter_IDF_objs_raw(objs, 'OutputControl:Table:Style')
    obj_idxs = [i for i,obj in enumerate(objs) if get_obj_type(obj)=='OutputControl:Table:Style']

    # Template for OutputControl:Table:Style,
    output_temp,output_defs=templ.template_output_control()
    output_formatted=idf_templater({}, output_temp, output_defs)

    # ASSUME only one OutputControl:Table:Style, E+ will throw error if several
    if len(tbl_objs)==0 :
        printc("Adding OutputControl:Table:Style object", 'green')
        new_objs.insert(-1, output_formatted )
    elif (len(tbl_objs)==1) and any(map(lambda x: 'JtoKWH' not in x, tbl_objs)):
        new_objs[obj_idxs[0]] = output_formatted
        printc("Modifying existing OutputControl:Table:Style object", 'green')
    elif (len(tbl_objs)==1) and any(map(lambda x: 'JtoKWH' in x, tbl_objs)):
        printc("Found a valid OutputControl:Table:Style object", 'green')
    #except Error,e:
    #    print(e)
    #    printc("Error in Modifying OutputControl:Table:Style", 'red')

    return new_objs

def mod_SolarDistribution_file(to_file=to_file):
    """Modified version of `add_SolarDistribution` which creates an IDF output for testing purposes. File output uses suffix `_SolarDis.idf` by default."""
    return __abstract_add_objs2file(mod_SolarDistribution, to_file=to_file, suffix='SolarDis')

def mod_SolarDistribution(objs_all, args={} ):
    """Modify E+ `SolarDistribution` to `FullExterior` or `FullInteriorAndExterior`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    `SolarDistribution` is set in the feature dictionary.

    Returns:

    * `new_objs`: genEPJ object list with modified `SolarDistribution` (Python `List`)
    """
    new_objs=list(objs_all)
    #tbl_objs=filter_IDF_objs_raw(objs, 'OutputControl:Table:Style')
    bldg_idx = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='Building'][0]
    obj = new_objs[ bldg_idx ]

    # SB: OpenStudio v1.4 doesn't add azimuth by default. Add if none existent
    azi_regex=re.compile(r'[-\d.]*,[ ]+!- North Axis {deg}')
    aziline=azi_regex.findall(obj)[0]
    if ''==aziline.split(',')[0]:
        printc("Adding default Azimuth to blank 'Building' object", 'green')
        myobj=obj.replace(aziline, "%.1f,           !- North Axis {deg}"%(0.0))
    else:
        myobj=obj

    solar_dist = feat_dict["solardistribution"]
    if solar_dist==1 :
        sd='FullExterior'
    elif solar_dist==2 :
        sd='FullInteriorAndExterior'
    else: raise ValueError("Invalid Solar Distribution Option")
    solar_regex=re.compile(r'[\w]*,[ ]+!- Solar Distribution')
    sdline = solar_regex.findall(myobj)[0]
    printc("Modifying Solar Distribution in 'Building' object: %s"%(mkcolor(sd,'yellow')), 'green')
    myobj=myobj.replace(sdline, "%s,      !- Solar Distribution"%(sd))

    new_objs[ bldg_idx ] = myobj

    return new_objs

def mod_pd_file(to_file=to_file):
    """Modified version of `mod_pd` which creates an IDF output for testing purposes. File output uses suffix `_modPD.idf` by default."""
    return __abstract_add_objs2file(mod_pd, to_file=to_file, suffix='modAzi')

def mod_pd(objs_all, args={ 'name': 'Lights', 'frac': 1.0} ):
    """Modify power density of E+ `Lighting/ElectricalEquipment` objects.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `frac` Multiply `Watts/Area` value by fraction `frac` (default is 1.0 or 0% reduction/increase).

    Returns:

    * `new_objs`: genEPJ object list with modified lighting/electric equipment power density (Python `List`)
    """

    nm=args['name']
    frac=args['frac']
    objs=list(objs_all)

    iter_objs=list(objs)
    mod_objs=filter_IDF_objs_raw(objs, nm)
    mod_objs=[obj for obj in mod_objs if 'Watts/Area' in obj]
    for i,obj in enumerate(iter_objs):
        if obj in mod_objs:
            objs[i]=set_obj_PowerDensity(obj, frac)

    # Added for EvePark (equipment loads specified in Watts)
    mod_objs=filter_IDF_objs_raw(objs_all, nm)
    mod_objs=[obj for obj in mod_objs if 'EquipmentLevel' in obj]
    iter_objs=list(objs) # Keep modified objects above
    for i,obj in enumerate(iter_objs):
        if obj in mod_objs:
            objs[i]=set_obj_Power(obj, frac)


    if options.debugelec:
        if 'light' in nm.lower():
            objs.insert(-1, "Output:Variable,*,Lights Electric Power,hourly;")
        elif 'electricequipment' in nm.lower():
            objs.insert(-1, "Output:Variable,*,Electric Equipment Electric Power,hourly;")
        else:
            raise ValueError("mod_pd fn: Modifying a non-classified power density end-use")

    return objs


def mod_azi_file(to_file=to_file):
    """Modified version of `mod_azi` which creates an IDF output for testing purposes. File output uses suffix `_modAzi.idf` by default."""
    return __abstract_add_objs2file(mod_azi, to_file=to_file, suffix='modAzi')

def mod_azi(objs, args={ 'azi': 0.0}):
    """Modify E+ `Azimuth` for `Building`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `azi` Azimuth with range from 0-360 (0->South, 90->East, 180->North, 270->West)

    Returns:

    * `new_objs`: genEPJ object list with modified Azimuth (Python `List`)
    """

    objs=list(get_IDF_objs_raw(objs))

    azi=float( args['azi'] )

    # Check that Azimuth is within expected limits
    if azi>=360 :
        printc("Azimuth limit exceeded: %s. Changing to: %.1f"%(mkcolor("%.1f"%(azi),'yellow'), azi-360),'red')
        azi=azi-360
    elif azi<0 :
        printc("Azimuth limit exceeded: %s. Changing to: %.1f"%(mkcolor("%.1f"%(azi),'yellow'), azi+360),'red')
        azi=azi+360

    iter_objs=list(objs)
    mod_objs=filter_IDF_objs_raw(objs, 'Building')
    #-0,                      !- North Axis {deg}
    #azi_regex=re.compile(r'[.-\d.]+,[ ]+!- North Axis {deg}')
    #print(mod_objs)
    if "!-" in mod_objs[0]:
        old_val=get_obj_abstract(mod_objs[0],2)
    else:
        old_val=get_obj_abstract(mod_objs[0],2, args={'trim_comments': False})
    azi_regex=re.compile(r'[-\d.]+,[ ]+!- North Axis|[-\d.]+;[ ]+!- North Axis|{}[,;]'.format(old_val)) # Added ';' option as JSON trims unnecessary info
    for i,obj in enumerate(iter_objs):
        if obj in mod_objs:
            lns=obj.split('\n')
            aziline=azi_regex.findall(obj)[0]
            #print("FOUND: ",aziline)
            #myobj=obj.replace(aziline, "%.2f,      !- North Axis {deg}"%(azi))
            if old_val+';' in aziline:
                myobj=obj.replace(aziline, "  %.2f;      !- North Axis"%(azi))
            else:
                myobj=obj.replace(aziline, "%.2f,      !- North Axis"%(azi))
            old_azi=get_obj_abstract(obj,2)
            print("Replacing Azimuth of 'Building' from '%s' to '%s'"%(mkcolor(old_azi,'yellow'), mkcolor(str(azi),'yellow')))
            objs[i]=myobj

    return objs


def mod_DHW_obj(myobj,frac=0.8):
    """Modify Domestic Hot Water E+ `'WaterUse:Equipment' object FlowRates by multiplying by fraction `frac` (default is 0.8 or 20% reduction).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with modified `WaterUse:Equipment` (Python `List`)
    """
    dhw_name=get_obj_name(myobj)
    try:
        old_flow=get_obj_abstract(myobj,3)
        new_flow=frac*float(old_flow)
        print("Modifying DHW of '%s' from '%s' to '%s'"%(mkcolor(dhw_name,'yellow'), mkcolor(old_flow,'yellow'), mkcolor(str(new_flow),'yellow')))
        myobj= myobj.replace(old_flow, "%.5g"%(new_flow))
    except:
        print("Error replacing DHW of '%s'"%(mkcolor(dhw_name,'yellow')))
    return myobj

def mod_DHW_objs_file(to_file=to_file):
    """Modified version of `mod_DHW_objs` which creates an IDF output for testing purposes. File output uses suffix `_modDHWeq.idf` by default."""
    return __abstract_add_objs2file(mod_DHW_objs, to_file=to_file, suffix='modDHWeq')

def mod_DHW_objs(objs,args={'frac':0.8}):
    """Modify ALL Domestic Hot Water E+ `WaterUse:Equipment` objects.

    Parameters:

    * `objs`: genEPJ object list (Python `List`)
    * `args`: `frac` Multiply FlowRates by fraction `frac` (default is 0.8 or 20% reduction).

    Returns:

    * `objs`: genEPJ object list with modified E+ `WaterUse:Equipment` flowrates (Python `List`)
    """
    iter_objs=list(objs)
    frac = args['frac']
    mod_objs=filter_IDF_objs_raw(objs, 'WaterUse:Equipment')
    mod_objs=[obj for obj in mod_objs if 'Peak Flow Rate' in obj]
    for i,obj in enumerate(iter_objs):
        if obj in mod_objs:
            objs[i]=mod_DHW_obj(obj, frac)

    return objs

def _mod_People_ASHRAE55_off(plp_obj):
    # Have to spec CO2 or your get IDD errors
    lns="""
    0,                       !- Carbon Dioxide Generation Rate
    No;                      !- Enable ASHRAE 55 Comfort Warnings
"""
    plp_obj=plp_obj.replace(';',',')
    return plp_obj+'\n'+lns

def _filter_surf_obj_by_type(mytype, surf_objs):
    #return [obj for obj in surf_objs if get_surf_type(obj).lower() == mytype.lower()]
    return [obj for obj in surf_objs if get_surf_type(obj) == mytype]

def _get_surf_coordin(surf):
    surf_lst=surf.split(',')
    cor_re=re.compile(r'([ \d.eE-]+),([ \d.eE-]+),([ \d.eE-]+)')
    cor=array(cor_re.findall(surf),dtype=float)
    return cor

def _get_zone_coordin(zn):
    x=get_obj_abstract(zn, 3)
    y=get_obj_abstract(zn, 4)
    z=get_obj_abstract(zn, 5)
    zn_coor=array([x,y,z],dtype=float)
    #print("Found coordinates in obj '%s': "%(get_obj_name(zn)), zn_coor)
    return zn_coor

def surf_is_tilted(cor):
    "Return true is the surface coordinates provided are tilted (ie. not vertical)"
    # Test if any surfaces are tilted (x,y,z) coordinates dont all match for every coordinate
    temp=[]
    #print('Tilt test: ',cor)
    for i in range(3): #check x,y,z coordinates
        #print('Tilt cor compare: ',cor[:,i])
        temp.append( all(e == cor[:,i][0] for e in cor[:,i]) )
    return not any(e == True for e in temp)

#NOTE: Other method to calc areas:
# 1. translate vectors to origin (one vector has [0,0] as point) (subtract all points by differing point from origin)
# 2. calc determinient of resulting matrix
def _calc_area5(surf,loc):
    # http://www.mathopenref.com/coordpolygonarea.html
    # Area of polygon: A = 1/2 * (x1*y2 + y1*x2 + (x2*y3 - y2*x3) + ... + )
    cor=array(_get_surf_coordin(surf))
    #print("is Tilted? ",surf_is_tilted(cor))
    #print("Coord for %s: "%(get_obj_name(surf)), cor)
    if len(cor)>4 :
        printc("Area calculations may not be accurate for surface: %s (%d surfaces)"%(mkcolor(get_obj_name(surf),'yellow'), len(cor)),'red')
    temp1=[]
    temp2=[]
    if loc=='Floor':
        for i in range(0,len(cor)-1):
            temp1.append(cor[i][0]*cor[i+1][1] - cor[i+1][0]*cor[i][1])
        area=abs(sum(temp1))/2.0
    elif loc=='Wall':
        for i in range(0,len(cor)-1):
            temp1.append(cor[i][0]*cor[i+1][1] - cor[i+1][0]*cor[i][1])
            temp2.append(cor[i][0]*cor[i+1][2] - cor[i+1][0]*cor[i][2])
        area1=abs(sum(temp1))/2.0
        area2=abs(sum(temp2))/2.0
        print("Areas: a1 %.2f, a2 %.2f"%(area1,area2))
        if   area1>=area2: area=area1
        elif area1<area2: area=area2
    #elif loc=='Roof': # NOTE- Slope roofs not presently implemented
    elif surf_is_tilted(cor):
        area=0
        print("Tilted Surfaces not implemented: %s"%(mkcolor(get_obj_name(surf),'yellow')))
    #print(temp)
    print("%s Area (%d cor): %s, Type: %s, BC: %s, Area: %.2fm2"%(loc,len(cor),mkcolor(get_obj_name(surf),'yellow'),mkcolor(get_obj_abstract(surf,2),'blue'),mkcolor(get_obj_abstract(surf,5),'green'),area))
    return area


# SQL alternative to other calc_area alternatives
# TODO/NOTE- Can actually use each construction index to make select statement
#  Ex. Net Area of all above grade Walls with Construction type 1
def _calc_area(surf,loc):
    surf_nm=get_obj_name(surf).upper()
    #sql_file=to_file.replace('idf','sql').replace('data_temp/','data_temp/Output/')
    #conn = sqlite3.connect(sql_file)
    #c = conn.cursor()
    sql_sel='SELECT GrossArea from Surfaces WHERE SurfaceName="%s";'
    res = c.execute(sql_sel %(surf_nm)).fetchone()
    if len(res)>1 :
        printc("WARNING! More than one area returned for surface: %s"%(mkcolor(surf_nm, "blue")), "yellow")
    a1=res[0]
    a1 = zeroIfNone(a1)
    return a1

def _calc_areas(objs_surf,loc='Floor'):
    areas=[_calc_area(s,loc) for s in objs_surf]
    return areas

def _calc_area_zone(zn):
    c = get_sql_database(to_file)
    sql_sel_zonenm='select SUM(a.GrossArea) FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Floor" AND a.ZoneIndex==b.ZoneIndex AND b.ZoneName=="%s";'
    #printc(sql_sel_zonenm%(zn.upper()), 'red')
    res = c.execute(sql_sel_zonenm%(zn.upper())).fetchone()
    #print("Raw Res: ", res)
    if len(res)>1 :
        printc("WARNING! More than one area returned for Zone %s"%(mkcolor(zn, "blue")), "yellow")
    a1=res[0]
    a1 = zeroIfNone(a1)
    return a1

# SQL alternative to other calc_area alternatives
# TODO/NOTE- Can actually use each construction index to make select statement
#  Ex. Net Area of all above grade Walls with Construction type 1
def _calc_area_intmass(zone_nm):

    grow_fac=2.0 #Factor to scale area results by: Exactly matches RefBldg's in E+/ExampleFiles
    sql_sel='select SUM(a.GrossArea)*%d FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Floor" AND a.ZoneIndex==b.ZoneIndex AND b.ZoneName=="%s";'
    res = c.execute(sql_sel %(grow_fac, zone_nm)).fetchone()
    if len(res)>1 :
        printc("WARNING! More than one area returned for Zone %s"%(mkcolor(zone_nm, "blue")), "yellow")
    a1=res[0]
    a1 = zeroIfNone(a1)
    if a1<=0.0 :
        printc("WARNING! Zero area returned for Zone %s"%(mkcolor(zone_nm, "blue")), "red")
    return a1

def calc_centroid(zone, c):
    """Returns the geometric centriod for a provided zone

    Parameters:

    * `zone`: Name of Zone to determine centroid for
    * `c`: sql database connection

    Returns:

    * `x`: x coordinates
    * `y`: y coordinates
    """
    zn_nm=get_obj_name(zone).upper()
    sql_sel='SELECT OriginX,OriginY,CentroidX,CentroidY from Zones WHERE ZoneName="%s";'
    sql_dat = c.execute(sql_sel %(zn_nm)).fetchone()
    x0 = sql_dat[0]
    y0 = sql_dat[1]
    x1 = sql_dat[2]
    y1 = sql_dat[3]
    return (x1-x0,y1-y0)

## TODO-Refactor: Works for PV surfaces ONLY. Rename this function or make it more generalized
#def filter_surf_by_azi(surf_objs, azi=180, pm=20):
#    sql_file=to_file.replace('idf','sql').replace('data_temp/','data_temp/Output/')
#    conn = sqlite3.connect(sql_file)
#    c = conn.cursor()
#    pvwall_sql_sel='SELECT SurfaceName from Surfaces WHERE ClassName=="Wall" AND Azimuth>%d AND Azimuth<=%d AND ExtBoundCond=0'
#    pvroof_sql_sel='SELECT SurfaceName from Surfaces WHERE ClassName=="Roof" AND ExtBoundCond=0'
#    pv_wall_names=c.execute(pvwall_sql_sel%(azi-pm/2., azi+pm/2. )).fetchall()
#    pv_roof_names=c.execute(pvroof_sql_sel).fetchall()
#    #print("PV wall names: ",pv_wall_names)
#    return pv_wall_names+pv_roof_names
#
#def filter_surf_by_azi2(surf_objs, azi=180, pm=20):
#    filt_surfs=[]
#    for surf in surf_objs:
#        surf_name=get_obj_name(surf)
#        surf_nc=trim_comments(surf)
#        coor = _get_surf_coordin(surf_nc)
#        if len(coor)==3 : #triangle surface, take last two coordinates
#            y1=coor[-1][1]
#            y2=coor[-2][1]
#            x1=coor[-1][0]
#            x2=coor[-2][0]
#        elif len(coor)==4 : #square surface, take middle two coordinates
#            y1=coor[-3][1]
#            y2=coor[-2][1]
#            x1=coor[-3][0]
#            x2=coor[-2][0]
#        else:
#            printc("Warning: GetAzi: Can't handle Surface '%s' found with %d vertices."%(surf_name,len(coor)),'red')
#            #x1, x2, y1, y2 = 0,0,0,0
#
#        #calc_azi=rad2deg(atan( abs(y2-y1)/abs(x2-x1) ))
#        calc_azi=rad2deg(atan( (x2-x1)/(y2-y1) ))
#        print("Surface %s with orientation %.1f"%(surf_name,calc_azi))
#        pass
#        if azi-pm<=calc_azi<=azi+pm:
#            filt_surfs.append(surf)
#    return filt_surfs

#def rm_obj_by_type(obj_type, myobjs):
def rm_obj_by_type(objs_all, args={}):
    "Remove E+ object type `obj_type` from genEPJ List `myobjs`"

    # Old way look for exact matches
    #return [obj for obj in myobjs if get_obj_type(obj)!=obj_type]
    if 'type' in args :
        obj_type=args['type']
    else:
        printc("Object type not provided. Do nothing!",'red')
        return objs_all

    # New statement allows for pseudo glob statements
    #return [obj for obj in myobjs if obj_type not in get_obj_type(obj)]
    if 'nm' in args :
        _nm= str( args['nm'] )
        return [obj for obj in objs_all if ( (obj_type not in get_obj_type(obj)) and (_nm not in get_obj_name(obj) ) )]
    else:
        return [obj for obj in objs_all if obj_type not in get_obj_type(obj)]

# Filter using raw text only
def filter_IDF_objs_raw(objs, mytype):
    """Reduce provided genEPJ `List` to only E+ objects with type==`mytype`

    Filter function allow for later parameter extraction and updates (eg. modify only `Zone` objects via `filter_IDF_objs_raw(objs, 'Zone')`)

    Parameters:

    * `objs`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with only objects which are type `mytype` (Python `List`)
    """
    return [obj for obj in objs if get_obj_type(obj)==mytype]

def _get_surf_BC(myobj):
    # TODO: Write test to make sure myobj is type 'BuildingSurface:Detailed'
    if 'Space Name' in myobj: # E+ v9.6 adds 'Space Name' to 'BuildingSurface:Detailed'
        _idx=6
    else:
        _idx=5
    no_com = trim_comments(myobj)
    #print(no_com)
    return no_com.split(',')[_idx].strip(' ').strip('\r').strip('\n')

# Filter all surfaces with Outdoor boundary condition (should be ground)
def filter_surf_by_extBC(surfs):
    """Reduce provided genEPJ `List` to only E+ `BuildingSurface:Detailed` objects with Outside Boundary Condition==`Outdoors`

    Filter function allow for later parameter extraction and updates (eg. modify only Exterior `BuildingSurface:Detailed` objects via `filter_surf_by_extBC(objs)`)

    Parameters:

    * `objs`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with only objects which are `Exterior` ``BuildingSurface:Detailed` objects (Python `List`)
    """
    # TODO: Test that object is 'BuildingSurface:Detailed'
    return [surf for surf in surfs if ((_get_surf_BC(surf)=='Outdoors') and (get_surf_type(surf)=='Wall'))]

# Filter all surfaces with Outdoor boundary condition (should be ground)
def filter_surf_by_zone(surfs, zonenm):
    """Reduce provided genEPJ `List` to only E+ `BuildingSurface:Detailed` objects with Zone Name==`zonenm`

    Filter function allow for later parameter extraction and updates (eg. modify only `BuildingSurface:Detailed` objects via `filter_surf_by_zone(objs, 'Zone 1')`)

    Parameters:

    * `objs`: genEPJ object list (Python `List`)
    * `args`: `zonenm` Zone Name that user wants to examine/modify/add details

    Returns:

    * `new_objs`: genEPJ object list with only `BuildingSurface:Detailed` with Zone Name `zonenm` objects (Python `List`)
    """
    # TODO: Test that object is 'BuildingSurface:Detailed'
    return [surf for surf in surfs if get_surf_zone(surf)==zonenm]


def _most_common(lst):
    return max(set(lst), key=lst.count)

def align_IDF_objs_file(to_file=to_file):
    """Modified version of `align_IDF_objs` which creates an IDF output for testing purposes. File output uses suffix `_aligned.idf` by default."""
    return __abstract_add_objs2file(align_IDF_objs, to_file=to_file, suffix='aligned')

# BEWARE: this object will change EUI by around 0.3% in a one month period
def align_IDF_objs(objs, arg={}):
    """Aligns comment symbols ('!-') in IDF with in a genEPJ file.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list aligned comments symbols (Python `List`)
    """
    myobjs=list(objs)

    # Get index of '!-' in a random object
    notFound=True
    #print("Len Objs: ",len(myobjs))
    mc_idxs=[]
    for j in range(20): # Take most common spacing indice from N IDF objects
        ind=randint(0,len(myobjs)-1)
        comment_indexs=[l.index('!-') for l in myobjs[ind].split('\n') if '!-' in l]
        try:
            mc_index=_most_common(comment_indexs)
            mc_idxs.append(mc_index)
            #print('Most Common Indices: ',_most_common(comment_indexs),comment_indexs)
        except ValueError: # Happens only if no common elements are found
            pass

    print('align_IDF_objs: Most Common Index: %d'%(_most_common(mc_idxs)))

    #fmt_str='{code:<30} !- {comment:}'
    # NOTE: < is left align, > is right align, ^ is centered
    #fmt_str='{code:<29}!-{comment:}'
    #fmt_str='{code:<42}!-{comment:}'
    fmt_str='{code:<%d}!-{comment:}'%(_most_common(mc_idxs))
    temp_objs=[]
    for obj in objs:
        temp_obj=[]
        for ln in obj.split('\n'):
            dat=ln.split('!-')
            try:
                temp_obj.append(fmt_str.format(code=dat[0], comment=dat[1]))
            except IndexError:
                temp_obj.append(ln)
        temp_objs.append( '\n'.join(temp_obj) )
    return temp_objs


# NOTE/TODO: ZoneList interaction: Determine which zones to add via zonelist names
def copy_IDF_geo(from_objs, to_objs):
    """Copy E+ geometry objects (`Zone`, `BuildingSurface:Detailed`, `FenestrationSurface:Detailed`) from `from_objs` to the `to_objs` which are two genEPJ Lists.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with copied geometry (Python `List`)
    """

    printc("\nCopying templated Zones/Surfaces.", 'green')

    objs_all_fr=from_objs
    objs_all_to=to_objs

    objs_filt_zon=filter_IDF_objs_raw(objs_all_fr, 'Zone')
    # SB: Find these from the proposed file?
    #objs_filt_mat=filter_IDF_objs_raw(objs_all_fr, 'Material')
    #objs_filt_winfrm=filter_IDF_objs_raw(objs_all_fr, 'WindowProperty:FrameAndDivider')
    objs_filt_sur=filter_IDF_objs_raw(objs_all_fr, 'BuildingSurface:Detailed')
    objs_filt_win=filter_IDF_objs_raw(objs_all_fr, 'FenestrationSurface:Detailed')
    #print(objs_filt)

    # Location in objs_all where objs_filt occurs. Used to splice later
    obj_idxs = [i for i,obj in enumerate(objs_all_to) if get_obj_type(obj)=='Zone']
    print("NUM New OBJS, b4 removal: ",len(objs_all_to))
    print("Obj idxs: ",obj_idxs)
    if obj_idxs:
        obj_idx = obj_idxs[0] # Take first occurance of object
    else:
        obj_idx=-1 # No objects found. Append to end of file

    ## Swap names of constructions into copied surfaces. Copy constructions if missing?

    # Get templated construction names (
    objs_cons_temp=filter_IDF_objs_raw(objs_all_to, 'Construction')
    objs_sur_temp=filter_IDF_objs_raw(objs_all_to, 'BuildingSurface:Detailed')
    objs_fen_temp=filter_IDF_objs_raw(objs_all_to, 'FenestrationSurface:Detailed')
    # Add Fenestration objects into Surfaces (will get replaced by block below)
    objs_sur_temp.extend(objs_fen_temp)
    ##objs_cons_fr=filter_IDF_objs_raw(objs_all_fr, 'Construction')

    cons_types=['Roof', 'Wall', 'Ceiling', 'Floor', 'Window']
    # Replace names in [Roof,Floor, Ceiling, Wall] constructions to names from filtered list
    for myty in cons_types: # Now dealing with rf/fl/ce/wl
        surf_obj= _filter_surf_obj_by_type(myty, objs_sur_temp)
        cons_name= get_cons_name_from_type( objs_cons_temp, surf_obj, myty)
        #print("CONS NAME: %s, type: %s"%(cons_name,myty))
        if cons_name: # If a name was found for the construction (not None)
            objs_iterate = list(objs_filt_sur)
            objs_iterate.extend(objs_filt_win)
            for j in range(len(objs_iterate)): # SB: Need to iterate to get right index
                if get_surf_type(objs_iterate[j])==myty:
                    objs_iterate[j]= set_surf_name(objs_iterate[j], cons_name)
            objs_filt_sur= list(objs_iterate)


    # Mark for deletition (refactored in 2022)
    ## Remove objects from objs list in to_file
    #new_objs= rm_obj_by_type("Zone", objs_all_to)
    #new_objs= rm_obj_by_type("BuildingSurface:Detailed", new_objs)
    #new_objs= rm_obj_by_type("FenestrationSurface:Detailed", new_objs)
    ###new_objs= rm_obj_by_type("*HVAC*", new_objs) # Remove all HVAC objects

    # Remove objects from objs list in to_file
    new_objs= rm_obj_by_type(objs_all_to, args={'type': "Zone"} )
    new_objs= rm_obj_by_type(new_objs, args={'type': "BuildingSurface:Detailed" })
    new_objs= rm_obj_by_type(new_objs, args={'type': "FenestrationSurface:Detailed"} )
    ##new_objs= rm_obj_by_type(new_objs, args={'type': "*HVAC*" }) # Remove all HVAC objects

    objs_filt_lst = ["\n".join(objs) for objs in [objs_filt_zon,objs_filt_sur,objs_filt_win]]
    objs_filt_str = "\n".join(objs_filt_lst)
    new_objs.insert(obj_idx, objs_filt_str )

    return new_objs

def copy_IDF_constr(from_objs, to_objs):
    """Copy `Material` and `Construction` objects from provide genEPJ List to specified genEPJ List.

    A naming convention is expected for `Construction` objects in template file:

    * *ExtWall* for Exterior Walls
    * *ExtFloor* for Exterior Floors
    * *ExtRoof* for Exterior Ceilings/Roofs
    * *ExtSlab* for Exterior Slabs on Grade
    * *IntWall* for Interior Walls
    * *IntFloor* for Interior Floors
    * *IntCeil* for Interior Ceilings

    Parameters:

    * `from_objs`: genEPJ object list to copy `Construction` and `Material` objects from (Python `List`)
    * `to_objs`: genEPJ object list to copy `Construction` and `Material` objects to (Python `List`)

    Returns:

    * `objs_all`: genEPJ object list with merged `Construction` and `Material` objects (Python `List`)
    """

    # SB TODO: Write function to check for Word segments in a list of names, use in objs_*_cons
    printc("\nCopying templated Constructions/Materials.", 'green')

    objs_all_fr=from_objs
    objs_all_to=to_objs
    accept_nm_extwall = ['extwall', 'exterior wall', 'ag wall', 'ext wall']
    accept_nm_baswall = ['baswall', 'basement wall', 'bg wall']
    accept_nm_intwall = ['intwall', 'interior wall', 'int-wall']
    accept_nm_win     = ['window', 'extwin', 'dgc', 'dgl', 'tgl', 'tgc' ]
    #accept_nm_ceil    = ['intceil', 'interior ceiling', 'ceiling', 'attic']
    # Added for make RefBldgSmallOfficeNew2004 work for radiant slabs
    accept_nm_ceil    = ['intceil', 'interior ceiling', 'ceiling', 'attic', 'int-ceil']
    accept_nm_extroof = ['extroof', 'exterior roof', 'roof']
    #NOTE- Removed 'atticfloor' since interior surfaces must be opposite
    #accept_nm_floor   = ['intfloor', 'interior floor', 'atticfloor']
    #accept_nm_floor   = ['intfloor', 'interior floor']
    # Added for make RefBldgSmallOfficeNew2004 work for radiant slabs
    accept_nm_floor   = ['intfloor', 'interior floor', 'floor', 'int-floor']
    accept_nm_basflr  = ['basement floor', 'extslab', 'extfloor', 'exterior floor', 'exterior slab']

    # Get templated construction names (
    objs_filt_mat=filter_IDF_objs_raw(objs_all_fr, 'Material')
    objs_filt_matnomass=filter_IDF_objs_raw(objs_all_fr, 'Material:NoMass')
    objs_filt_matairgp=filter_IDF_objs_raw(objs_all_fr, 'Material:AirGap')
    objs_filt_winglz=filter_IDF_objs_raw(objs_all_fr, 'WindowMaterial:Glazing')
    objs_filt_winglzsys=filter_IDF_objs_raw(objs_all_fr, 'WindowMaterial:SimpleGlazingSystem')
    objs_filt_wingas=filter_IDF_objs_raw(objs_all_fr, 'WindowMaterial:Gas')
    objs_filt_mat.extend(objs_filt_matnomass)
    objs_filt_mat.extend(objs_filt_matairgp)
    objs_filt_mat.extend(objs_filt_winglz)
    objs_filt_mat.extend(objs_filt_winglzsys)
    objs_filt_mat.extend(objs_filt_wingas)
    objs_all_cons=filter_IDF_objs_raw(objs_all_fr, 'Construction')
    objs_all_consrad=filter_IDF_objs_raw(objs_all_fr, 'Construction:InternalSource')
    objs_all_cons.extend(objs_all_consrad) # Add radiant floor/ceiling objects
    #objs_filt_winfrm=filter_IDF_objs_raw(objs_all_fr, 'WindowProperty:FrameAndDivider')
    #objs_filt_sur=filter_IDF_objs_raw(objs_all_fr, 'BuildingSurface:Detailed')
    #objs_filt_win=filter_IDF_objs_raw(objs_all_fr, 'FenestrationSurface:Detailed')
    #print(objs_filt)
    objs_extroof_cons= [obj for obj in objs_all_cons if is_in(accept_nm_extroof, get_obj_name(obj).lower())]
    objs_extwall_cons= [obj for obj in objs_all_cons if is_in(accept_nm_extwall, get_obj_name(obj).lower())]
    objs_baswall_cons= [obj for obj in objs_all_cons if is_in(accept_nm_baswall, get_obj_name(obj).lower())]
    objs_intwall_cons= [obj for obj in objs_all_cons if is_in(accept_nm_intwall, get_obj_name(obj).lower())]
    objs_ceiling_cons= [obj for obj in objs_all_cons if is_in(accept_nm_ceil, get_obj_name(obj).lower())]
    objs_floor_cons  = [obj for obj in objs_all_cons if is_in(accept_nm_floor, get_obj_name(obj).lower())]
    objs_basflr_cons = [obj for obj in objs_all_cons if is_in(accept_nm_basflr, get_obj_name(obj).lower())]
    objs_window_cons = [obj for obj in objs_all_cons if is_in(accept_nm_win, get_obj_name(obj).lower())]

    #print("TEST:",objs_basflr_cons )
    objs_know = []
    container=[objs_extroof_cons,objs_extwall_cons,objs_baswall_cons,objs_intwall_cons,objs_ceiling_cons,objs_floor_cons,objs_basflr_cons,objs_window_cons]
    [objs_know.extend(objs) for objs in container]

    # Check that multiple objects arent defined for Window, Walls, IntWalls, Ceilings, etc
    for objs in container:
        if len(objs)>1 :
            printc('Warning: Multiple objs found in construction: %s'%(mkcolor(str(list(map(get_obj_name,objs))),'blue')), 'yellow')

    # Check for objects that arent being classified
    objs_other_cons= [obj for obj in objs_all_cons if obj not in objs_know]
    if len(objs_other_cons)>0 :
        printc('Warning: Multiple unclassified objs found in construction: %s'%(mkcolor(str(list(map(get_obj_name, objs_other_cons))),'blue')), 'yellow')

    objs_extroof_nm= try2get(get_obj_name, objs_extroof_cons)
    objs_extwall_nm= try2get(get_obj_name, objs_extwall_cons)
    objs_baswall_nm= try2get(get_obj_name, objs_baswall_cons)
    objs_intwall_nm= try2get(get_obj_name, objs_intwall_cons)
    objs_ceiling_nm= try2get(get_obj_name, objs_ceiling_cons)
    objs_floor_nm  = try2get(get_obj_name, objs_floor_cons)
    objs_basflr_nm = try2get(get_obj_name, objs_basflr_cons)
    objs_window_nm = try2get(get_obj_name, objs_window_cons)

    # SB NOTE: Order is very important here
    cons_names=[objs_extroof_nm,objs_extwall_nm,objs_baswall_nm,objs_intwall_nm,objs_ceiling_nm,objs_floor_nm,objs_basflr_nm,objs_window_nm]

    # Location in objs_all where objs_filt occurs. Used to splice later
    obj_idxs = [i for i,obj in enumerate(objs_all_to) if get_obj_type(obj)=='Material']
    #print("NUM New OBJS, b4 removal: ",len(objs_all_to))
    #print("Obj idxs: ",obj_idxs)
    if obj_idxs:
        obj_idx = obj_idxs[0] # Take first occurance of object
    else:
        obj_idx=-1 # No objects found. Append to end of file

    ### Swap names of constructions into copied surfaces. Copy constructions if missing?

    ## Get BuildingSurface names (where we are putting new Contruction names)
    objs_surf_to=filter_IDF_objs_raw(objs_all_to, 'BuildingSurface:Detailed')
    objs_cons_to=filter_IDF_objs_raw(objs_all_to, 'Construction')
    objs_fen_to= filter_IDF_objs_raw(objs_all_to, 'FenestrationSurface:Detailed')
    ## Add Fenestration objects into Surfaces (will get replaced by block below)
    objs_surf_to.extend(objs_fen_to)

    # NOTE: Match order of container object
    cons_types=['Roof'    , 'Wall'    , 'Wall'   , 'Wall'    , 'Ceiling' , 'Floor'   , 'Floor'  , 'Window']
    cons_bound=['Outdoors', 'Outdoors', 'Ground' , 'Surface' , 'Surface' , 'Surface' , 'Ground' , '']
    # Replace names in [Roof,Floor, Ceiling, Wall] constructions to names from filtered list
    for i,myty in enumerate(cons_types): # Now dealing with rf/extwall/intwall/ce/flr/win
        printc("\nIdentifying names for construction type: %s, BC: %s"%(mkcolor(myty,'yellow'), mkcolor(str(cons_bound[i]),'yellow')), 'green')

        #if cons_bound[i]:
        surf_obj= _filter_surf_obj_by_type(myty, objs_surf_to)
        #print('TEST found surf_obj: %s'%( "\n".join(surf_obj)) )
        surf_obj=[s for s in surf_obj if _get_surf_BC(s)==cons_bound[i]]
        surf_obj_nm=[get_obj_name(s) for s in surf_obj if _get_surf_BC(s)==cons_bound[i]]
        #print('Filtered Surface names: %s'%(str(surf_obj_nm)))
        #else:
        #    surf_obj= _filter_surf_obj_by_type(myty, objs_surf_to)
        #    #print("Surf BC: ",str([_get_surf_BC(s) for s in surf_obj]))
        #    # Does object have Interior Boundar Conditions?
        #    surf_obj=[s for s in surf_obj if _get_surf_BC(s)=='Surface']
        print('TEST: %s with name %s with BD %s'%(myty, cons_names[i], cons_bound[i]))
        new_cons_name=cons_names[i]
        #print('TEST found surf_obj: %s'%( "\n".join(surf_obj)) )
        if new_cons_name:
            print("CONS NAME: %s, type: %s"%(new_cons_name,myty))
            objs_all_iter=list(objs_all_to)
            for j,obj in enumerate(objs_all_iter):
                #if obj in surf_obj:
                # HACK: get_obj_abstract(obj, 3) is Construction Type (BuildingSurface:Detailed)
                #print( "BOOL TEST:", (obj in surf_obj) and ("Air Wall" not in get_obj_abstract(obj, 3)) )
                if ( (obj in surf_obj) and ("Air Wall" not in get_obj_abstract(obj, 3)) ):
                    objs_all_to[j]=set_surf_name(obj, new_cons_name)


    # Mark for deletition (refactored in 2022)
    ## Remove objects from objs list in to_file
    #new_objs= rm_obj_by_type("Construction", objs_all_to)
    #new_objs= rm_obj_by_type("Material", new_objs)

    # Remove objects from objs list in to_file
    new_objs= rm_obj_by_type(objs_all_to, args={'type': "Construction"} )
    new_objs= rm_obj_by_type(new_objs, args={'type': "Material"} )

    # Add new Materials/Construction objects to new_objs
    if len(objs_filt_mat)<1 :
        ValueError("Unable to find Material objects in provided object list len: ", len(from_objs))
    if len(objs_all_cons)<1 :
        ValueError("Unable to find Construction objects in provided object list len: ", len(from_objs))
    objs_mat_cons=list(objs_filt_mat)
    objs_mat_cons.extend(objs_all_cons)
    objs_mat_cons_str = "\n"+"\n\n".join(objs_mat_cons)
    new_objs.insert(obj_idx, objs_mat_cons_str)

    ## Write IDF objs to file and reload
    #new_file=write_file( new_objs, '/tmp/temp_file.idf')
    #objs_all=get_IDF_objs_raw(new_file)
    objs_all=get_IDF_objs_raw(new_objs)

    return objs_all

def add_construction_materials_file(to_file=to_file):
    """Modified version of `add_construction_materials` which creates an IDF output for testing purposes. File output uses suffix `_constemp.idf` by default."""
    return __abstract_add_objs2file(add_construction_materials, to_file=to_file, suffix='constemp')

def add_construction_materials(objs_all, args={'const_file': "templates/ref_constructions_materials.idf"}):
    """Add user specified E+ `Construction` and `Material` to IDF provided in template: `sim/templates/*idf` file.

    A naming convention is expected for `Construction` objects in template file (see all naming conventions in `accept_nm_*` in function `copy_IDF_constr`):

    * *ExtWall* for Exterior Walls
    * *ExtFloor* for Exterior Floors
    * *ExtRoof* for Exterior Ceilings/Roofs
    * *ExtSlab* for Exterior Slabs on Grade
    * *IntWall* for Interior Walls
    * *IntFloor* for Interior Floors
    * *IntCeil* for Interior Ceilings

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `const_file` 

    Returns:

    * `new_objs`: genEPJ object list new `Construction/Material` template added (Python `List`)
    """

    const_file=args['const_file']
    new_objs=list(objs_all)

    #const_file='templates/ref_constructions_materials.idf'
    objs_all_fr=get_IDF_objs_raw(const_file)
    if len(objs_all_fr)<1 :
        ValueError("Unable to find objects in file ",fr_file)
    new_objs = copy_IDF_constr(objs_all_fr, new_objs)

    return new_objs

def copy_IDF_files(from_file=fr_file, to_file=to_file, myfn=copy_IDF_geo):
    """Modified version of `copy_IDF_geo`/`copy_IDF_constr` which creates an IDF output for testing purposes. File output uses suffix `_consobjs.idf` by default."""

    print("\nCopying information from file %s to templated file %s\n"%(mkcolor(from_file,'blue'), mkcolor(to_file,'blue')))

    # Get objs to copy into FROM_FILE (originating in from_file)
    objs_all_fr=get_IDF_objs_raw(from_file)
    if objs_all_fr<1 :
        ValueError("Unable to find objects in file ",fr_file)

    # Get objs to copy into TO_FILE (originating in to_file)
    objs_all_to=get_IDF_objs_raw(to_file)
    if objs_all_to<1 :
        ValueError("Unable to find objects in file ",to_file)

    new_objs=myfn(objs_all_fr, objs_all_to)

    #Finally, splice in copied objects and write to file
    #print("NUM New OBJS, after removal: ",len(new_objs))
    newfile=to_file.replace(".","_consobjs.")
    printc("Saving new IDF file to: %s"%(newfile), 'green')

    f=open(newfile, 'w')
    # dos2unix: get rid of pesky '\r' objects
    f.write( dos2unix("\n\n".join(new_objs)) )
    return newfile

# SB NOTE: this function needs to be run several times
# Run until number of objects doesnt change
def rm_all_unused_objs_file(to_file=to_file):
    """Modified version of `rm_all_unused_objs` which creates an IDF output for testing purposes. File output uses suffix `_purge.idf` by default."""
    return __abstract_add_objs2file(rm_all_unused_objs, to_file=to_file, suffix='purge')

def rm_all_unused_objs(objs_all, args={} ):
    """Removes unused IDF objects from provided genEPJ object list

    Parameters:

    * `objs_all`: genEPJ object list
    * `args`: `None`

    Returns:

    * `myobjs`: genEPJ object list with unused objects purged
    """

    not_converged=True
    myobjs=list(objs_all)
    printc("Purging unused objects from file",'green')
    len_orig=len(myobjs)
    while not_converged:
        len_objs=len(myobjs)
        myobjs=rm_unused_objs(myobjs)
        #print("len(myobjs)==len_objs: %d==%d"%(len(myobjs),len_objs))
        if len(myobjs)==len_objs:
            not_converged=False
            printc('Purged %d objects!'%(len_orig-len(myobjs)),'green')
        else:
            not_converged=True
            print('Still more unused objects, trying one more iteration')

    ##myobjs = align_IDF_objs(myobjs)
    #newfile=to_file.replace(".","_purge.")
    #print("Saving new file to: %s"%(newfile))
    ##objs_filt_str = "".join(myobjs)
    #objs_filt_str = "\n".join(myobjs)
    #f=open(newfile, 'w')
    #f.write( dos2unix(objs_filt_str) )
    #return newfile
    return myobjs

def rm_skylights_file(to_file=to_file):
    """Modified version of `rm_skylights` which creates an IDF output for testing purposes. File output uses suffix `_rmskyli.idf` by default."""
    return __abstract_add_objs2file(rm_skylights, to_file=to_file, suffix='rmskyli')


def rm_skylights(objs_all, args={}):
    """Remove skylights (roof mounted E+ `FenestrationSurface:Detailed` objects) from genEPJ object list.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with skylights removed (Python `List`)
    """
    #select a.SurfaceName, b.SurfaceName, b.SurfaceIndex, a.BaseSurfaceIndex from Surfaces as a, Surfaces as b WHERE a.ClassName="Window" AND b.SurfaceIndex=a.BaseSurfaceIndex and b.ClassName="Roof";
    #to_file=args['to_file']
    #c = get_sql_database(to_file)
    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()
    sql_sel='SELECT a.SurfaceName FROM Surfaces as a, Surfaces as b WHERE a.ClassName="Window" AND b.SurfaceIndex=a.BaseSurfaceIndex AND b.ClassName="Roof";'
    skylight_names = c.execute(sql_sel).fetchall()
    skylight_names = list( map(lambda x: x[0].lower(), skylight_names ))
    print(skylight_names)
    # Check flag to keep a fraction of skylights. TODO- remove randomness
    if 'frac_remove' in args :
        _frac= float( args['frac_remove'] )
         # round to nearest whole integer
        _num_sample= int(round( len(skylight_names)*(1 - _frac) ))
        skylight_names = sample(skylight_names, _num_sample)

    # if IDF
    if isinstance(objs_all, list):
        new_objs = list(objs_all)
        objs_surf_win=filter_IDF_objs_raw(objs_all, 'FenestrationSurface:Detailed')
        new_objs= [obj for obj in new_objs if not ( 'FenestrationSurface:Detailed' == get_obj_type(obj) and get_obj_name(obj).lower() in skylight_names)]
    # if JSON
    elif isinstance(objs_all, dict):
        #objs_surf_win=objs_all['FenestrationSurface:Detailed']
        # TODO-!
        pass
    return new_objs

def diagnostic_output_areas_file(to_file=to_file):
    """Modified version of `diagnostic_output_areas` which creates an IDF output for testing purposes. File output uses suffix `_diagAreas.idf` by default."""
    return __abstract_add_objs2file(diagnostic_output_areas, to_file=to_file, suffix='diagAreas')

# TODO- Add look up indices for each construction type. Each surface refers to this (in terms of area).
# TODO- Any need to output areas by zone!?
# TODO- Want PV areas for cost analyses
def diagnostic_output_areas(objs_all, args={}):
    """Diagnostic script which outputs areas of E+ objects: `BuildingSurface:Detailed`,`FenestrationSurface:Detailed` for above and below grade.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `area_hash`: Dictionary of above/below grade areas for wall/roofs and windows (Python `dict`)
    """
    # Output areas into a CSV file.

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    # Load up in cash_flow.py for the cost analysis
    objs_filt_sur=filter_IDF_objs_raw(objs_all, 'BuildingSurface:Detailed')
    objs_surf_win=filter_IDF_objs_raw(objs_all, 'FenestrationSurface:Detailed')
    objs_surf_ext=[surf for surf in objs_filt_sur if _get_surf_BC(surf)=='Outdoors']
    awin,awall,aflr,abas,aslb,aroof=[],[],[],[],[],[]
    # Surface Types/Combinations:
    #  1. Walls
    #  2. Flat Roofs
    #  3. Sloped Roofs
    #  4. Floors with exterior BC (exposed floors)
    #  5. Walls with Ground BC
    #  6. Floors with Ground BC (ie. Slabs)
    print("Calculating areas for %d Surfaces and %d Windows"%(len(objs_filt_sur), len(objs_surf_win)))

    for surf in objs_surf_ext:
        # Need to look for each FenestrationSurface:Detailed associated with the wall object.
        #print("Calculating areas for ABOVE GRADE surface: %s"%(get_obj_name(surf)))
        # Calc of wall area: requires subtraction of window areas in that wall
        #print(surf)
        if get_obj_abstract(surf,2)=='Wall':
            wall_area=_calc_area(surf, 'Wall')
            #print("Wall Area: ",wall_area)
            wins_in_wall=[win for win in objs_surf_win if get_obj_name(surf) == get_obj_abstract(win,4)]
            win_areas=map(lambda x: _calc_area(x, 'Wall'), wins_in_wall)
            awall.append( wall_area-sum(win_areas) )
            awin.append( sum(win_areas) )
        elif get_obj_abstract(surf,2)=='Floor':
            flr_area=_calc_area(surf, 'Floor')
            aflr.append(flr_area)
        elif get_obj_abstract(surf,2)=='Roof':
            rf_area=_calc_area(surf, 'Floor')
            aroof.append(rf_area)

    # Need to separate Exterior Wall and Basement Walls since they have different constructions
    objs_surf_gnd=[surf for surf in objs_filt_sur if _get_surf_BC(surf)=='Ground']
    for surf in objs_surf_gnd:
        #print("Calculating areas for BELOW GRADE surface: %s"%(get_obj_name(surf)))
        if get_obj_abstract(surf,2)=='Wall':
            gwall_area=_calc_area(surf, 'Wall')
            #gwins_in_wall=[win for win in objs_surf_win if get_obj_name(surf) == get_obj_abstract(win,4)]
            #win_areas=map(lambda x: _calc_area(x, 'Wall'), wins_in_wall)
            #awin.append( sum(win_areas) )
            #abas.append( wall_area-sum(win_areas) )
            abas.append( gwall_area )
        elif get_obj_abstract(surf,2)=='Floor':
            flr_area=_calc_area(surf, 'Floor')
            aslb.append(flr_area)

    print("Wall ABOVE GRADE Areas:   %.2f"%(sum(awall)))
    print("Wall BELOW GRADE Areas:   %.2f"%(sum(abas)))
    print("Window ABOVE GRADE Areas: %.2f"%(sum(awin)))
    print("Floor ABOVE GRADE Areas:  %.2f"%(sum(aflr)))
    print("Floor BELOW GRADE Areas:  %.2f"%(sum(aslb)))
    print("Exposed Roof Areas:       %.2f"%(sum(aroof)))

    data_temp=[('Wall',   0),
               ('Floor',  0),
               ('Window', 0),
               ('Wall',  -1),
               ('Floor', -1),
               ('Roof',   0),
              ]

    #TODO- Fix SQL injection
    # Area == Net Area (subtract subsurfaces), GrossArea == Gross total area (subsurfaces NOT subtracted)
    #sql_sel='SELECT sum(Area) from Surfaces WHERE ClassName=="?" and ExtBoundCond==?;'
    sql_sel='SELECT sum(Area) from Surfaces WHERE ClassName=="%s" and ExtBoundCond==%d;'
    awall = c.execute(sql_sel % data_temp[0]).fetchone()[0]
    aflr  = c.execute(sql_sel % data_temp[1]).fetchone()[0]
    awin  = c.execute(sql_sel % data_temp[2]).fetchone()[0]
    abas  = c.execute(sql_sel % data_temp[3]).fetchone()[0]
    aslb  = c.execute(sql_sel % data_temp[4]).fetchone()[0]
    aroof = c.execute(sql_sel % data_temp[5]).fetchone()[0]
    # PV Area: Exterior BCs, Surface is azimuth is between East-South-West
    sql_sel2= 'SELECT sum(Area) from Surfaces WHERE ExtBoundCond=0 AND Azimuth>=90 AND Azimuth<=270 and ClassName="Wall";'
    pv_frac=0.9
    apv = c.execute(sql_sel2).fetchone()[0]*pv_frac
    conn.close()
    awall,aflr,awin,abas,aslb,aroof,apv=map(zeroIfNone,[awall,aflr,awin,abas,aslb,aroof,apv])

    print("SQL Wall ABOVE GRADE Areas:  ",awall)
    print("SQL Wall BELOW GRADE Areas:  ",abas)
    print("SQL Window ABOVE GRADE Areas:",awin)
    print("SQL Floor ABOVE GRADE Areas: ",aflr)
    print("SQL Floor BELOW GRADE Areas: ",aslb)
    print("SQL Exposed Roof Areas:      ",aroof)
    print("SQL PV Areas (%.1f of East-South-West area): %.1f"%(pv_frac, apv))
    area_hash={"awall": awall,
               "abas": abas,
               "awin": awin,
               "aflr": aflr,
               "aslb": aslb,
               "aroof": aroof,
               "apv": apv,
              }

    return area_hash
    #return objs_all


def __abstract_add_objs2file(myfn, to_file=to_file, suffix='newobj'):
    objs_all=get_IDF_objs_raw(to_file)
    if len(objs_all)<1 :
        ValueError("Unable to find objects in file %s"%(to_file))
    #print(objs_all)

    # Added for SQL file finding
    #new_objs=myfn(objs_all, {'file_name': to_file})
    new_objs=myfn(objs_all)
    print("After fn call")

    # NO repeat objects
    #new_objs=list(set(new_objs))
    #print(new_objs)

    #Finally, splice in copied objects and write to file
    newfile=to_file.replace(".","_%s."%(suffix))
    fname=write_file(new_objs, newfile)

    return fname

## SB Goal: Push values in schedules forward/backward by N hours
## WHY: Accumulation of exact load profiles in a community can cause peak load issues
def push_schedule_values_file(to_file=to_file):
    """Modified version of `push_schedule_values` which creates an IDF output for testing purposes. File output uses suffix `_PUSHSch.idf` by default."""
    return __abstract_add_objs2file(push_schedule_values, to_file=to_file, suffix='PUSHSch')

def _modify_ScheduleDay(myobj, N):

    sche_temp="""
    0%d:00,                   !- Time 1
    %.2f,                    !- Value Until Time 1
"""

    # Start my grabbing the hourly increments

    # [4 :] - All values after 4th line
    # [::2] - Every other value
    temp_vls= array( trim_comments( myobj.strip(',') ).split('\n') )
    temp_hrs = temp_vls[4 :][ ::2]
    temp_frac = temp_vls[5 :][ ::2]
    #print temp_vls
    #
    ### Intenional: Ignore Minute values
    #old_vls = [ ( t.split(':')[0],t.split(':')[1] ) for t in temp_hrs ]
    old_hrs = [ float( t.split(':')[0] ) for t in temp_hrs ]
    print(old_hrs)

    # Increment time values by N
    new_hrs = map( lambda x: '{:.0f}'.format(x)+':00',  array( old_hrs ) + N )
    print(new_hrs)
    for i,nv in enumerate( new_hrs ):
        if float( nv.split(':')[0] ) < 24.:
            myobj = myobj.replace( temp_hrs[i], nv )


    # Edge Case: Wrap around of time values
    # SB: Issue is here
    temp_dat1 =  array( myobj.split('\n') )[: 4] # Join later below
    temp_dat3 =  array( myobj.split('\n') )[4 :] # Join later below
    # TODO: What if I have more than one value?
    if float( new_hrs[-1].split(':')[0] ) > 24.:
        new_hr = float( new_hrs[-1].split(':')[0] ) - 24.
        new_vl = float( temp_frac[-1].strip(';') )
        temp_dat2 = sche_temp%(new_hr, new_vl)
        printc('modify_ScheduleDay: Wrapping hourly data', 'yellow')
    else:
        temp_dat2 = ''
    temp_dat1 = list( temp_dat1 )
    temp_dat1.extend( temp_dat2 )
    temp_dat1.extend( temp_dat3 )
    print(temp_dat1)
    myobj = ''.join( temp_dat1 )
    #myobj = list(temp_dat1)

    return myobj

def push_schedule_values(objs_all, args={'N':2}):
    """Push `Schedule:Day:Interval` ahead by `N` hours. Used to study schedule diversity in peak load management.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `N` Hours to push schedule ahead by

    Returns:

    * `new_objs`: genEPJ object list with modified `Schedule:Day:Interval` (Python `List`)
    """
    new_objs = list(objs_all)

    N=args['N']

    # TODO: check if Schedule is Lighting, Plug, Occupancy, etc
    mysch_type = 'Schedule:Day:Interval,'
    #objs_sche=filter_IDF_objs_raw(objs_all,'Schedule:Day:Interval')
    objs_sche = [obj for i,obj in enumerate(objs_all) if ( (get_obj_type(obj)=='Schedule:Day:Interval') and ('Kitchen' in obj) ) ]
    objs_idxs = [i for i,obj in enumerate(objs_all) if ( (get_obj_type(obj)=='Schedule:Day:Interval') and ('Kitchen' in obj) ) ]
    #objs_idxs = [i for i,obj in enumerate(objs_all) if get_obj_type(obj)=='Schedule:Day:Interval' ]
    #print( objs_sche )
    #print( objs_idxs )

    for i,obj in enumerate(objs_sche):
        mod_obj=_modify_ScheduleDay(obj, N)
        new_objs[ objs_idxs[i] ] = mod_obj

    return new_objs

def rename_from_zonelist_file(to_file=to_file):
    """Modified version of `rename_from_zonelist` which creates an IDF output for testing purposes. File output uses suffix `_RENAME.idf` by default."""
    return __abstract_add_objs2file(rename_from_zonelist, to_file=to_file, suffix='RENAME')

def rename_from_zonelist(objs_all, args={} ):
    "Rename E+ `Zones` using values specified in `ZoneList`"
    new_objs = list(objs_all)
    raw_txt = combine_objects(objs_all)

    objs_zonlist=filter_IDF_objs_raw(objs_all, 'ZoneList')
    objs_zone=filter_IDF_objs_raw(objs_all, 'Zone')
    #ref_nm =    ['riseApartment Apartment' , 'Storage' , 'Restroom' , 'Stair'  , 'Retail' , 'riseApartment Corridor' , ]
    #rename_nm = ['Apartment'               , 'Storage' , 'WashRm'   , 'Stairs' , 'Retail' , 'Corridor'               , ]
    ref_nm =    [ 'Storage' , 'Restroom' , 'Stair'  , 'Retail' , 'riseApartment Corridor' , ]
    rename_nm = [ 'Storage' , 'WashRm'   , 'Stairs' , 'Retail' , 'Corridor'               , ]
    # Mid-riseApartment Corridor
    # 'mid-riseapartment apartment')
    for j,rn in enumerate(ref_nm):
        try:
            zone_nms = extract_nms_from_zonelist(objs_zonlist, rn.lower())
        except:
            zone_nms = []
        if len(zone_nms) > 0 : printc("Replacing Thermal Zone names of ZoneList Type: '%s'"%(rn), "blue")
        for zn in zone_nms:
            new_zn = zn+" "+rename_nm[j]
            printc("Replacing ZoneName: '%s' with '%s'"%(mkcolor(zn,'green'), mkcolor(new_zn,'yellow')), "blue")
            raw_txt = raw_txt.replace( zn+",", new_zn+",")
            raw_txt = raw_txt.replace( zn+";", new_zn+";")

    new_objs = get_IDF_objs_raw( raw_txt )

    return new_objs

def add_HVAC_ideal_file(to_file=to_file):
    """Modified version of `add_HVAC_ideal` which creates an IDF output for testing purposes. File output uses suffix `_Ideal.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_ideal, to_file=to_file, suffix='Ideal')

def add_HVAC_ideal(objs_all, args={} ):
    """Add HVACTemplate of IdealAir system in specified `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with Ideal HVACTemplate (Python `List`)
    """
    # Function:
    # 1. Add Heating/Cooling schedules
    # 2. Add HVACTemplate:Thermostat
    # 3. Foreach zone: Add HVACTemplate:Zone:IdealLoadsAirSystem (referring to HVACTemplate:Thermostat Name)

    #from copy import deepcopy
    #new_objs=deepcopy(objs_all)
    new_objs=list(objs_all)


    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    # SB TODO: Move into building model (ex. SiftonHQ.py)
    no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    # Allows fn to run outside of genEPJ (ie. via genEPJ/standalone/run_genEPJ_functions.sh)
    if not 'txt_thermsch_global_heat' in globals().keys():
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    # SB TODO: Move into building model (ex. SiftonHQ.py)
    no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    obj_idx=-1

    # Foreach Zone:
    new_objs.insert(obj_idx, '! generate_IDF.py: Adding Ideal HVACSystem to IDF file')
    ideal_temp,ideal_defs=templ.HVACtemplate_Ideal_zone()
    for nm in zone_nm:

        printc("Adding Ideal HVAC to Zone: %s"%(mkcolor(nm,'green')), "blue")
        zone_defs={
              "zone_name": nm,
              "thermo_name": thermo_nm,
            }
        new_objs.insert(obj_idx, idf_templater(zone_defs, ideal_temp, ideal_defs ) )


    #==================================================
    printc("Adding HVACTemplate:Thermostat", 'yellow')
    #==================================================
    objs_sche=filter_IDF_objs_raw( new_objs, 'Schedule:Compact')
    objs_sche_nms = [ get_obj_name(o) for o in objs_sche ]
    if heatsp_nm not in objs_sche_nms:
        # Heating/Cooling Setpoint Schedules
        new_objs.insert(obj_idx, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
        new_objs.insert(obj_idx, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
        # Main thermostat
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )

    #if options.debughvac:
    #    printc("Adding FCU specific Output Variables", 'yellow')

    #    temp_output, output_defs =templ.template_output()

    #new_objs = align_IDF_objs(new_objs)
    return new_objs


def add_HVAC_VAVelec_file(to_file=to_file):
    """Modified version of `add_HVAC_VAVelec` which creates an IDF output for testing purposes. File output uses suffix `_VAVelec.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_VAVelec, to_file=to_file, suffix='VAVelec')

# SB TODO: Add ventilation effectiveness
# Improvements: Define plenum objects, hook them up to HVACTemplate objects
def add_HVAC_VAVelec(objs_all, args={ 'use_DOAS': False } ):
    """Add HVACTemplate of electric Variable Air Volume (VAV) system in specified `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `use_DOAS` link Zone to centralized DOAS system.

    Returns:

    * `new_objs`: genEPJ object list with VAVelec HVACTemplate (Python `List`)
    """
    # Objects to use: (electric reheat)
    #  * Implementation based on ExampleFile: HVACTemplate-5ZonePackagedVAV.idf
    # HVACTemplate:Zone:VAV:HeatAndCool (ELEC REHEAT!!)
    #  HVACTemplate:Thermostat
    # HVACTemplate:System:PackagedVAV

    new_objs=list(objs_all)

    # Modifying Simulation Control Object (if available)
    # VAV requires systems sizing
    obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='SimulationControl']
    if obj_idxs:
        # MODIFY SimulationControl
        objs_simcontrl=filter_IDF_objs_raw(objs_all, 'SimulationControl')[0]
        new_objs[obj_idxs[0]]=set_simcontrl_sizing(objs_simcontrl, 'Yes')


    fansch_nm="FanAvailSchedVAVelec"
    OAavailsch_nm="Min OA Sched VAVelec"

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    # SB TODO: Move into building model (ex. SiftonHQ.py)
    no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    # Allows fn to run outside of genEPJ (ie. via genEPJ/standalone/run_genEPJ_functions.sh)
    if not 'txt_thermsch_global_heat' in globals().keys():
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()

    obj_idx=-1

    # Foreach Zone:
    new_objs.insert(obj_idx, '! generate_IDF.py: Adding VAVelec System to IDF file')
    for nm in zone_nm:

        printc("Adding VAVelec Unit to Zone: %s"%(mkcolor(nm,'green')), "blue")
        zone_defs={
              "zone_name": nm,
              "thermo_name": thermo_nm,
              "fan_sch": fansch_nm,
            }
        vav_temp,vav_defs=templ.HVACtemplate_VAV_zone()
        new_objs.insert(obj_idx, idf_templater(zone_defs, vav_temp, vav_defs ) )
        #if use_DOAS: # Insert DOAS name
        #    zone_defs["doas_name"]="DOAS"
        #    new_objs.insert(obj_idx, idf_templater(zone_defs, fcu_temp, fcu_defs ) )
        #else:
        #    new_objs.insert(obj_idx, idf_templater(zone_defs, fcu_temp, fcu_defs ) )

    #==================================================
    printc("Adding HVACTemplate:Thermostat", 'yellow')
    #==================================================
    objs_sche=filter_IDF_objs_raw( new_objs, 'Schedule:Compact')
    objs_sche_nms = [ get_obj_name(o) for o in objs_sche ]
    if heatsp_nm not in objs_sche_nms:
        # Heating/Cooling Setpoint Schedules
        new_objs.insert(obj_idx, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
        new_objs.insert(obj_idx, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
        # Main thermostat
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )
    # Fan availability schedules
    avail_sche, avail_defs = templ.HVACtemplate_schedule_avail()
    new_objs.insert(obj_idx, idf_templater({"avail_nm": fansch_nm}, avail_sche, avail_defs) )
    # OA availability schedulidf_e
    # SB: TODO: OA OFF from 12am to 8am. Wont work on residential!!
    OA_temp,OA_defs=templ.HVACtemplate_OAschedule_avail()
    new_objs.insert(obj_idx, idf_templater({'oa_sche': OAavailsch_nm}, OA_temp, OA_defs ) )

    #=============================================
    printc("Adding HVACTemplate:System:PackagedVAV", 'yellow')
    #=============================================
    d={
      'vav_name': "DXVAV Sys 1",
      'fan_sch': fansch_nm,
      'avail_nm': OAavailsch_nm,
      'hcoil_type': "Electric",
      'ccoil_type': "TwoSpeedDX",
    }
    VAV_temp,VAV_defs=templ.HVACtemplate_VAV_system()
    new_objs.insert(obj_idx, idf_templater(d, VAV_temp, VAV_defs ) )

    if options.debughvac:
        printc("Adding VAVelec specific Output Variables", 'yellow')

        temp_output, output_defs =templ.template_output()

        output_vars=[
          'PlantSupplySideOutletTemperature',
          'Zone Air Terminal VAV Damper Position',
        ]

        for v in output_vars:
            new_objs.insert(obj_idx, idf_templater( {'name': v}, temp_output, {} ) )

    #new_objs = align_IDF_objs(new_objs)
    return new_objs


def add_HVAC_VAVgas_file(to_file=to_file):
    """Modified version of `add_HVAC_VAVgas` which creates an IDF output for testing purposes. File output uses suffix `_VAVgas.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_VAVgas, to_file=to_file, suffix='VAVgas')

# SB TODO: Add ventilation effectiveness
# Improvements: Define plenum objects, hook them up to HVACTemplate objects
def add_HVAC_VAVgas(objs_all, args={'use_DOAS': False } ):
    """Add HVACTemplate of gas Variable Air Volume (VAV) system in specified `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `use_DOAS` link Zone to centralized DOAS system.

    Returns:

    * `new_objs`: genEPJ object list with VAVgas HVACTemplate (Python `List`)
    """
    # Objects to use: (electric reheat)
    #  * Implementation based on ExampleFile: HVACTemplate-5ZonePackagedVAV.idf
    # HVACTemplate:Zone:VAV:HeatAndCool (ELEC REHEAT!!)
    #  HVACTemplate:Thermostat
    # HVACTemplate:System:PackagedVAV
    new_objs=list(objs_all)

    # Modifying Simulation Control Object (if available)
    # VAV requires systems sizing
    obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='SimulationControl']
    if obj_idxs:
        # MODIFY SimulationControl
        objs_simcontrl=filter_IDF_objs_raw(objs_all, 'SimulationControl')[0]
        new_objs[obj_idxs[0]]=set_simcontrl_sizing(objs_simcontrl, 'Yes')


    fansch_nm="FanAvailSchedVAVelec"
    OAavailsch_nm="Min OA Sched VAVelec"

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    # SB TODO: Move into building model (ex. SiftonHQ.py)
    no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    # Allows fn to run outside of genEPJ (ie. via genEPJ/standalone/run_genEPJ_functions.sh)
    if not 'txt_thermsch_global_heat' in globals().keys():
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()

    obj_idx=-1

    # Foreach Zone:
    new_objs.insert(obj_idx, '! generate_IDF.py: Adding VAVgas System to IDF file')
    vav_temp,vav_defs=templ.HVACtemplate_VAV_zone()
    for nm in zone_nm:

        printc("Adding VAVelec Unit to Zone: %s"%(mkcolor(nm,'green')), "blue")
        zone_defs={
              "zone_name": nm,
              "thermo_name": thermo_nm,
              "fan_sch": fansch_nm,
              "hcoil_type": "HotWater",
            }
        new_objs.insert(obj_idx, idf_templater(zone_defs, vav_temp, vav_defs ) )
        #if use_DOAS: # Insert DOAS name
        #    zone_defs["doas_name"]="DOAS"
        #    new_objs.insert(obj_idx, idf_templater(zone_defs, fcu_temp, fcu_defs ) )
        #else:
        #    new_objs.insert(obj_idx, idf_templater(zone_defs, fcu_temp, fcu_defs ) )

    #==================================================
    printc("Adding HVACTemplate:Thermostat", 'yellow')
    #==================================================
    objs_sche=filter_IDF_objs_raw( new_objs, 'Schedule:Compact')
    objs_sche_nms = [ get_obj_name(o) for o in objs_sche ]
    if heatsp_nm not in objs_sche_nms:
        # Heating/Cooling Setpoint Schedules
        new_objs.insert(obj_idx, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
        new_objs.insert(obj_idx, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
        # Main thermostat
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )
    # Fan availability schedules
    avail_sche, avail_defs = templ.HVACtemplate_schedule_avail()
    new_objs.insert(obj_idx, idf_templater({"avail_nm": fansch_nm}, avail_sche, avail_defs) )
    # OA availability schedule
    # SB: TODO: OA OFF from 12am to 8am. Wont work on residential!!
    OA_temp,OA_defs=templ.HVACtemplate_OAschedule_avail()
    new_objs.insert(obj_idx, idf_templater({'oa_sche': OAavailsch_nm}, OA_temp, OA_defs ) )

    #=============================================
    printc("Adding HVACTemplate:System:PackagedVAV", 'yellow')
    #=============================================
    d={
      'vav_name': "DXVAV Sys 1",
      'fan_sch': fansch_nm,
      'avail_nm': OAavailsch_nm,
      'hcoil_type': "Gas",
      'ccoil_type': "TwoSpeedDX",
    }
    VAV_temp,VAV_defs=templ.HVACtemplate_VAV_system()
    new_objs.insert(obj_idx, idf_templater(d, VAV_temp, VAV_defs ) )
    # HWL
    HWL_temp,HWL_defs=templ.HVACtemplate_HWL()
    new_objs.insert(obj_idx, idf_templater({}, HWL_temp, HWL_defs ) )
    # Boiler
    boil_temp,boil_defs=templ.HVACtemplate_boiler()
    new_objs.insert(obj_idx, idf_templater({}, boil_temp, boil_defs ) )

    if options.debughvac:
        printc("Adding VAVelec specific Output Variables", 'yellow')

        temp_output, output_defs =templ.idf_template_output()

        output_vars=[
          'PlantSupplySideOutletTemperature',
          'Zone Air Terminal VAV Damper Position',
        ]

        for v in output_vars:
            new_objs.insert(obj_idx, idf_templater( {'name': v}, temp_output, {} ) )

    #new_objs = align_IDF_objs(new_objs)
    return new_objs


def add_HVAC_PTAC_file(to_file=to_file):
    """Modified version of `add_HVAC_PTAC` which creates an IDF output for testing purposes. File output uses suffix `_PTAC.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_PTAC, to_file=to_file, suffix='PTAC')

# SB TODO: Add ventilation effectiveness
# Improvements: Define plenum objects, hook them up to HVACTemplate objects
def add_HVAC_PTAC(objs_all, args={ 'use_DOAS': False } ):
    """Add HVACTemplate of Package Terminal Air Conditioner (PTAC) system in specified `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `use_DOAS` link Zone to centralized DOAS system.

    Returns:

    * `new_objs`: genEPJ object list with PTAC HVACTemplate (Python `List`)
    """
    # Objects to use: (electric reheat)
    #  * Implementation based on ExampleFile: HVACTemplate-5ZonePackagedVAV.idf
    # HVACTemplate:Zone:VAV:HeatAndCool (ELEC REHEAT!!)
    #  HVACTemplate:Thermostat
    # HVACTemplate:System:PackagedVAV

    use_DOAS=args['use_DOAS']

    new_objs=list(objs_all)

    # Modifying Simulation Control Object (if available)
    # PTAC requires systems sizing
    obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='SimulationControl']
    if obj_idxs:
        # MODIFY SimulationControl
        objs_simcontrl=filter_IDF_objs_raw(objs_all, 'SimulationControl')[0]
        new_objs[obj_idxs[0]]=set_simcontrl_sizing(objs_simcontrl, 'Yes')

    fansch_nm="AlwaysPTAC"

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    # SB TODO: Move into building model (ex. SiftonHQ.py)
    no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    # Allows fn to run outside of genEPJ (ie. via genEPJ/standalone/run_genEPJ_functions.sh)
    if not 'txt_thermsch_global_heat' in globals().keys():
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()

    obj_idx=-1

    # Foreach Zone:
    new_objs.insert(obj_idx, '! generate_IDF.py: Adding PTAC System to IDF file')
    for nm in zone_nm:

        printc("Adding PTAC Unit to Zone: %s"%(mkcolor(nm,'green')), "blue")
        zone_defs={
              "zone_name": nm,
              "thermo_name": thermo_nm,
              "fan_sch": fansch_nm,
              "doas_name": "",
            }
        ptac_temp,ptac_defs=templ.HVACtemplate_PTAC_zone()
        if use_DOAS: # Insert DOAS name
            zone_defs["doas_name"]="DOAS"
            new_objs.insert(obj_idx, idf_templater(zone_defs, ptac_temp, ptac_defs ) )
        else:
            new_objs.insert(obj_idx, idf_templater(zone_defs, ptac_temp, ptac_defs ) )


    #==================================================
    printc("Adding HVACTemplate:Thermostat", 'yellow')
    #==================================================
    objs_sche=filter_IDF_objs_raw( new_objs, 'Schedule:Compact')
    objs_sche_nms = [ get_obj_name(o) for o in objs_sche ]
    if heatsp_nm not in objs_sche_nms:
        # Heating/Cooling Setpoint Schedules
        new_objs.insert(obj_idx, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
        new_objs.insert(obj_idx, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
        # Main thermostat
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )
    # Fan availability schedules
    fanavail_temp, fanavail_defs = templ.HVACtemplate_schedule_alwaysON2()
    new_objs.insert(obj_idx, idf_templater({'name': fansch_nm, }, fanavail_temp, fanavail_defs ) )

    #=============================================
    printc("Adding PTAC HVACTemplate:Plant", 'yellow')
    #=============================================
    # HWL
    HWL_temp,HWL_defs=templ.HVACtemplate_HWL()
    new_objs.insert(obj_idx, idf_templater({}, HWL_temp, HWL_defs ) )
    # Boiler
    boil_temp,boil_defs=templ.HVACtemplate_boiler()
    new_objs.insert(obj_idx, idf_templater({}, boil_temp, boil_defs ) )

    if options.debughvac:
        printc("Adding PTAC specific Output Variables", 'yellow')

        temp_output, output_defs =templ.template_output()


        output_vars=[
          'Heating Coil Heating Rate',
          'Plant Supply Side Outlet Temperature',
          'Boiler Heating Rate',
          'Boiler Gas Rate',
          'Zone Packaged Terminal Air Conditioner Total Heating Rate',
          'Zone Packaged Terminal Air Conditioner Total Cooling Rate',
          'Zone Packaged Terminal Air Conditioner Sensible Heating Rate',
          'Zone Packaged Terminal Air Conditioner Sensible Cooling Rate',
          'Zone Packaged Terminal Air Conditioner Latent Heating Rate',
          'Zone Packaged Terminal Air Conditioner Latent Cooling Rate',
          'Zone Packaged Terminal Air Conditioner Electric Power',
          'Zone Packaged Terminal Air Conditioner Fan Part Load Ratio',
          'Zone Packaged Terminal Air Conditioner Compressor Part Load Ratio',
          'Boiler Part Load Ratio',
          'BoilerHeatingRate',
          'BoilerGasRate',
        ]

        for v in output_vars:
            new_objs.insert(obj_idx, idf_templater( {'name': v}, temp_output, {} ) )

    #new_objs = align_IDF_objs(new_objs)
    return new_objs

def add_HVAC_VRF_file(to_file=to_file):
    """Modified version of `add_HVAC_VRF` which creates an IDF output for testing purposes. File output uses suffix `_VRFnoboil.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_VRF, to_file=to_file, suffix='VRFnoboil')

# SB TODO: Add ventilation effectiveness
#def add_HVAC_VRF(objs_all, args={ 'use_DOAS': True, 'use_district': False } ):
def add_HVAC_VRF(objs_all, args={ 'use_DOAS': True, 'use_district': True } ):
    """Add HVACTemplate of Variable Refrigeration Flow (VRF) system in specified `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `use_DOAS` link Zone to centralized DOAS system. `use_district` Water loop temperature controlled via district system

    Returns:

    * `new_objs`: genEPJ object list with VAVgas HVACTemplate (Python `List`)
    """
    # LOGIC:
    # Variable refrigerant flow heat pumps (air-to-air):
    #  - HVACTemplate:Thermostat
    #  - HVACTemplate:Zone:VRF
    #  - HVACTemplate:System:VRF
    # For variable refrigerant flow heat pumps (water-to-air)with boiler and cooling tower:
    #  - HVACTemplate:Thermostat
    #  - HVACTemplate:Zone:VRF
    #  - HVACTemplate:System:VRF
    #  - HVACTemplate:Plant:MixedWaterLoop
    #  - HVACTemplate:Plant:Boiler
    #  - HVACTemplate:Plant:Tower
    # What Expand Objects Adds:
    # 1. Ventilation requirements: Sizing:Zone, DesignSpecification:ZoneAirDistribution (vent eff),
    # 2. Mech: Equipment, System Curves (from VariableRefrigerantFlow_5Zone.idf)
    # 3. OutdoorAir: condensers and tie
    # 4. Site:GroundTemperature:BuildingSurface,
    #    - I was surprized from this...


    use_DOAS=args['use_DOAS']
    use_district=args['use_district']

    fansch_nm="FanAvailSchedVRF"


    new_objs=list(objs_all)

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    if 'no_mech_lst' in args:
        no_mech_lst=args['no_mech_lst']
    else:
        # SB TODO: Move into building model (ex. SiftonHQ.py)
        no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']
    #no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']
    #no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'corridor']
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    # Allows fn to run outside of genEPJ (ie. via genEPJ/standalone/run_genEPJ_functions.sh)
    if not 'txt_thermsch_global_heat' in globals().keys():
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()

    obj_idx=-1

    # Added for outages during resiliency studies. Override 'AlwaysOn' defaults using EMS/Erl
    hvac_sysavail_temp,hvac_sysavail_defs=templ.HVACtemplate_schedule_alwaysON2()
    hvac_availsch_nm= "HVAC Avail Sche" # Schedule type: 'Schedule:Constant'
    _d={
        'name': hvac_availsch_nm, # Schedule type: 'Schedule:Constant'
        'frac':      "1", # Default fraction of available
#        'frac':      "0", # Default fraction of available
        'limits':    "",
    }
    new_objs.insert(obj_idx, idf_templater(_d, hvac_sysavail_temp, hvac_sysavail_defs ) )

    # Foreach Zone:
    #   ADD Output Variables
    new_objs.insert(obj_idx, '\n! generate_IDF.py: Adding VRF System to IDF file\n')
    for nm in zone_nm:

        printc("Adding Terminal Unit to Zone: %s"%(mkcolor(nm,'green')), "blue")
        zone_defs={
              "zone_name": nm,
              "thermo_name": thermo_nm,
              "fan_sch": fansch_nm,
              "doas_name": "",
              "sys_avail": hvac_availsch_nm,
            }
        if 'heat_COP' in args:
            zone_defs['heat_COP']=args['heat_COP']
        if 'cool_COP' in args:
            zone_defs['cool_COP']=args['cool_COP']
        if 'heat_oversize' in args:
            zone_defs['heat_oversize']=args['heat_oversize']
        if 'cool_oversize' in args:
            zone_defs['cool_oversize']=args['cool_oversize']
        if 'sysheat_oversize' in args:
            zone_defs['sysheat_oversize']=args['sysheat_oversize']
        vrf_temp,vrf_defs=templ.HVACtemplate_VRF_zone()
        if use_DOAS: # Insert DOAS name
            zone_defs["doas_name"]="DOAS"
            new_objs.insert(obj_idx, idf_templater(zone_defs, vrf_temp, vrf_defs ) )
        else:
            new_objs.insert(obj_idx, idf_templater(zone_defs, vrf_temp, vrf_defs ) )


    #==================================================
    printc("Adding HVACTemplate:System:VRF", 'yellow')
    #==================================================
    d={}
    d['sys_avail']=hvac_availsch_nm
    vrfsys_temp,vrfsys_defs=templ.HVACtemplate_VRF_system()
    if use_district:
        d['cond_type']="WaterCooled"
        #new_objs.insert(obj_idx, idf_templater({'cond_type': "WaterCooled"}, vrfsys_temp, vrfsys_defs ) )
        new_objs.insert(obj_idx, idf_templater(d, vrfsys_temp, vrfsys_defs ) )
        # District Water Loops Temperature Schedules
        dist_temp,dist_defs=templ.HVACtemplate_thermosche_district()
        dist_vars_low={
          'name': "District-Loop-Temp-Low-Schedule",
          'temp_low':  "15.0",
          'temp_high':  "30.0",
        }
        dist_vars_hot={
          'name': "District-Loop-Temp-High-Schedule",
          'temp_low':  "20.0",
          'temp_high':  "40.0",
        }
        new_objs.insert(obj_idx, idf_templater(dist_vars_low, dist_temp, dist_defs ) )
        new_objs.insert(obj_idx, idf_templater(dist_vars_hot, dist_temp, dist_defs ) )
        # Mixed Water Loop
        MWL_temp,MWL_defs=templ.HVACtemplate_MWL()
        MWL_vars={
          'MWL_name':      "Only Water Loop" ,
          'temp_hsp_sche': "District-Loop-Temp-High-Schedule",
          'temp_hsp':      "" ,
          'temp_lsp_sche': "District-Loop-Temp-Low-Schedule" ,
          'temp_lsp':      "" ,
        }
        new_objs.insert(obj_idx, idf_templater(MWL_vars, MWL_temp, MWL_defs ) )
        # Tower
        tow_temp,tow_defs=templ.HVACtemplate_tower()
        new_objs.insert(obj_idx, idf_templater({}, tow_temp, tow_defs ) )
        # Boiler
        boil_vars={
          'boiler_name': "Main Boiler",
          'boiler_type': "DistrictHotWater",
          'boiler_eff': "0.8",
        }
        boil_temp,boil_defs=templ.HVACtemplate_boiler()
        #
        boil_vars["boiler_eff"]=1.0
        boil_vars["boiler_type"]='DistrictHotWater'
        new_objs.insert(obj_idx, idf_templater(boil_vars, boil_temp, boil_defs ) )
    else:
        d['cond_type']="AirCooled"
        new_objs.insert(obj_idx, idf_templater(d, vrfsys_temp, vrfsys_defs ) )

    #==================================================
    printc("Adding HVACTemplate:Thermostat", 'yellow')
    #==================================================
    objs_sche=filter_IDF_objs_raw( new_objs, 'Schedule:Compact')
    objs_sche_nms = [ get_obj_name(o) for o in objs_sche ]
    if heatsp_nm not in objs_sche_nms:
        # Heating/Cooling Setpoint Schedules
        new_objs.insert(obj_idx, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
        new_objs.insert(obj_idx, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
        # Main thermostat
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )
    else:
        printc("Previous Thermostat schedules 'Schedule:Compact' found. Do nothing", 'yellow')
    # VRF Fan avail sche
    fanavail_temp, fanavail_defs = templ.HVACtemplate_schedule_alwaysON()
    new_objs.insert(obj_idx, idf_templater({'name': fansch_nm}, fanavail_temp, fanavail_defs ) )
    # Main thermostat
    objs_therm=filter_IDF_objs_raw( new_objs, 'HVACTemplate:Thermostat')
    if not len(objs_therm)>0 :
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )


    if options.debughvac:
        printc("Adding VRFnoboiler specific Output Variables", 'yellow')

        temp_output, output_defs =templ.template_output()

        output_vars=[
          'Zone VRF Air Terminal Cooling Electric Power',
          'Zone VRF Air Terminal Heating Electric Power',
          'Zone VRF Air Terminal Total Cooling Rate',
          'Zone VRF Air Terminal Total Heating Rate',
          'Zone VRF Air Terminal Fan Availability Status',
          'VRF Heat Pump Total Cooling Rate',
          'VRF Heat Pump Total Heating Rate',
          'VRF Heat Pump Cooling Electric Power',
          'VRF Heat Pump Heating Electric Power',
          'VRF Heat Pump Cooling COP',
          'VRF Heat Pump Heating COP',
          'VRF Heat Pump COP',
          'VRF Heat Pump Heat Recovery Status Change Multiplier',
          'VRF Heat Pump Defrost Electric Power',
          'VRF Heat Pump Part Load Ratio',
          'VRF Heat Pump Runtime Fraction',
          'VRF Heat Pump Cycling Ratio',
          'VRF Heat Pump Operating Mode',
          'VRF Heat Pump Condenser Inlet Temperature',
          'VRF Heat Pump Condenser Outlet Temperature',
          'VRF Heat Pump Condenser Heat Transfer Rate',
          'VRF Heat Pump Terminal Unit Cooling Load Rate',
          'VRF Heat Pump Terminal Unit Heating Load Rate',
        ]

        for v in output_vars:
            new_objs.insert(obj_idx, idf_templater( {'name': v}, temp_output, output_defs ) )


    return new_objs

def add_HVAC_FCU_file(to_file=to_file):
    """Modified version of `add_HVAC_FCU` which creates an IDF output for testing purposes. File output uses suffix `_FCU.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_FCU, to_file=to_file, suffix='FCU')

# SB NOTE: FCU must be added AFTER the DOAS system (references it)
# SB TODO: Does ASHRAE 90.1 require an OA reset?
def add_HVAC_FCU(objs_all, args={ 'use_DOAS': False, 'heat_avail': None, 'cool_avail': None }):
    """Add HVACTemplate of Fan Coil Unit (FCU) system in specified `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `use_DOAS` link Zone to centralized DOAS system

    Returns:

    * `new_objs`: genEPJ object list with FCU HVACTemplate (Python `List`)
    """
    # Implementation:
    # 1. FanAvail Schedule (Schedule:Compact)
    # For in Zone:
    #  2. Add HVACTemplate:Zone:FanCoil (refer to DOAS system if present)
    # 3. Add Boiler, Chiller Objects
    # 4. Add HVACTemplate:Plant:HotWaterLoop, HVACTemplate:Plant:ChilledWaterLoop
    # 5. HVACTemplate:Plant:Tower

    use_DOAS=args['use_DOAS']
    new_objs=list(objs_all)

    #fansch_nm="FanAvailSchedFCU"
    fansch_nm="HVAC Avail Sche" # April 2023- Changed for resil analysis (want same name as other configs)

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    # SB TODO: Move into building model (ex. SiftonHQ.py)
    if 'no_mech_lst' in args:
        no_mech_lst=args['no_mech_lst']
    else:
        no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    # Allows fn to run outside of genEPJ (ie. via genEPJ/standalone/run_genEPJ_functions.sh)
    if not 'txt_thermsch_global_heat' in globals().keys():
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()

    obj_idx=-1

    # Foreach Zone:
    new_objs.insert(obj_idx, '! generate_IDF.py: Adding FCU System to IDF file')
    for nm in zone_nm:

        printc("Adding Fan-coil Unit to Zone: %s"%(mkcolor(nm,'green')), "blue")
        zone_defs={
              "zone_name": nm,
              "thermo_name": thermo_nm,
              "fan_sch": fansch_nm,
              "doas_name": "",
            }
        fcu_temp,fcu_defs=templ.HVACtemplate_FCU_zone()
        if use_DOAS: # Insert DOAS name
            zone_defs["doas_name"]="DOAS"
            new_objs.insert(obj_idx, idf_templater(zone_defs, fcu_temp, fcu_defs ) )
        else:
            new_objs.insert(obj_idx, idf_templater(zone_defs, fcu_temp, fcu_defs ) )

    #==================================================
    printc("Adding HVACTemplate:Thermostat", 'yellow')
    #==================================================
    objs_sche=filter_IDF_objs_raw( new_objs, 'Schedule:Compact')
    objs_sche_nms = [ get_obj_name(o) for o in objs_sche ]
    if heatsp_nm not in objs_sche_nms:
        # Heating/Cooling Setpoint Schedules
        new_objs.insert(obj_idx, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
        new_objs.insert(obj_idx, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
        # Main thermostat
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )
    # Fan availability schedules
    #avail_sche, avail_defs = templ.HVACtemplate_schedule_avail()
    #new_objs.insert(obj_idx, idf_templater({"avail_nm": fansch_nm}, avail_sche, avail_defs) )
    avail_sche, avail_defs = templ.HVACtemplate_schedule_alwaysON()
    new_objs.insert(obj_idx, idf_templater({"name": fansch_nm}, avail_sche, avail_defs) )
    ## Main thermostat
    #d={
    #  "thermo_nm": thermo_nm,
    #  "hsp_sche": heatsp_nm,
    #  "csp_sche": coolsp_nm,
    #}
    #thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
    #new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )


    #=============================================
    printc("Adding HVACTemplate:Plant", 'yellow')
    #=============================================
    # CWL
    CWL_temp,CWL_defs=templ.HVACtemplate_CWL()
    new_objs.insert(obj_idx, idf_templater({}, CWL_temp, CWL_defs ) )
    # Chiller
    chill_temp,chill_defs=templ.HVACtemplate_chiller()
    new_objs.insert(obj_idx, idf_templater({}, chill_temp, chill_defs ) )
    # Tower
    tow_temp,tow_defs=templ.HVACtemplate_tower()
    new_objs.insert(obj_idx, idf_templater({}, tow_temp, tow_defs ) )
    # HWL
    HWL_temp,HWL_defs=templ.HVACtemplate_HWL()
    new_objs.insert(obj_idx, idf_templater({}, HWL_temp, HWL_defs ) )
    # Boiler
    boil_temp,boil_defs=templ.HVACtemplate_boiler()
    new_objs.insert(obj_idx, idf_templater({}, boil_temp, boil_defs ) )

    if options.debughvac:
        printc("Adding FCU specific Output Variables", 'yellow')

        temp_output, output_defs =templ.template_output()

        output_vars=[
          'Boiler Part Load Ratio',
          'Chiller Part Load Ratio',
          'HeatingCoilHeatingRate',
          'CoolingCoilTotalCoolingRate',
          'CoolingCoilSensibleCoolingRate',
          'PlantSupplySideOutletTemperature',
          'ChillerEvaporatorCoolingRate',
          'ChillerCondenserHeatTransferRate',
          'ChillerElectricPower',
          'ChillerCOP',
          'BoilerHeatingRate',
          'BoilerGasRate',
          'CoolingTowerHeatTransferRate',
          'CoolingTowerFanElectricPower',
          'Fan Coil Fan Electric Power',
        ]

        for v in output_vars:
            #new_objs.insert(obj_idx, idf_templater( {'name': v}, temp_output, {} ) )
            new_objs.insert(obj_idx, idf_templater( {'name': v, 'timestep': 'hourly'}, temp_output, {} ) )

    #new_objs = align_IDF_objs(new_objs)
    return new_objs


def add_HVAC_PTHP_file(to_file=to_file):
    """Modified version of `add_HVAC_PTHP` which creates an IDF output for testing purposes. File output uses suffix `_PTHP.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_PTHP, to_file=to_file, suffix='PTHP')

# SB NOTE: PTHP must be added AFTER the DOAS system (references it)
# SB TODO: Does ASHRAE 90.1 require an OA reset
def add_HVAC_PTHP(objs_all, args={ 'use_DOAS': False, 'heat_avail': None, 'cool_avail': None }):
    """Add HVACTemplate of Package Terminal Heat Pump (PTHP) system in specified `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `use_DOAS` link Zone to centralized DOAS system. `heat_avail/cool_avail` specify an availability schedule  for this system (used for Mexico where spaces are conditioned for a few hours per day).

    Returns:

    * `new_objs`: genEPJ object list with PTHP HVACTemplate (Python `List`)
    """

    use_DOAS=args['use_DOAS']

    new_objs=list(objs_all)

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    if 'no_mech_lst' in args:
        no_mech_lst=args['no_mech_lst']
    else:
        # SB TODO: Move into building model (ex. SiftonHQ.py)
        no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']

    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    # Allows fn to run outside of genEPJ (ie. via genEPJ/standalone/run_genEPJ_functions.sh)
    if not 'txt_thermsch_global_heat' in globals().keys():
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()

    obj_idx=-1

    def _not_none(mystr):
        if args[mystr]!=None: return True
        else: return False

    if 'heat_avail' in args:
        if _not_none('heat_avail'):
            #havail_temp,havail_defs=templ.HeatingCoilAvail()
            havail_temp,havail_defs=getattr(templ, args['heat_avail'])()
            new_objs.insert(obj_idx, idf_templater({}, havail_temp, havail_defs ) )
    if 'cool_avail' in args:
        if _not_none('cool_avail'):
            #cavail_temp,cavail_defs=templ.CoolingCoilAvail()
            cavail_temp,cavail_defs=getattr(templ, args['cool_avail'])()
            new_objs.insert(obj_idx, idf_templater({}, cavail_temp, cavail_defs ) )

    # Added for outages during resiliency studies. Override 'AlwaysOn' defaults using EMS/Erl
    hvac_sysavail_temp,hvac_sysavail_defs=templ.HVACtemplate_schedule_alwaysON2()
    hvac_availsch_nm= "HVAC Avail Sche" # Schedule type: 'Schedule:Constant'
    _d={
        'name': hvac_availsch_nm, # Schedule type: 'Schedule:Constant'
        'frac':      "1", # Default fraction of available
#        'frac':      "0", # Default fraction of available
        'limits':    "",
    }
    new_objs.insert(obj_idx, idf_templater(_d, hvac_sysavail_temp, hvac_sysavail_defs ) )

    # Foreach Zone:
    new_objs.insert(obj_idx, '! generate_IDF.py: Adding PTHP System to IDF file')
    for nm in zone_nm:

        printc("Adding Packaged-Terminal HP Unit to Zone: %s"%(mkcolor(nm,'green')), "blue")
        #   Add Terminal Unit: HVACTemplate:Zone:PTHP

        zone_defs={
              "zone_name": nm,
              "thermo_name": thermo_nm,
              "doas_name": "",
            }
        if 'heat_COP' in args:
            zone_defs['heat_COP']=args['heat_COP']
        if 'cool_COP' in args:
            zone_defs['cool_COP']=args['cool_COP']
        if 'heat_avail' in args:
            zone_defs['heat_avail']="HeatAvailSched"
        if 'cool_avail' in args:
            zone_defs['cool_avail']="CoolAvailSched"

        pthp_temp,pthp_defs=templ.HVACtemplate_PTHP_zone()
        if use_DOAS: # Insert DOAS name
            zone_defs["doas_name"]="DOAS"
            new_objs.insert(obj_idx, idf_templater(zone_defs, pthp_temp, pthp_defs ) )
        else:
            new_objs.insert(obj_idx, idf_templater(zone_defs, pthp_temp, pthp_defs ) )

    #==================================================
    printc("Adding HVACTemplate:Thermostat", 'yellow')
    #==================================================
    objs_sche=filter_IDF_objs_raw( new_objs, 'Schedule:Compact')
    objs_sche_nms = [ get_obj_name(o) for o in objs_sche ]
    if heatsp_nm not in objs_sche_nms:
        # Heating/Cooling Setpoint Schedules
        new_objs.insert(obj_idx, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
        new_objs.insert(obj_idx, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
        # Main thermostat
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )


    if options.debughvac:

        printc("Adding PTHP specific Output Variables", 'yellow')
        temp_output, output_defs =templ.template_output()

        output_vars=[
          'Zone Packaged Terminal Heat Pump Total Heating Rate',
          'Zone Packaged Terminal Heat Pump Total Cooling Rate',
          'Zone Packaged Terminal Heat Pump Sensible Heating Rate',
          'Zone Packaged Terminal Heat Pump Sensible Cooling Rate',
          'Zone Packaged Terminal Heat Pump Latent Heating Rate',
          'Zone Packaged Terminal Heat Pump Latent Cooling Rate',
          'Zone Packaged Terminal Heat Pump Electric Power',
          'Zone Packaged Terminal Heat Pump Fan Part Load Ratio',
          'Zone Packaged Terminal Heat Pump Compressor Part Load Ratio',
          'Heating Coil Air Heating Rate',
          'Heating Coil Electric Power',
          'Heating Coil Gas Rate',
          'Heating Coil Runtime Fraction',
          'Cooling Coil Total Cooling Rate',
          'Cooling Coil Electric Power',
      ]

        for v in output_vars:
            #new_objs.insert(obj_idx, idf_templater( {'name': v}, temp_output, {} ) )
            new_objs.insert(obj_idx, idf_templater( {'name': v, 'timestep': 'hourly'}, temp_output, {} ) )

    #new_objs = align_IDF_objs(new_objs)
    return new_objs

def add_HVAC_HP_file(to_file=to_file):
    """Modified version of `add_HVAC_HP` which creates an IDF output for testing purposes. File output uses suffix `_HP.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_HP, to_file=to_file, suffix='HP')

#def add_HVAC_HP(objs_all, use_DOAS=True, use_district=True):
#def add_HVAC_HP(objs_all, use_DOAS=False, use_district=True):
def add_HVAC_HP(objs_all, args={ 'use_DOAS': False, 'use_district': False } ):
    """Add HVACTemplate of Water Source Heat Pump (HP) system in specified `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `use_DOAS` link Zone to centralized DOAS system. `use_district` Water loop temperature controlled via district system

    Returns:

    * `new_objs`: genEPJ object list with HP HVACTemplate (Python `List`)
    """
    # METHOD:
    # ADD:
    #  1) HVACTemplate:Thermostat
    #  2) For each zone: HVACTemplate:Zone:WaterToAirHeatPump
    # IF boiler/cooling tower
    #  1) HVACTemplate:Plant:MixedWaterLoop
    #  2) HVACTemplate:Plant:Tower
    #  3) HVACTemplate:Plant:Boiler

    new_objs = list(objs_all)
    use_DOAS=args['use_DOAS']
    use_district=args['use_district']

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']
    #no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'corridor']
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    # Allows fn to run outside of genEPJ (ie. via genEPJ/standalone/run_genEPJ_functions.sh)
    if not 'txt_thermsch_global_heat' in globals().keys():
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()

    obj_idx=-1

    # Foreach Zone:
    new_objs.insert(obj_idx, '! generate_IDF.py: Adding WSHP System to IDF file')
    for nm in zone_nm:

        printc("Adding HP Unit to Zone: %s"%(mkcolor(nm,'green')), "blue")
        #   Add Terminal Unit: HVACTemplate:Zone:PTHP

        # Hot-water OR electric reheat
        #if use_district:
        #    supplement_heat="HotWater"
        #else:
        #    supplement_heat="Electric"

        zone_defs={
              "zone_name": nm,
              "thermo_name": thermo_nm,
              "doas_name": "",
              "supp_heat": "Electric",
              #"supp_heat": "HotWater",
            }
        hp_temp,hp_defs=templ.HVACtemplate_HP_zone()
        if use_DOAS: # Insert DOAS name
            zone_defs["doas_name"]="DOAS"
            new_objs.insert(obj_idx, idf_templater(zone_defs, hp_temp, hp_defs ) )
        else:
            new_objs.insert(obj_idx, idf_templater(zone_defs, hp_temp, hp_defs ) )

    #=============================================
    printc("Adding HVACTemplate:Plant", 'yellow')
    #=============================================
    # SB: Obtuse order to perform side-by-side testing with previous genEPJ version
    # Boiler
    boil_vars={
      'boiler_name': "Main Boiler",
      'boiler_type': "HotWaterBoiler",
      'boiler_eff': "0.8",
    }
    boil_temp,boil_defs=templ.HVACtemplate_boiler()
    # MWL
    MWL_vars={
      'temp_hsp_sche': "",
      'temp_hsp':      "30",
      'temp_lsp_sche': "",
      'temp_lsp':      "20",
    }
    MWL_temp,MWL_defs=templ.HVACtemplate_MWL()
    #
    if not use_district: # Use local boiler
        new_objs.insert(obj_idx, idf_templater({}, boil_temp, boil_defs ) )
        new_objs.insert(obj_idx, idf_templater(MWL_vars, MWL_temp, MWL_defs ) )
    else: # Use district energy source
        boil_vars["boiler_eff"]=1.0
        boil_vars["boiler_type"]='DistrictHotWater'
        new_objs.insert(obj_idx, idf_templater(boil_vars, boil_temp, boil_defs ) )
        # District Water Loops Temperature Schedules
        dist_temp,dist_defs=templ.HVACtemplate_thermosche_district()
        dist_vars_low={
          'name': "District-Loop-Temp-Low-Schedule",
          #'temp_low':  "15.0",
          #'temp_high':  "30.0",
          'temp_low':  "10.0", # CANSOFCOM update
          'temp_high':  "30.0",
        }
        dist_vars_hot={
          'name': "District-Loop-Temp-High-Schedule",
          'temp_low':  "20.0",
          'temp_high':  "40.0",
        }
        new_objs.insert(obj_idx, idf_templater(dist_vars_low, dist_temp, dist_defs ) )
        new_objs.insert(obj_idx, idf_templater(dist_vars_hot, dist_temp, dist_defs ) )
        # Mixed Water Loop
        MWL_vars={
          'MWL_name':      "Only Water Loop" ,
          'temp_hsp_sche': "District-Loop-Temp-High-Schedule",
          'temp_hsp':      "" ,
          'temp_lsp_sche': "District-Loop-Temp-Low-Schedule" ,
          'temp_lsp':      "" ,
        }
        new_objs.insert(obj_idx, idf_templater(MWL_vars, MWL_temp, MWL_defs ) )
    # Tower
    tow_temp,tow_defs=templ.HVACtemplate_tower()
    new_objs.insert(obj_idx, idf_templater({}, tow_temp, tow_defs ) )


    #==================================================
    printc("Adding HVACTemplate:Thermostat", 'yellow')
    #==================================================
    objs_sche=filter_IDF_objs_raw( new_objs, 'Schedule:Compact')
    objs_sche_nms = [ get_obj_name(o) for o in objs_sche ]
    if heatsp_nm not in objs_sche_nms:
        # Heating/Cooling Setpoint Schedules
        new_objs.insert(obj_idx, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
        new_objs.insert(obj_idx, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
        # Main thermostat
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )

    #new_objs = align_IDF_objs(new_objs)
    return new_objs

def match_occupancy_schedule_file(to_file=to_file):
    """Modified version of `match_occupancy_schedule` which creates an IDF output for testing purposes. File output uses suffix `_MATCHOcc.idf` by default."""
    return __abstract_add_objs2file(match_occupancy_schedule, to_file=to_file, suffix='MATCHOcc')

# TODO- Need to add other building type occupancy schedules: religious, supermarket, etc
def match_occupancy_schedule(objs_all, args={}):
    """Identifies and returns a schedule type (commercial or residential). Used to define ventilation schedules

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `occ_guestrm_*`: Commercial or Residential schedule object
    """

    objs_plp=filter_IDF_objs_raw(objs_all, 'People')
    #print("Plp",objs_plp)
    #if not to_file: to_file=try2get(str, glob('*prep.idf') )

    occ_guestrm_resi=[obj for obj in objs_plp if 'apartment' in get_obj_name(obj).lower()]
    occ_guestrm_comm=[obj for obj in objs_plp if 'office' in get_obj_name(obj).lower()]
    #print("Resi",occ_guestrm_resi)
    #print("Comm",occ_guestrm_comm)

    if len(occ_guestrm_resi) >= len(occ_guestrm_comm):
        #return get_obj_abstract(occ_guestrm_resi[0], 3)
        return occ_guestrm_resi
    elif len(occ_guestrm_resi)==len(occ_guestrm_comm)==0 :
        printc('ERROR!: DOAS: No occupancy schedule associated with People object','red')
        raise ValueError("add_DOAS has no valid option People schedules to work from")
    else:
        #return get_obj_abstract(occ_guestrm_comm[0], 3)
        return occ_guestrm_comm


def add_HVAC_DOAS_file(to_file=to_file):
    """Modified version of `add_HVAC_DOAS` which creates an IDF output for testing purposes. File output uses suffix `_DOAS.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_DOAS, to_file=to_file, suffix='DOAS')

def add_HVAC_DOAS(objs_all, args={ 'need_boiler': False, 'need_chiller': False, 'use_coils': False, 'to_file': None } ):
    """Add HVACTemplate of a dedicated outdoor air system (DOAS). Allow for peak output specification if applied to individual zones.

    User required to specify at least one HVACTemplate:Thermostat object.

    `HVACTemplate:Zone` must refer to the DOAS name defined here.

    `add_HVAC_DOAS` must be defined in conjunction with the following objects:

    * HVACTemplate:Zone:BaseboardHeat (`add_HVAC_Baseboard`)
    * HVACTemplate:Zone:FanCoil (`add_HVAC_FCU`)
    * HVACTemplate:Zone:PTAC (`add_HVAC_PTAC`)
    * HVACTemplate:Zone:PTHP (`add_HVAC_PTHP`)
    * HVACTemplate:Zone:WaterToAirHeatPump (`add_HVAC_HP`)
    * HVACTemplate:Zone:VRF (`add_HVAC_VRF`)

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `need_boiler/need_chiller` when `True`, implies that heating/cooling must be provided to the DOAS. When set to `False`, it may imply that centralized district systems are used to heat/cool air going into the DOAS. `use_coils` turn off/on heating/cooling coils to preheat/precool air. `to_file` used to specify `People` schedule (mark for refactoring).

    Returns:

    * `new_objs`: genEPJ object list with DOAS HVACTemplate (Python `List`)
    """

    # NOTE: This implementation also adds a centralized HeatExchanger:AirToAir:SensibleAndLatent
    need_boiler=args['need_boiler']
    need_chiller=args['need_chiller']
    use_coils=args['use_coils']
    to_file=args['to_file']

    # Ensure no previous DOAS systems are defined
    #if 'HVACTemplate:System:DedicatedOutdoorAir' in '\n'.join(objs_all):
    #    raise ValueError("DOAS fn: Found existing DOAS system. Not adding another")

    #printc("Removing HVAC objects!", 'blue')
    #new_objs=rm_all_HVAC(objs_all)

    objs_filt_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    obj_idxs = [i for i,obj in enumerate(objs_all) if get_obj_type(obj)=='Zone']
    #print("Found matching indexes: ",obj_idxs)

    new_objs=list(objs_all)

    # Modifying Simulation Control Object (if available)
    # NOTE: DOAS requires System sizing to be set to 'Yes'
    obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='SimulationControl']
    if obj_idxs:
        # MODIFY SimulationControl
        objs_simcontrl=filter_IDF_objs_raw(objs_all, 'SimulationControl')[0]
        new_objs[obj_idxs[0]]=set_simcontrl_sizing(objs_simcontrl, 'Yes')

    # Match People object and extract occupancy schedule
    ## NOTE: Easier to extract occupancy schedule name from the People object than find in Schedule:* objs
        #return get_obj_abstract(occ_guestrm_resi[0], 3)
    occ_plp_objs=match_occupancy_schedule(objs_all)
    #print(occ_plp_objs)
    occ_sch_name=get_obj_abstract(occ_plp_objs[0], 3)
    print("DOAS: Use occupancy schedule name '%s' for DOAS system control"%(mkcolor(occ_sch_name,'yellow')))


    #==================================================
    printc("Adding DOAS HVACTemplate objects","green")
    #==================================================
    # DOAS boilers needed for some systems:
    # DOAS can't use HP coils for heating... Need post-processing
    if need_boiler:
        objs_HWL=filter_IDF_objs_raw(new_objs, 'HotWaterLoop')
        if len(objs_HWL)>=1 :
            printc("ERROR: Multiple HotWaterLoops defined!","red")
        printc("Adding DOAS HVACTemplate BOILER","green")
        # HWL
        HWL_temp,HWL_defs=templ.HVACtemplate_HWL()
        new_objs.insert(-1, idf_templater({'HWL_name': "Hot Water Loop DOAS"}, HWL_temp, HWL_defs ) )
        # Boiler
        boil_temp,boil_defs=templ.HVACtemplate_boiler()
        new_objs.insert(-1, idf_templater({'boiler_name': "DOAS Boiler"}, boil_temp, boil_defs ) )
    # Chiller
    # DOAS chillers and loops needed for some systems: PTAC, PTHP, ...
    # DOAS can't use HP coils for cooling...
    if need_chiller:
        objs_CWL=filter_IDF_objs_raw(new_objs, 'ChilledWaterLoop')
        if len(objs_CWL)>=1 :
            printc("ERROR: Multiple ChilledWaterLoops defined!","red")
        printc("Adding DOAS HVACTemplate CHILLER","green")
        d={
          'CWL_name': "Chilled Water Loop DOAS",
          'outdoor_temp': "", # No limit on minimal OA temperature
        }
        CWL_temp,CWL_defs=templ.HVACtemplate_CWL()
        new_objs.insert(-1, idf_templater(d, CWL_temp, CWL_defs ) )
        # Chiller
        chill_temp,chill_defs=templ.HVACtemplate_chiller()
        new_objs.insert(-1, idf_templater({ 'chiller_name': "DOAS Chiller" }, chill_temp, chill_defs ) )
        # Tower
        tow_temp,tow_defs=templ.HVACtemplate_tower()
        new_objs.insert(-1, idf_templater({ 'tower_name': "DOAS Tower" }, tow_temp, tow_defs ) )

    doasys_temp,doasys_defs=templ.HVACtemplate_DOAS_system()
    if use_coils: # DOAS with HC and CC
        new_objs.insert(-1, idf_templater({'avail_sche': occ_sch_name, 'coil_avail_sche': "" }, doasys_temp, doasys_defs ) )
    else:         # DOAS with NO HC and CC: SB: actural disabled Electric coils and disabled DXCoils
        # Set heating/cooling coils to OFF
        d={
          'name': "ALWAYS OFF DOAS",
          'frac': "0",
        }
        availOFF_temp, availOFF_defs = templ.HVACtemplate_schedule_alwaysON()
        new_objs.insert(-1, idf_templater(d, availOFF_temp, availOFF_defs ) )
        #
        d={
          'name': "DOAS",
          'avail_sche': occ_sch_name,
          'cool_coil': "HeatExchangerAssistedDX",
          'heat_coil': "Electric",
          'coil_avail_sche': "ALWAYS OFF DOAS",
        }
        # TEST to see if DX coils makes different in EUI: SB: adds 2kWh/m2 to EUI
        new_objs.insert(-1, idf_templater(d, doasys_temp, doasys_defs ) )

    return new_objs


def add_HVAC_Baseboard_file(to_file=to_file):
    """Modified version of `add_HVAC_Baseboard` which creates an IDF output for testing purposes. File output uses suffix `_bboard.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_Baseboard, to_file=to_file, suffix='bboard')

def add_HVAC_Baseboard(objs_all, args={ 'use_DOAS': False, 'capacity': 'autosize' } ):
    """Add HVACTemplate of Baseboards in specified `Zones`. Allow for peak output specfication if applied to individual zones.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `use_DOAS` Use a dedicated outdoor air system for providing ventilation air to `Zone`, `capacity` peak size of baseboard heater (if `None` specified, will be set to `autosize`).

    Returns:

    * `new_objs`: genEPJ object list with Baseboard HVACTemplate (Python `List`)
    """

    use_DOAS = args['use_DOAS']
    try:
        capacity = args['capacity']
    except:
        capacity = 'autosize'

    new_objs = list(objs_all)

    if 'no_mech_lst' in args:
        no_mech_lst=args['no_mech_lst']
    else:
        no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']

    # Modifying Simulation Control Object (if available)
    # Baseboard requires systems sizing (as of Eplus v8.6)
    obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='SimulationControl']
    if obj_idxs:
        # MODIFY SimulationControl
        objs_simcontrl=filter_IDF_objs_raw(objs_all, 'SimulationControl')[0]
        new_objs[obj_idxs[0]]=set_simcontrl_sizing(objs_simcontrl, 'Yes')

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    #no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'corridor']
    # VD: Add specific zones if specified
    if 'zone_selective_add' in args:
        zone_selective_add = args['zone_selective_add']
        zone_nm = [get_obj_name(myobj) for myobj in objs_zon if zone_selective_add in get_obj_name(myobj).lower()]
    # Apply to every zone except to the "no_mech_lst"
    else:
        zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    # Allows fn to run outside of genEPJ (ie. via genEPJ/standalone/run_genEPJ_functions.sh)
    if not 'txt_thermsch_global_heat' in globals().keys():
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()

    #print("Thermo test")
    #print( 'txt_thermsch_global_heat' in globals().keys() )
    #print( 'txt_thermsch_global_cool' in globals().keys() )
    ##print( globals().keys() )
    #print(str(txt_thermsch_global_heat))
    #print(str(txt_thermsch_global_cool))

    obj_idx=-1

    # Added for outages during resiliency studies. Override 'AlwaysOn' defaults using EMS/Erl
    hvac_sysavail_temp,hvac_sysavail_defs=templ.HVACtemplate_schedule_alwaysON2()
    hvac_availsch_nm= "HVAC Avail Sche" # Schedule type: 'Schedule:Constant'
    _d={
        'name': hvac_availsch_nm, # Schedule type: 'Schedule:Constant'
        'frac':      "1", # Default fraction of available
#        'frac':      "0", # Default fraction of available
        'limits':    "",
    }
    new_objs.insert(obj_idx, idf_templater(_d, hvac_sysavail_temp, hvac_sysavail_defs ) )

    # Foreach Zone:
    new_objs.insert(obj_idx, '! generate_IDF.py: Adding Baseboard System to IDF file')
    for nm in zone_nm:

        printc("Adding Baseboard Unit to Zone: %s"%(mkcolor(nm,'green')), "blue")
        #   Add Terminal Unit: HVACTemplate:Zone:Baseboard

        zone_defs={
              "zone_name": nm,
              "thermo_name": thermo_nm,
              "doas_name": "",
              "sys_avail": hvac_availsch_nm,
              "supp_heat": "Electric",
              #"supp_heat": "HotWater",
              "capacity": capacity,
            }
        bb_temp,bb_defs=templ.HVACtemplate_Baseboard_zone()
        if use_DOAS: # Insert DOAS name
            zone_defs["doas_name"]="DOAS"
            new_objs.insert(obj_idx, idf_templater(zone_defs, bb_temp, bb_defs ) )
        else:
            new_objs.insert(obj_idx, idf_templater(zone_defs, bb_temp, bb_defs ) )

    #==================================================
    printc("Adding HVACTemplate:Thermostat", 'yellow')
    #==================================================
    objs_sche=filter_IDF_objs_raw( new_objs, 'Schedule:Compact')
    objs_sche_nms = [ get_obj_name(o) for o in objs_sche ]
    if heatsp_nm not in objs_sche_nms:
        # Heating/Cooling Setpoint Schedules
        new_objs.insert(obj_idx, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
        new_objs.insert(obj_idx, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
        # Main thermostat
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )

    #new_objs = align_IDF_objs(new_objs)
    return new_objs

def add_HVAC_RTU_file(to_file=to_file):
    """Modified version of `add_HVAC_RTU` which creates an IDF output for testing purposes. File output uses suffix `_RTU.idf` by default."""
    return __abstract_add_objs2file(add_HVAC_RTU, to_file=to_file, suffix='RTU')

def add_HVAC_RTU(objs_all, args={ 'use_DOAS': False, 'use_district': False }):
    """Add HVACTemplate of Roof Top Unit (RTU) system in specified `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `use_DOAS` link Zone to centralized DOAS system. `use_district` Water loop temperature controlled via district system

    Returns:

    * `new_objs`: genEPJ object list with RTU HVACTemplate (Python `List`)
    """

    new_objs=list(objs_all)

    # Modifying Simulation Control Object (if available)
    # RTUs requires systems sizing
    obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='SimulationControl']
    if obj_idxs:
        # MODIFY SimulationControl
        objs_simcontrl=filter_IDF_objs_raw(objs_all, 'SimulationControl')[0]
        new_objs[obj_idxs[0]]=set_simcontrl_sizing(objs_simcontrl, 'Yes')

    availsch_nm="AlwaysOnRTU"
    fansch_nm="FanAvailSchedRTU"
    OAavailsch_nm="Min OA Sched RTU"
    rtu_nm="RTUDX "

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    if 'no_mech_lst' in args:
        no_mech_lst=args['no_mech_lst']
    else:
        # SB TODO: Move into building model (ex. SiftonHQ.py)
        no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'storage']
    print("RTU: No add list: ", no_mech_lst)
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    # Allows fn to run outside of genEPJ (ie. via genEPJ/standalone/run_genEPJ_functions.sh)
    if not 'txt_thermsch_global_heat' in globals().keys():
        global txt_thermsch_global_heat, tempsch_def_heat
        global txt_thermsch_global_cool, tempsch_def_cool
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()

    obj_idx=-1

    # Which zones to add district/heat recovery to
    # Mocks heat recovery from a refridgeration system
    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    # ADD TO HR TO ALL ZONES
    if 'zone_selective_add' in args:
        zone_use_district_nms = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower() )]
        print(zone_use_district_nms)
    ## ADD TO HR TO GIVEN ZONES
    #if 'zone_selective_add' in args:
    #    zone_selective_add = args['zone_selective_add']
    #    #zone_use_district_nms = [get_obj_name(myobj) for myobj in objs_zon if zone_selective_add in get_obj_name(myobj).lower()]
    #    zone_use_district_nms = [get_obj_name(myobj) for myobj in objs_zon if is_in(zone_selective_add, get_obj_name(myobj).lower() )]
    #    print(zone_use_district_nms)
    # Otherwise, DONT apply to zones
    else:
        zone_use_district_nms = []

    # Do any zones use district? if so ADD BOILER/HWL
    if zone_use_district_nms:
        # Boiler
        boil_vars={
          'boiler_name': "HeatRecovery Boiler",
          'boiler_type': "DistrictHotWater",
          #'boiler_type': "HotWaterBoiler",
          'boiler_eff': "1.0",
          #'boiler_fuel': "OtherFuel1",
        }
        boil_temp,boil_defs=templ.HVACtemplate_boiler()
        new_objs.insert(obj_idx, idf_templater(boil_vars, boil_temp, boil_defs ) )
        ## Add OtherFuel (Don't want to account in District category)
        #d={'name': 'OtherFuel1',
        #   'unit': 'm3',
        #   #'energy_unit': '1000',
        #   'energy_unit': '0.001',
        #   #'source_PEF': '1000', }
        #   'source_PEF': '0.001', }
        #fuel_temp,fuel_defs=templ.add_misc_PEF()
        #new_objs.insert(obj_idx, idf_templater(d, fuel_temp, fuel_defs ) )
        # Hot-Water Loop
        d={'HWL_name': "HeatRecovery Loop",
           'HWL_config': "ConstantFlow",
           'pump_head': "1000", # key parameter for large buildings
           'HWL_setpoint_reset': "None", }
        HWL_temp,HWL_defs=templ.HVACtemplate_HWL()
        new_objs.insert(obj_idx, idf_templater(d, HWL_temp, HWL_defs ) )

    # Calculate total area of district/heat recovery. Will be used to scale up/down fraction of baseboard total size
    total_district_area=0.0
    for znnm in zone_use_district_nms:
        area = float( _calc_area_intmass( znnm.upper() ) )/2.0 # intmass has a x2 multiplier
        total_district_area = total_district_area + area
        printc("Adding Zone: %s to with Area: %.1f to District/HeatRecovery List"%(mkcolor(znnm,'green'), area), "blue")

    rtu_temp,rtu_defs=templ.HVACtemplate_RTU_zone()
    rtu_sys,rtusys_defs=templ.HVACtemplate_RTU_system()
    # Foreach Zone:
    new_objs.insert(obj_idx, '! generate_IDF.py: Adding RTU System to IDF file')
    for nm in zone_nm:

        printc("Adding RTU Unit to Zone: %s"%(mkcolor(nm,'green')), "blue")
        zone_defs={
              "zone_name": nm,
              "rtu_name": rtu_nm+nm,
              "thermo_name": thermo_nm,
              "fan_sch": fansch_nm,
              "oa_sche": OAavailsch_nm,
              "avail_sche": availsch_nm,
              # SB: Added cause unmet hours changed RTU HR savings (Longos)
              "baseboard":      'Electric',
              "baseboard_size": 'autosize',
            }
        if nm in zone_use_district_nms:
            area = float( _calc_area_intmass( nm.upper() ) )/2.0 # intmass has a x2 multiplier
            zone_defs['baseboard']='HotWater'
            recov_size= float( args['recovery_size'] )
            zone_defs['baseboard_size']= "%.0f"%(recov_size * area/total_district_area)
            zone_defs['baseboard_availsche']= availsch_nm
            printc("Adding RTU heat recovery to Zone: %s"%(mkcolor(nm,'green')), "blue")
        new_objs.insert(obj_idx, idf_templater(zone_defs, rtu_temp, rtu_defs ) )
        new_objs.insert(obj_idx, idf_templater(zone_defs, rtu_sys, rtusys_defs ) )

        # TODO- Does the zone use district?

        #if use_DOAS: # Insert DOAS name
        #    zone_defs["doas_name"]="DOAS"
        #else:
        #    new_objs.insert(obj_idx, idf_templater(zone_defs, rtu_temp, rtu_defs ) )

    #==================================================
    printc("Adding HVACTemplate:Thermostat", 'yellow')
    #==================================================
    objs_sche=filter_IDF_objs_raw( new_objs, 'Schedule:Compact')
    objs_sche_nms = [ get_obj_name(o) for o in objs_sche ]
    if heatsp_nm not in objs_sche_nms:
        # Heating/Cooling Setpoint Schedules
        new_objs.insert(obj_idx, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
        new_objs.insert(obj_idx, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
        # Main thermostat
        d={
          "thermo_nm": thermo_nm,
          "hsp_sche": heatsp_nm,
          "csp_sche": coolsp_nm,
        }
        thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
        new_objs.insert(obj_idx, idf_templater(d, thermo_temp, thermo_defs ) )
    # Fan availability schedules
    avail_sche, avail_defs = templ.HVACtemplate_schedule_avail()
    new_objs.insert(obj_idx, idf_templater({"avail_nm": fansch_nm}, avail_sche, avail_defs) )
    # OA availability schedule
    # SB: TODO: OA OFF from 12am to 8am. Wont work on residential!!
    OA_temp,OA_defs=templ.HVACtemplate_OAschedule_avail()
    new_objs.insert(obj_idx, idf_templater({'oa_sche': OAavailsch_nm}, OA_temp, OA_defs ) )
    # System availability: Always ON
    avail_temp, avail_defs = templ.HVACtemplate_schedule_alwaysON2()
    new_objs.insert(obj_idx, idf_templater({'name': availsch_nm}, avail_temp, avail_defs ) )


    if options.debughvac:
        printc("Adding RTU specific Output Variables", 'yellow')

        temp_output, output_defs =templ.template_output()

        output_vars=[
        ]

        for v in output_vars:
            new_objs.insert(obj_idx, idf_templater( {'name': v}, temp_output, {} ) )

    #new_objs = align_IDF_objs(new_objs)
    return new_objs

def mod_HVAC_district_file(to_file=to_file):
    """Modified version of `mod_HVAC_district` which creates an IDF output for testing purposes. File output uses suffix `_HVACdistrict.idf` by default."""
    return __abstract_add_objs2file(mod_HVAC_district, to_file=to_file, suffix='HVACdistrict')

# SB: This script is run *after* add_HVAC_... Swap out existing Boiler/Chiller for district systems.
def mod_HVAC_district(objs_all, args={'use_district': False}):
    """Modify a previous HVACTemplate swapping out the Chiller/Boiler for a District system.

    **Mark for deletion (redundant with dispatch_HVAC)**

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `use_district` Flag to make the district system swap. If set to False, NO CHANGES ARE MADE (converts this fn to an Identity fn).

    Returns:

    * `new_objs`: genEPJ object list with an HVACTemplate using a District system  (Python `List`)
    """


    new_objs=list(objs_all)

    if 'use_district' in args:
        use_district=args['use_district']

    if use_district:

        # Remove old boiler
        new_objs= [obj for obj in objs_all if 'site:groundtemperature:deep' not in get_obj_type(obj).lower()]
        new_objs= [obj for obj in objs_all if 'site:groundtemperature:buildingsurface' not in get_obj_type(obj).lower()]

        new_objs.insert(obj_idx, idf_templater({'cond_type': "WaterCooled"}, vrfsys_temp, vrfsys_defs ) )
        # District Water Loops Temperature Schedules
        dist_temp,dist_defs=templ.HVACtemplate_thermosche_district()
        dist_vars_low={
          'name': "District-Loop-Temp-Low-Schedule",
          'temp_low':  "15.0",
          'temp_high':  "30.0",
        }
        dist_vars_hot={
          'name': "District-Loop-Temp-High-Schedule",
          'temp_low':  "20.0",
          'temp_high':  "40.0",
        }
        new_objs.insert(obj_idx, idf_templater(dist_vars_low, dist_temp, dist_defs ) )
        new_objs.insert(obj_idx, idf_templater(dist_vars_hot, dist_temp, dist_defs ) )
        # Mixed Water Loop
        MWL_temp,MWL_defs=templ.HVACtemplate_MWL()
        MWL_vars={
          'MWL_name':      "Only Water Loop" ,
          'temp_hsp_sche': "District-Loop-Temp-High-Schedule",
          'temp_hsp':      "" ,
          'temp_lsp_sche': "District-Loop-Temp-Low-Schedule" ,
          'temp_lsp':      "" ,
        }
        new_objs.insert(obj_idx, idf_templater(MWL_vars, MWL_temp, MWL_defs ) )
        # Tower
        tow_temp,tow_defs=templ.HVACtemplate_tower()
        new_objs.insert(obj_idx, idf_templater({}, tow_temp, tow_defs ) )
        # Boiler
        boil_vars={
          'boiler_name': "Main Boiler",
          'boiler_type': "DistrictHotWater",
          'boiler_eff': "0.8",
        }
        boil_temp,boil_defs=templ.HVACtemplate_boiler()
        #
        boil_vars["boiler_eff"]=1.0
        boil_vars["boiler_type"]='DistrictHotWater'
        new_objs.insert(obj_idx, idf_templater(boil_vars, boil_temp, boil_defs ) )

    return new_objs

def add_DHWNGplant_file(to_file=to_file):
    """Modified version of `add_DHWNGplant` which creates an IDF output for testing purposes. File output uses suffix `_DHWNGplant.idf` by default."""
    return __abstract_add_objs2file(add_DHWNGplant, to_file=to_file, suffix='DHWNGplant')

# SB: Usage of args is assumed to be applied to DHW Tank
def add_DHWNGplant(objs_all, args={}):
    """Add a NaturalGas DHW Tank with default efficiency of X. Requires that `WaterUse:Equipment` objects be previously defined.


    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: Dictionary of tank volume size, efficiency, skin losses, etc (Python Dict)

    Returns:

    * `new_objs`: genEPJ object list with newly added NaturalGas DHW tank (Python `List`)
    """

    # Do nothing if previous tanks are in the file
    if any([True for obj in objs_all if ((get_obj_type(obj)=='WaterHeater:Mixed') and (get_obj_abstract(obj,11).upper()=='NATURALGAS'))]):
        printc("Existing DHW NG objects found. Do nothing!",'red')
        return objs_all # NG DHW already exists, return objects

    new_objs=list(objs_all)

    # Schedules:Compact
    staticsche_temp, staticsche_defs = templ.HVACtemplate_schedule_alwaysON()
    # DHW ambient temperature
    d={'name': 'SWHSys1 Water Heater Ambient Temperature Schedule Name',
       'type': 'Temperature',
       'frac': '22.0'}
    new_objs.insert(-1, idf_templater(d, staticsche_temp, staticsche_defs ) )
    # DHW heater setpoint
    d={'name': 'SWHSys1 Water Heater Setpoint Temperature Schedule Name',
       'type': 'Temperature',
       'frac': '60.0'}
    new_objs.insert(-1, idf_templater(d, staticsche_temp, staticsche_defs ) )
    # DHW loop setpoint
    d={'name': 'SWHSys1-Loop-Temp-Schedule',
       'type': 'Temperature',
       'frac': '60.0'}
    new_objs.insert(-1, idf_templater(d, staticsche_temp, staticsche_defs ) )
    # DHW scheduled SP manager
    sp_temp,sp_defs = templ.SetpointManager()
    d={'name':     "SWHSys1 Loop Setpoint Manager",
       'sche_name':"SWHSys1-Loop-Temp-Schedule",
       'sp_name':  "SWHSys1 Supply Outlet Node"}
    new_objs.insert(-1, idf_templater(d, sp_temp, sp_defs ) )
    # DHW availability
    dhwavail_temp, dhwavail_defs = templ.HVACtemplate_schedule_alwaysON2()
    new_objs.insert(-1, idf_templater({'name': "ALWAYS ON DHW", 'limits': "ANY"}, dhwavail_temp, dhwavail_defs ) )
    # DHW Tank
    tank_temp, tank_defs = templ.DHW_WaterHeaterMixed()
    d={'fuel': "NATURALGAS",
              'eff': "0.8", }
    # SB: Adding additional args to tank
    for k in args.keys():
        d[k]=args[k]
    new_objs.insert(-1, idf_templater(d, tank_temp, tank_defs ) )

    pump_temp, pump_defs = templ.Pump()
    d={ 'name': 'SWHSys1 Pump',
        'inlet_node': 'SWHSys1 Supply Inlet Node',
        'outlet_node': 'SWHSys1 Pump-SWHSys1 Water HeaterNodeviaConnector', }
    new_objs.insert(-1, idf_templater(d, pump_temp, pump_defs ) )

    size_temp, size_defs = templ.Plant_Sizing()
    d={ 'loop_name':'SWHSys1',
        'loop_type':'Heating',
        'temp':     '60',
        'deltaC':   '5.0', }
    new_objs.insert(-1, idf_templater(d, size_temp, size_defs ) )

    pipe_temp, pipe_defs = templ.DHW_PipeAdiabatic()
    d={'name':  "SWHSys1 Demand Bypass Pipe",
       'inlet': "SWHSys1 Demand Bypass Pipe Inlet Node",
       'outlet':"SWHSys1 Demand Bypass Pipe Outlet Node", }
    new_objs.insert(-1, idf_templater(d, pipe_temp, pipe_defs ) )
    d={'name':  "SWHSys1 Demand Inlet Pipe",
       'inlet': "SWHSys1 Demand Inlet Node",
       'outlet':"SWHSys1 Demand Inlet Pipe-SWHSys1 Demand Mixer", }
    new_objs.insert(-1, idf_templater(d, pipe_temp, pipe_defs ) )
    d={'name':  "SWHSys1 Demand Outlet Pipe",
       'inlet': "SWHSys1 Demand Mixer-SWHSys1 Demand Outlet Pipe",
       'outlet':"SWHSys1 Demand Outlet Node", }
    new_objs.insert(-1, idf_templater(d, pipe_temp, pipe_defs ) )
    d={'name':  "SWHSys1 Supply Equipment Bypass Pipe",
       'inlet': "SWHSys1 Supply Equip Bypass Inlet Node",
       'outlet':"SWHSys1 Supply Equip Bypass Outlet Node", }
    new_objs.insert(-1, idf_templater(d, pipe_temp, pipe_defs ) )
    d={'name':  "SWHSys1 Supply Outlet Pipe",
       'inlet': "SWHSys1 Supply Mixer-SWHSys1 Supply Outlet Pipe",
       'outlet':"SWHSys1 Supply Outlet Node", }
    new_objs.insert(-1, idf_templater(d, pipe_temp, pipe_defs ) )

    loop_temp, loop_defs = templ.Plant_Loop()
    d={ 'loop_name': 'SWHSys1',
        'loop_type': 'Water',
        'supply_inlet': 'SWHSys1 Supply Inlet Node',
        'supply_outlet': 'SWHSys1 Supply Outlet Node',
        'supply_branch': 'SWHSys1 Supply Branches',
        'supply_connect': 'SWHSys1 Supply Connectors',
        'demand_inlet': 'SWHSys1 Demand Inlet Node',
        'demand_outlet': 'SWHSys1 Demand Outlet Node',
        'demand_branch': 'SWHSys1 Demand Branches',
        'demand_connect': 'SWHSys1 Demand Connectors',
        'scheme': 'SWHSys1 Loop Operation Scheme List',
        'outlet_node': 'SWHSys1 Supply Outlet Node', }
    new_objs.insert(-1, idf_templater(d, loop_temp, loop_defs ) )

    eqlst_temp, eqlst_defs = templ.Plant_EquipmentList()
    d={ 'name': 'SWHSys1 Equipment List',
        'type': 'WaterHeater:Mixed',
        'eq_name': 'SWHSys1 Water Heater', }
    new_objs.insert(-1, idf_templater(d, eqlst_temp, eqlst_defs ) )

    scheme_temp, scheme_defs = templ.Plant_EquipmentOperationList()
    d={ 'name':   'SWHSys1 Loop Operation Scheme List',
        'type':   'PlantEquipmentOperation:HeatingLoad',
        'scheme': 'SWHSys1 Operation Scheme',
        'sche':    'ALWAYS ON DHW', }
    new_objs.insert(-1, idf_templater(d, scheme_temp, scheme_defs ) )

    opheat_temp, opheat_defs = templ.Plant_EquipmentOperationHeating()
    d={ 'name':    'SWHSys1 Operation Scheme',
        'lower':   '0.0',
        'upper':  '%d'%(1e15),
        'list_nm': 'SWHSys1 Equipment List', }
    new_objs.insert(-1, idf_templater(d, opheat_temp, opheat_defs ) )


    #  'contrl_type': 'Bypass',
    branch_temp, branch_defs = templ.Branch()
    defs_dmdbr={
        'name':        'SWHSys1 Demand Load Branch %(n)d',
        'type':        'WaterUse:Connections',
        'comp_nm':     '%(nm)s',
        'inlet_node':  '%(nm)s Water Inlet Node',
        'outlet_node':  '%(nm)s Water Outlet Node',
        'contrl_type': 'Active', }
    defs_outbr={
        'name':        'SWHSys1 Demand Outlet Branch',
        'type':        'Pipe:Adiabatic',
        'comp_nm':     'SWHSys1 Demand Outlet Pipe',
        'inlet_node':  'SWHSys1 Demand Mixer-SWHSys1 Demand Outlet Pipe',
        'outlet_node':  'SWHSys1 Demand Outlet Node',
        'contrl_type': 'Passive', }
    defs_supeqbr={
        'name':        'SWHSys1 Supply Equipment Branch',
        'type':        'WaterHeater:Mixed',
        'comp_nm':     'SWHSys1 Water Heater',
        'inlet_node':  'SWHSys1 Pump-SWHSys1 Water HeaterNode',
        'outlet_node': 'SWHSys1 Supply Equipment Outlet Node',
        'contrl_type': 'Active', }
    defs_supeqbybr={
        'name':        'SWHSys1 Supply Equipment Bypass Branch',
        'type':        'Pipe:Adiabatic',
        'comp_nm':     'SWHSys1 Supply Equipment Bypass Pipe',
        'inlet_node':  'SWHSys1 Supply Equip Bypass Inlet Node',
        'outlet_node': 'SWHSys1 Supply Equip Bypass Outlet Node',
        'contrl_type': 'Bypass', }
    defs_supinbr={
        'name':        'SWHSys1 Supply Inlet Branch',
        'type':        'Pump:ConstantSpeed',
        'comp_nm':     'SWHSys1 Pump',
        'inlet_node':  'SWHSys1 Supply Inlet Node',
        'outlet_node': 'SWHSys1 Pump-SWHSys1 Water HeaterNodeviaConnector',
        'contrl_type': 'Active', }
    defs_supoutbr={
        'name':        'SWHSys1 Supply Outlet Branch',
        'type':        'Pipe:Adiabatic',
        'comp_nm':     'SWHSys1 Supply Outlet Pipe',
        'inlet_node':  'SWHSys1 Supply Mixer-SWHSys1 Supply Outlet Pipe',
        'outlet_node': 'SWHSys1 Supply Outlet Node',
        'contrl_type': 'Passive', }
    defs_dmdbybr={
        'name':        'SWHSys1 Demand Bypass Branch',
        'type':        'Pipe:Adiabatic',
        'comp_nm':     'SWHSys1 Demand Bypass Pipe',
        'inlet_node':  'SWHSys1 Demand Bypass Pipe Inlet Node',
        'outlet_node': 'SWHSys1 Demand Bypass Pipe Outlet Node',
        'contrl_type': 'Bypass', }
    defs_dmdinbr={
        'name':        'SWHSys1 Demand Inlet Branch',
        'type':        'Pipe:Adiabatic',
        'comp_nm':     'SWHSys1 Demand Inlet Pipe',
        'inlet_node':  'SWHSys1 Demand Inlet Node',
        'outlet_node': 'SWHSys1 Demand Inlet Pipe-SWHSys1 Demand Mixer',
        'contrl_type': 'Passive', }

    allbrdefs=[defs_outbr, defs_supeqbr, defs_supeqbybr, defs_supinbr, defs_supoutbr, defs_dmdbybr, defs_dmdinbr]

    # TODO- Refactors for:
    # 1. Object Type/Name combination list Ex. txt_demandbranchlst_st
    # 2. Object Name list Ex. txt_supplybranchlst
    # Templates for DemandBranchList
    # TODO- Mark for refactor using iterative method
    txt_demandbranchlst_st="""
  BranchList,
    SWHSys1 Demand Branches, !- Name
    SWHSys1 Demand Inlet Branch,  !- Branch 1 Name
"""
    temp_demandbranchlst_mi="""    SWHSys1 Demand Load Branch %d,  !- Branch %d Name
"""
    temp_demandbranchlst_en="""    SWHSys1 Demand Bypass Branch,  !- Branch %d Name
    SWHSys1 Demand Outlet Branch;  !- Branch %d Name
"""

    txt_supplybranchlst="""
  BranchList,
    SWHSys1 Supply Branches, !- Name
    SWHSys1 Supply Inlet Branch,  !- Branch 1 Name
    SWHSys1 Supply Equipment Branch,  !- Branch 2 Name
    SWHSys1 Supply Equipment Bypass Branch,  !- Branch 3 Name
    SWHSys1 Supply Outlet Branch;  !- Branch 4 Name
"""

    wateruse_temp, wateruse_defs = templ.Water_Connections()
    defs_conn={
       'name':       "%(nm)s",
       'inlet_node': "%(nm)s Water Inlet Node",
       'outlet_node':"%(nm)s Water Outlet Node",
       'eq_name':    "%(nm)s", }

    # TODO- Mark for refactor using iterative method
    # Demand Splitter on Outlet Side: 3 string templates
    txt_demandsplt_st="""
  Connector:Splitter,
    SWHSys1 Demand Splitter, !- Name
    SWHSys1 Demand Inlet Branch,  !- Inlet Branch Name
"""
    temp_demandspli_mi="""    SWHSys1 Demand Load Branch %d,  !- Outlet Branch %d Name
"""
    temp_demandspli_en="""    SWHSys1 Demand Bypass Branch;  !- Outlet Branch %d Name
"""

    # TODO- Mark for refactor using iterative method
    # Demand Mixer on Inlet Side: 3 string templates
    txt_demandmix_st="""
  Connector:Mixer,
    SWHSys1 Demand Mixer, !- Name
    SWHSys1 Demand Outlet Branch,  !- Outlet Branch Name
"""
    temp_demandmix_mi="""    SWHSys1 Demand Load Branch %d,  !- Inlet Branch %d Name
"""
    temp_demandmix_en="""    SWHSys1 Demand Bypass Branch;  !- Inlet Branch %d Name
"""

    # TODO- Mark for refactor using iterative method
    txt_supplysplit_mix="""
  Connector:Splitter,
    SWHSys1 Supply Splitter, !- Name
    SWHSys1 Supply Inlet Branch,  !- Inlet Branch Name
    SWHSys1 Supply Equipment Branch,  !- Outlet Branch 1 Name
    SWHSys1 Supply Equipment Bypass Branch;  !- Outlet Branch 2 Name

  Connector:Mixer,
    SWHSys1 Supply Mixer,    !- Name
    SWHSys1 Supply Outlet Branch,  !- Outlet Branch Name
    SWHSys1 Supply Equipment Branch,  !- Inlet Branch 1 Name
    SWHSys1 Supply Equipment Bypass Branch;  !- Inlet Branch 2 Name

  ConnectorList,
    SWHSys1 Supply Connectors,  !- Name
    Connector:Splitter,      !- Connector 1 Object Type
    SWHSys1 Supply Splitter, !- Connector 1 Name
    Connector:Mixer,         !- Connector 2 Object Type
    SWHSys1 Supply Mixer;    !- Connector 2 Name

  ConnectorList,
    SWHSys1 Demand Connectors,  !- Name
    Connector:Splitter,      !- Connector 1 Object Type
    SWHSys1 Demand Splitter, !- Connector 1 Name
    Connector:Mixer,         !- Connector 2 Object Type
    SWHSys1 Demand Mixer;    !- Connector 2 Name
"""

    # WaterUse:Equipment list
    objs_filt_watereq=filter_IDF_objs_raw(new_objs, 'WaterUse:Equipment')
    nm_watereq=[get_obj_name(o) for o in objs_filt_watereq]

    # Two fns: 1) Added DemandBranch, 2) Built DemandBranch list
    demandbranchlst=[txt_demandbranchlst_st]
    demandsplt=[txt_demandsplt_st]
    demandmix=[txt_demandmix_st]
    printc("Adding DHW Plant!", "yellow")
    for ii,nm in enumerate(nm_watereq):
        printc("DHW Plant: Adding WaterUse:Equipment object: %s to DHW Plant"%(mkcolor(nm,'green')), "blue")
        demandbranchlst.append(temp_demandbranchlst_mi%(ii+1,ii+2))
        demandsplt.append( temp_demandspli_mi%(ii+1, ii+1))
        demandmix.append( temp_demandmix_mi%(ii+1, ii+1))
        new_objs.insert(-1, idf_templater(template_dict(defs_dmdbr, {"n": ii+1, "nm": nm}),
                                      branch_temp,
                                      branch_defs ) )
        new_objs.insert(-1, idf_templater(template_dict(defs_conn, {"nm": nm}),
                                      wateruse_temp,
                                      wateruse_defs ) )
        if ii+1==len(nm_watereq):
            demandbranchlst.append(temp_demandbranchlst_en%(ii+3, ii+4))
            demandsplt.append( temp_demandspli_en%(ii+2))
            demandmix.append( temp_demandmix_en%(ii+2))
    new_objs.insert(-1, "".join(demandbranchlst))
    new_objs.insert(-1, "".join(demandsplt))
    new_objs.insert(-1, "".join(demandmix))

    # Supply mixer and splitter (no magic needed)
    new_objs.insert(-1, "".join(txt_supplysplit_mix))

    new_objs.insert(-1, txt_supplybranchlst)
    [new_objs.insert(-1, idf_templater(dd, branch_temp, branch_defs ) ) for dd in allbrdefs]


    #new_objs = align_IDF_objs(new_objs)
    return new_objs

def add_DHWElecTank_file(to_file=to_file):
    """Modified version of `add_DHWElecTank` which creates an IDF output for testing purposes. File output uses suffix `_DHWElecTank.idf` by default."""
    return __abstract_add_objs2file(add_DHWElecTank, to_file=to_file, suffix='DHWElecTank')

def add_DHWElecTank(objs_all, args={}):
    """Add an Electric DHW Tank. Piggy-backs `add_DHWNGplant` function and Template and then modifies `WaterHeater` fuel source type from `NaturalGas` to `Electricity`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)

    Returns:

    * `new_objs`: genEPJ object list with newly added Electric DHW tank (Python `List`)
    """

    #if not any([True for obj in new_objs if ((get_obj_type(obj)=='WaterHeater:Mixed') and (get_obj_abstract(obj,11)=='NATURALGAS'))]):
    if not any([True for obj in objs_all if get_obj_type(obj)=='WaterHeater:Mixed']):
        # Add NG DHW plant as a basis of design
        printc("Adding basis of design for DHW Elec Tank",'yellow')
        new_objs=add_DHWNGplant(objs_all, args=args)
    elif any([True for obj in objs_all if ((get_obj_type(obj)=='WaterHeater:Mixed') and (get_obj_abstract(obj,11).upper()=='NATURALGAS'))]):
        printc("Found existing NG DHW. NOT adding basis of design for DHW Elec",'yellow')
        new_objs = list(objs_all) # Do nothing since DHW NG has already been added
    # SB Could be HP OR DHW. ASS-U-ME never going to be a HP in the reference design
    elif any([True for obj in objs_all if ((get_obj_type(obj)=='WaterHeater:Mixed') and (get_obj_abstract(obj,11).upper()=='ELECTRICITY'))]):
        printc("Existing DHW Elec Tank objects found. Do nothing!",'red')
        return objs_all # HP already exists, return objects
    else:
        raise ValueError("DHW Elec Plant Error: No valid option found to work from")

    # SB: Need to rebuild objects since many are cluster together
    new_objs=get_IDF_objs_raw(new_objs)

    # Modify WaterHeater:Mixed object
    wh_objs = [obj for obj in new_objs if get_obj_type(obj)=='WaterHeater:Mixed']
    wh_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='WaterHeater:Mixed']
    if len(wh_objs)>1 :
        printc("Several DHW Tank objects found. Do nothing!",'red')
        return objs_all # quit and return objects
    wh_obj = wh_objs[0]
    wh_idx = wh_idxs[0]
    #print( wh_obj )
    wh_obj = wh_obj.replace('NATURALGAS', 'Electricity')
    wh_obj = wh_obj.replace('0.8,', '1.0,', 1)
    #print( wh_obj )
    new_objs[wh_idx] = wh_obj

    return new_objs

def add_DHWHPplant_file(to_file=to_file):
    """Modified version of `add_DHWHPplant` which creates an IDF output for testing purposes. File output uses suffix `_DHWHPplant.idf` by default."""
    return __abstract_add_objs2file(add_DHWHPplant, to_file=to_file, suffix='DHWHPplant')

# SB Hack: Grabbing air from OA, not indoors (need to mess with EquipmentLists/NodeLists in each zone to do this)
def add_DHWHPplant(objs_all, args={}):
    """Add an Electric HeatPump DHW Tank. Piggy-backs `add_DHWNGplant` function and Template and then modifies `WaterHeater` fuel source type from `NaturalGas` to `Electricity` using a compression cycle with a default COP of 3.2.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)

    Returns:

    * `new_objs`: genEPJ object list with newly added Electric HeatPump DHW tank (Python `List`)
    """

    #if not any([True for obj in new_objs if ((get_obj_type(obj)=='WaterHeater:Mixed') and (get_obj_abstract(obj,11)=='NATURALGAS'))]):
    if not any([True for obj in objs_all if get_obj_type(obj)=='WaterHeater:Mixed']):
        # Add NG DHW plant as a basis of design
        printc("Adding basis of design for DHW HP",'yellow')
        new_objs=add_DHWNGplant(objs_all, args)
    elif any([True for obj in objs_all if ((get_obj_type(obj)=='WaterHeater:Mixed') and (get_obj_abstract(obj,11).upper()=='NATURALGAS'))]):
        printc("Found existing NG DHW. NOT adding basis of design for DHW HP",'yellow')
        new_objs = list(objs_all) # Do nothing since DHW NG has already been added
    elif any([True for obj in objs_all if ((get_obj_type(obj)=='WaterHeater:Mixed') and (get_obj_abstract(obj,11).upper()=='ELECTRICITY'))]):
        printc("Existing DHW HP objects found. Do nothing!",'red')
        return objs_all # HP already exists, return objects
    else:
        raise ValueError("DHW HP Plant Error: No valid option found to work from")

    # SB: Need to rebuild objects since many are cluster together
    new_objs=get_IDF_objs_raw(new_objs)

    # Remove existing WaterHeater:Mixed
    #obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='WaterHeater:Mixed']
    #new_objs[obj_idxs[0]]=""
    objs = [obj for obj in new_objs if get_obj_type(obj)=='WaterHeater:Mixed']
    new_objs.remove( objs[0] )

    # SB: July10: Names are staying the same...
    ##Remove SWHSys1 Supply Branches. Needs to be rebuilt with WaterHeater:HeatPump
    #objs = [obj for obj in new_objs if (get_obj_type(obj)=='BranchList') and ('swhsys1 supply branch' in get_obj_name(obj))]
    #new_objs.remove( objs[0] )

    # Remove existing PlantEquipmentList (needs to include HP equipment)
    objs = [obj for obj in new_objs if get_obj_type(obj)=='PlantEquipmentList']
    new_objs.remove( objs[0] )

    # Remove existing Equipment Branch (needs to include HP equipment)
    objs = [obj for obj in new_objs if ((get_obj_type(obj)=='Branch') and ('Supply Equipment Branch' in get_obj_name(obj)))]
    try:
        new_objs.remove( objs[0] )
    except:
        raise ValueError("Existing electric DHW implementation not found. Required for DHW_HP")

    ep_version=get_eplus_version(new_objs)
    #print(ep_version)
    ep_version_major=int(ep_version.split('.')[0])
    #print(ep_version_major)

    # Changes required:
    #  1. Swap out old WaterHeater:Mixed
    #  2. Add templates:
    #      *
    #      * HP coil curves


#    # SB TODO: Need to add HPWH to NodeList of the zone
#    # SB: This uses air from ZoneName to determine COPs (left blank since I need to add to ZoneEquipment list requiring ExpandObjects fn)

    #3.2,                     !- Rated COP {W/W}
    txt_WHHP="""

  PlantEquipmentList,
    SWHSys1 Equipment List,           !- Name
    WaterHeater:HeatPump,    !- Equipment 1 Object Type
    OutdoorHeatPumpWaterHeater;!- Equipment 1 Name

  OutdoorAir:Node,
    HPWHOutdoorTank OA Node; !- Name

  OutdoorAir:NodeList,
    OutsideAirInletNodes;    !- Node or NodeList Name 1

  NodeList,
    OutsideAirInletNodes,    !- Name
    HPOutdoorAirInletNode;   !- Node 2 Name

"""
    if ep_version_major>=9:
        txt_WHHP=txt_WHHP.replace('WaterHeater:HeatPump', 'WaterHeater:HeatPump:PumpedCondenser')

    # TODO: Refer to HP Branch
    txt_supplybranchlst="""
  BranchList,
    SWHSys1 Supply Branches, !- Name
    SWHSys1 Supply Inlet Branch,  !- Branch 1 Name
    SWHSys1 Supply Equipment Branch,  !- Branch 2 Name
    SWHSys1 Supply Equipment Bypass Branch,  !- Branch 3 Name
    SWHSys1 Supply Outlet Branch;  !- Branch 4 Name
"""

    # TODO: Add HP Branch
    txt_supplysplit_mix="""
  Connector:Splitter,
    SWHSys1 Supply Splitter, !- Name
    SWHSys1 Supply Inlet Branch,  !- Inlet Branch Name
    SWHSys1 Supply Equipment Branch,  !- Outlet Branch 1 Name
    SWHSys1 Supply Equipment Bypass Branch;  !- Outlet Branch 2 Name

  Connector:Mixer,
    SWHSys1 Supply Mixer,    !- Name
    SWHSys1 Supply Outlet Branch,  !- Outlet Branch Name
    SWHSys1 Supply Equipment Branch,  !- Inlet Branch 1 Name
    SWHSys1 Supply Equipment Bypass Branch;  !- Inlet Branch 2 Name
"""

    new_objs.insert(-1, txt_WHHP)

    # Updated schedules
    sche_temp, sche_defs = templ.HVACtemplate_schedule_alwaysON()
    d={'name': "PlantHPWHSch",
       'type': "Any Number",
       'frac': "1.0", }
    new_objs.insert(-1, idf_templater(d, sche_temp, sche_defs ) )
    d={'name': "HPWHTempSch",
       'type': "Any Number",
       'frac': "60.0", }
    new_objs.insert(-1, idf_templater(d, sche_temp, sche_defs ) )

    hpwater_temp, hpwater_defs = templ.HVAC_HeatPumpWaterHeater()
    #d={'tank_type': 'WaterHeater:Mixed'}
    d={'tank_type': 'WaterHeater:Stratified'}
    new_objs.insert(-1, idf_templater(d, hpwater_temp, hpwater_defs ) )

    branch_temp, branch_defs = templ.Branch()
    defs_supbr={
        'name':        'SWHSys1 Supply Equipment Branch',
        #'type':        'WaterHeater:HeatPump',
        'type':        'WaterHeater:HeatPump',
        'comp_nm':     'OutdoorHeatPumpWaterHeater',
        'inlet_node':  'SWHSys1 Pump-SWHSys1 Water HeaterNode',
        'outlet_node': 'SWHSys1 Supply Equipment Outlet Node',
        'contrl_type': 'Passive', }

    # SB- see templates_v9 to see changes to templ.HVAC_HeatPumpWaterHeater
    if ep_version_major>=9:
        defs_supbr['type']='WaterHeater:HeatPump:PumpedCondenser'

    # TODO: Zone where the HPWH is placed (ambient gains/AC effect)


    #tank_temp, tank_defs = templ.DHW_WaterHeaterMixed()
    tank_temp, tank_defs = templ.DHW_WaterHeaterStratified()
    d={'volume': "0.3785", # m3
       'sch_nm': "SWHSys1 Water Heater Setpoint Temperature Schedule Name",
       'fuel': "ELECTRICITY",
       'eff': "0.98",
       'temp_sche': "",
       'skin_coeff': "0.200", }
    for k in args.keys():
        d[k]=args[k]
    new_objs.insert(-1, idf_templater(d, tank_temp, tank_defs ) )

    new_objs.insert(-1, idf_templater(defs_supbr, branch_temp, branch_defs ) )

    return new_objs

def remove_types_from_JSON_file(to_file=to_file):
    """Modified version of `remove_types_from_JSON` which creates an IDF output for testing purposes. File output uses suffix `_rmJSON.idf` by default."""
    return __abstract_add_objs2file(remove_types_from_JSON, to_file=to_file, suffix='rmJSON')

def remove_types_from_JSON(objs_all, args={'rm_keys':[]}):
    """Iterate over provide keys and remove from the provided epJSON dictionary"""
    # Dict comprehension loses order
    #return {k:v for k,v in objs_all.items() if not is_in(rm_keys, k) } # Dict comprehension: is_in matches partial strings. Eg 'Coil' in 'Coil:Heating'

    # convert to JSON if wrong file type
    # Allows for testing using IDF format via script genEPJ/standalone/run_genEPJ_functions.sh
    if isinstance(objs_all, list) :
        objs_all=swap_IDFJSON(objs_all)

    if 'rm_keys' in args:
        rm_keys=args['rm_keys']
    else:
        printc("'rm_keys' not supplied in args. Nothing to do!", 'yellow')

    new_objs = OrderedDict()
    for k,v in objs_all.items():
        if not is_in(rm_keys, k):
            new_objs[k]=v
    return new_objs


def rm_all_HVAC_file(to_file=to_file):
    """Modified version of `rm_all_HVAC` which creates an IDF output for testing purposes. File output uses suffix `_rmAllHVAC.idf` by default."""
    return __abstract_add_objs2file(rm_all_HVAC, to_file=to_file, suffix='rmAllHVAC')

# SB: Overrides previous 'genEPJ_pkg/pylib/genEPJ_lib.py' implementation. IDF version name changed to 'rm_all_HVAC_IDF'. Now used with Modelkit exclusively
def rm_all_HVAC(objs_all, args={}):
    """Remove all HVAC objects in provided genEPJ object list.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with HVAC objects removed (Python `List`)
    """

    # convert to JSON if wrong file type
    if isinstance(objs_all, list) :
        objs_all=swap_IDFJSON(objs_all)

    if 'rm_hvac_list' in args:
        rm_hvac_list=args['rm_hvac_list']
    else: # no rules provided, use defaults
        # Glob searches to grab HVAC objects
        # NOTE: to see what *NAME* matches:
        # 1. open template epJSON: d=json.load( open('templateGenerator_epJSON/templates_9.0.1.json', 'r'))
        # 2. in ipython: redirect keys to text file: %store d.keys() > /tmp/1.csv
        # 3. in vim, :s/',/',\r/g
        # 4. in vim, find items of interest, :v/district/d OR :v/hvac/d
        # 5. redirect changes to list
        rm_hvac_list=[
                   ##### Glob specification of objects to be removed ####
                   'HVAC',
                   'Coil', #Warning: grabs 'AirflowNetwork:Distribution:Component:Coil'
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
                   'DesignSpecification:OutdoorAir', # SB: Vent sizing for OA (DSOA/ZoneHVAC obj). Removal needed to get VAVTemplate to run Mon Jan 21 09:06:56 EST 2019
                   'Controller:OutdoorAir', # SB: OA controller (ZoneHVAC obj). Removal needed to get VAVTemplate to run Mon Jan 21 09:06:56 EST 2019
                   #'Sizing:Zone', # Zone air specs for each zone (refer to DSOA obj)
                   'Sizing:System', # Referred to by ZoneHVAC
                   'ThermostatSetpoint:DualSetpoint',
                   'ZoneControl:Thermostat',
                   'AirConditioner:VariableRefrigerantFlow',
                   'Curve:Biquadratic', # TEST: Used for VRF coil/unit properties
                   'Curve:Cubic', # TEST: Used for VRF coil/unit properties
                   'Curve:Quadratic', # TEST: Used for VRF coil/unit properties
                   'CURVE:QUADRATIC', # TEST: Used for VRF coil/unit properties
                   'Curve:Linear', # TEST: Used for VRF coil/unit properties
                   'Branch',
                  ]

    # Need to incrementally apply changes to the dictionary
    new_objs=remove_types_from_JSON(objs_all, {'rm_keys': rm_hvac_list})
    return new_objs

def dispatch_JSON_file(to_file=to_file):
    """Modified version of `dispatch_JSON` which creates an JSON output for testing purposes. File output uses suffix `_dispatchJSON.json` by default."""
    return __abstract_add_objs2file(dispatch_JSON, to_file=to_file, suffix='dispatchJSON')

# SB NOTE: Move to templater.py?
def dispatch_JSON(objs_all, args={} ):
    """Add objects to epJSON file by iterating over a provided dict of JSON templates and epJSON keys"""

    new_objs= objs_all
    #global json_temp
    #json_temp = load_json_template( epJSON_template )

    if 'payload' in list(args.keys()):
        payload=args['payload']
        if isfile( str( payload ) ):
            payload=get_JSON_objs_raw( payload, ordered=1 ) # custom JSON directives fname
        elif isinstance(payload, dict):
            # do nothing, payload in appropriate format already
            pass # TODO- TEST to ensure data meets specification
        else:
            printc("DispatchJSON: Payload in inappropriate format: '%s' (not file.json/dict). Do nothing"%( mkcolor(type(payload),'yellow')  ), 'red')
            payload={}
    else: # no payload provided
        printc("DispatchJSON: Payload not provided. Do nothing", 'red')
        payload={}

    # for testing in ipython
    #_take_first_key=lambda mydict : list(mydict.keys())[0]
    def _take_first_key(mydict): # TODO- Add try statement
        return list(mydict.keys())[0]
    def _take_first_value(mydict): # TODO- Add try statement
        return list(mydict.value())[0]

    def _get_defaults(mydata):
        if isfile( str(mydata) ):
            _json=get_JSON_objs_raw( mydata ) # custom JSON template fname (without merger to template)
            _key=_take_first_key(_json)
            _defaults=_json[_key]['defaults']
        elif isinstance(mydata, dict):
            _defaults=mydata
        else:
            printc("> 'get_dict': Inappropriate format provided for '%s'. Expected JSON fname OR dict"%(mkcolor(mydata,'yellow')), "red")
            raise ValueError()
        return _key,_defaults




    # Iterate over each instruction in the file and execute 'add/merge/etc' directives with appropriate payloads
    #for directive,paylds in payload:
    for directive,paylds in payload.items():

         #SB: Overwrites object if pre-existing
         if directive=='add' or directive=='append':
            for payld in paylds:
                printc("Processing directive '%s' with payload '%s'"%(directive, str(payld)), 'blue')
                if isfile( str(payld) ):  # JSON File
                    json_fname=payld
                    raw_json=get_JSON_objs_raw(json_fname) # custom JSON template fname (without merger to template)
                    ep_key=_take_first_key(raw_json)
                    old_templ,old_defal,old_requ=get_template_defaults_required( ep_key )
                    # open JSON and apply template rules
                    new_templ,new_defal,new_requ=get_template_defaults_required( json_fname )
                    # If defaults in JSON provided, but no template: use existing template with new defaults
                    if not new_templ and new_defal:
                        new_template=templater( {}, old_templ, new_defal )
                        #print("IF 1: newDEFAULTS, oldTemplate: ",new_template)
                    # If defaults in JSON provided with new template but no defaults: use new template with old defaults
                    elif new_templ and not new_defal:
                        new_template=templater( {}, new_templ, new_defal )
                    else:
                        new_template=templater( {}, new_templ, new_defal )
                    # Finally add object to new_objs
                    if directive=='add' and ep_key in epJSON_keys:
                        new_objs[ep_key] = new_template
                    elif directive=='add' and ep_key not in epJSON_keys: # Not a real E+ key, add data to root structure
                        new_objs.update(new_template)
                    elif directive=='append':
                        new_objs[ep_key].update(new_template)

        # HACK SB: REFACTOR. Hardcoded objs_all['HVACTemplate:Thermostat']['name'] makes no sense below
         elif directive=='for_iter':

            for payld in paylds:
                # if isfile, load JSON
                if isfile( str(payld) ):
                    json_fname=payld
                    iter_dict=get_JSON_objs_raw(json_fname) # custom JSON template fname (without merger to template)
                elif isinstance(payld, dict):
                    iter_dict=payld
                else:
                    printc("'iter_dict': Inappropriate format provided: '%s'."%(mkcolor(zn,'red'), mkcolor(type(payld),'red')), "yellow")

                # ASSUME JSON and dict have identical formats

                ep_key=iter_dict['obj']
                omit_zones=iter_dict['iter_exclude']
                iter_over=iter_dict['iter_over']
                _get_zone_names=lambda x: list(x.keys())
                templ,defal,requ=get_template_defaults_required( ep_key )
                #zone_nms=[_nm for _nm in _get_zone_names( objs_all[iter_over] ) if _nm.lower() not in omit_zones]
                if iter_dict['defaults']:
                    def_key,defaults=_get_defaults( iter_dict['defaults'] )
                else:
                    defaults={}
                zone_nms=[_nm for _nm in _get_zone_names( objs_all[iter_over] ) if not is_in2(omit_zones, _nm.lower())]
                zones_template={}
                for zn in zone_nms:
                        d={
                            'name': "%s %s"%(ep_key.split(':')[-1],zn),
                            'zone_name': zn,
                            'template_thermostat_name': objs_all['HVACTemplate:Thermostat']['name'],
                          }
                        defaults.update(d)
                        new_template=templater( defaults, templ, defal )
                        new_objs[ep_key] = new_template
                        printc("Adding Ideal HVAC to Zone: %s"%(mkcolor(zn,'green')), "blue")
                        zones_template[d['name']]= new_template
                # Finally add object to new_objs
                print(zones_template)
                new_objs[ep_key] = zones_template

         elif directive=='append_schedules': # edge case for Schedule:Compact/Schedule:Annual

            for payld in paylds:
                printc("Processing directive '%s' with payload '%s'"%(directive, str(payld)), 'blue')
                #print("TEST", payld)
                if isfile( payld ):  # JSON File
                    json_fname=payld
                    raw_json=get_JSON_objs_raw(json_fname) # custom JSON template fname (without merger to template)
                    ep_key=_take_first_key(raw_json)
                    # open JSON and apply template rules
                    new_templ,new_defal,new_requ=get_template_defaults_required( json_fname )
                    # If defaults AND template in JSON provided, use both
                    if new_templ and new_defal:
                        new_template=templater( {}, new_templ, new_defal, new_requ )
                    elif new_templ and not new_defal:
                        new_template=templater( {}, new_templ, {}, new_requ )
                    else:
                        printc("append_schedules: New defaults/templates not specified in '%s'"%(json_fname), 'red')
                        new_template={}
                    # Finally splice object into 'data: []' in new_objs
                    obj_nm=_take_first_key(new_template)
                    new_objs[ep_key][obj_nm] = new_template[obj_nm]
                else:
                    printc("Requested directive '%s' doesn't support payload: '%s'"%(directive, str(payload)), "red")

         # SB REFACTOR/HACK: This directive will live in it's own directory. ie. can be used independently of genEPJ
         elif directive=='add_EPSchematic': # BIG MESSY HVAC implementation

            # New name for EPSchematic directives
            #epsch_json=paylds

            # get sub-directive: AirLoop, WaterLoop, ZoneHVAC, etc
            #sub_directive=list(paylds.keys())[0]
            #_dir_data=epsch_json[sub_directive]
            #print(paylds.keys())
            _dir_data=paylds

            ## Load src file for EPSchematic directives
            #epsch_fn=paylds['src']
            #epsch_json=get_JSON_objs_raw(epsch_fn) # custom JSON template fname (without merger to template)
            #print(epsch_json)
            #print(epsch_json.keys())

            # Get NAMES that will be iterated over. Test for redundant information (halt processing if necessary)
            _templates={}
            if 'iter_obj' in _dir_data.keys():
                if 'iter_sql' in _dir_data.keys(): # Throw error if found redundant instructions
                    raise ValueError("EPSchematic: redundant iterate instructions found! Must be unique instruction in set: ['iter_obj', 'iter_sql']")
                elif False: # Test if key exists in E+.json template set
                    pass

                printc("Found 'iter_obj' key for iteration: %s"%(_dir_data['iter_obj']) , 'green')
                iter_over=_dir_data['iter_obj']['ep_key']
                # SB TODO: refactor into a common function with "elif directive=='for_iter'" above
                _get_zone_names=lambda x: list(x.keys())
                iter_nms=[_nm for _nm in _get_zone_names( objs_all[iter_over] )]
                print(iter_nms)
                _templates=_dir_data['iter_obj']['templates']
            elif 'iter_sql' in _dir_data.keys():
                if 'iter_obj' in _dir_data.keys(): # Throw error if found redundant instructions
                    raise ValueError("EPSchematic: redundant iterate instructions found! Must be unique instruction in set: ['iter_obj', 'iter_sql']")

                printc("Found 'iter_sql' key for iteration: %s"%(_dir_data['iter_sql']) , 'green')

                # setting up SQL for selections
                global c
                to_file=args['to_file']
                c = get_sql_database(to_file)
                sql_sel = _dir_data['iter_sql']['sql_select']
                printc("EPSchematic 'iter_sql':  Using SQL select statement '%s' to iterate over objects"%(sql_sel), 'yellow')
                _iter_nms=c.execute(sql_sel).fetchall()
                iter_nms=list( map(lambda x: x[0], _iter_nms) )

                print(iter_nms)
                _templates=_dir_data['iter_sql']['templates']
            else:
                printc("EPSchematic: key for iteration: NOT SUPPORTED (%s)"%(list( _dir_data.keys() )) , 'yellow')

            #--------------------------
            # **Development Strategy:**
            #--------------------------
            # * Isolate the required information (Nodes for BranchList, EPObjects for EquipmentLists, etc)
            # * template and add using specialized functions
            # * reuse code where possible
            # * REFACTOR after fully implemented

            # Take subset of directives processed above and run those first

            #templ,defal,requ=get_template_defaults_required( ep_key )
            #new_templ,new_defal,new_requ=get_template_defaults_required( json_fname )
            #new_template=templater( values, template, defaults )
            def _process_templ_defaul_require(prov_JSON_fname):
                print("Processing JSON: %s"%(prov_JSON_fname))
                raw_json=get_JSON_objs_raw(prov_JSON_fname) # custom JSON template fname (without merger to template)
                ep_key=_take_first_key(raw_json)
                prov_templ,prov_defal,prov_requ=get_template_defaults_required( prov_JSON_fname )
                templ,defal,requ=get_template_defaults_required( ep_key )

                # If defaults in JSON provided, but no template: use existing template with new defaults
                def _choose_data(templ,prov):
                    if not prov: new= templ
                    else: new= prov
                    return new

                    #print("IF 1: newDEFAULTS, oldTemplate: ",new_template)
                # If defaults in JSON provided with new template but no defaults: use new template with old defaults
                new_templ = _choose_data(templ, prov_templ)
                new_defal = _choose_data(defal, prov_defal)
                #return new_templ, new_defal, requ
                return new_templ, new_defal

            # Load in defaults using E+ object key
            #epsch_defs_json=paylds['defaults']
            #epsch_defs_json=paylds['templates']
            if _templates:
                epsch_defs_json=_templates
            elif paylds['templates']:
                epsch_defs_json=paylds['templates']
            elif _templates and paylds['templates']:
                epsch_defs_json=_templates
                epsch_defs_json.update( paylds['templates'] )
            print(epsch_defs_json)
            #epsch_defs = list( map( lambda x: _process_templ_defaul_require(x), epsch_defs_json) )
            epschem_data = list( map( _process_templ_defaul_require, epsch_defs_json) )
            #print(epschem_data)



#Mon Jan 28 09:35:54 EST 2019
# * remove 'defs' from _format_data. Make generic
# * iterate over templ, defal, requ (NOT just defs)
# ** sub each in if matching {}

            # Subs ANY provided key into JSON/defaults.json. Normally used for 'ZoneName'
            def _format_data(data_dict, mydict):
                data_templ= Template(json.dumps(data_dict))
                data_new= idf_templater({}, data_templ, mydict, IGNORE_ERRORS=True)
                return json.loads( data_new, object_pairs_hook=OrderedDict )

            # Iteration allowed only on specified directives: AirLoop:DemandSide, ZoneHVAC, ... (iterate over Zone, etc)
            #allowed2iter=[ ':DemandSide', 'ZoneHVAC']
            #if is_in(allowed2iter, sub_directive):

            _sub_text=[]
            for _i,_nm in enumerate(iter_nms):
                print("   >ITER: %s"%(_nm) )

                # Subbing iterables: ${ZoneName}, ${N}, etc
                new_epschem_data= epschem_data
                #print(epschem_data)
                for ii,data in enumerate(epschem_data):

                    def _get_iter_value(_dict):
                        for k,v in _dict.items():
                            for _k,_v in v.items():
                                if 'ITERATEOVER' in _k:
                                    return _dict[k][_k][0]
                    def _get_iter_key(_dict):
                        for k,v in _dict.items():
                            for _k,_v in v.items():
                                if 'ITERATEOVER' in _k: return _k
                    # Two Paths:
                    # 1. Iterate over the entire template (default) OR Iterate over internals of the template ('ITERATEOVER' in template)
                    if 'ITERATEOVER' in json.dumps( data ): # Iterate over internals of the template, add on final iteration
                        printc("Iterating within object", 'yellow')

                        # Get text block we'll be iterating over
                        iter_dict= _get_iter_value(data[0])
                        printc("IterDict: %s"%(iter_dict), 'green')

                        # Build sub-text
                        _data=_format_data( iter_dict, {"ZoneName": _nm, "N": _i+1})
                        _sub_text.append( _data )

                        if _nm==iter_nms[-1] : # If last entry, append model to new_objs
                            printc("LAST Iteration. Adding object", 'red')
                            _sub_key=_get_iter_key(data[0])
                            print( _sub_text )
                            print( _sub_key )

                            # Make the sub
                            _raw_json=get_JSON_objs_raw(epsch_defs_json[ii]) # custom JSON template fname (without merger to template)
                            ep_key=_take_first_key(_raw_json)

                            if ep_key not in new_objs.keys():
                                new_objs[ep_key]={}

                            # Add whole object. We'll make manual overwrite below
                            new_data=_format_data( data, {"ZoneName": _nm, "N": _i+1})
                            #print(new_data)
                            _templ,_defal=new_data
                            templ_key=_take_first_key(_templ)
                            new_objs[ep_key][templ_key] = templater({}, _templ, _defal, IGNORE_ERRORS=True)[templ_key]

                            # Override
                            new_objs[ep_key][templ_key][_sub_key]= _sub_text

                            # :s/ITERATEOVER//g
                            _text= json.dumps( new_objs[ep_key][templ_key] )
                            _text=_text.replace('ITERATEOVER', '')
                            new_objs[ep_key][templ_key]= json.loads(_text)

                            ## Finally splice object into 'data: []' in new_objs
                            #obj_nm=_take_first_key(new_template)
                            #new_objs[ep_key][obj_nm] = new_template[obj_nm]

                    else: # Default: Iterate over the entire template
                        #print(data)
                        new_data=_format_data( data, {"ZoneName": _nm, "N": _i+1})
                        #print(new_data)
                        _templ,_defal=new_data

                        _raw_json=get_JSON_objs_raw(epsch_defs_json[ii]) # custom JSON template fname (without merger to template)
                        ep_key=_take_first_key(_raw_json)
                        templ_key=_take_first_key(_templ)
                        if ep_key not in new_objs.keys():
                            new_objs[ep_key]={}
                        new_objs[ep_key][templ_key] = templater({}, _templ, _defal, IGNORE_ERRORS=True)[templ_key]

                # Sub into JSON
                # Finally splice object into 'data: []' in new_objs
                #obj_nm=_take_first_key(new_template)
                #new_objs[ep_key][obj_nm] = new_template[obj_nm]


# FORMAT:
#    "ZoneHVAC:EquipmentList": {
#        "Main Floor Equipment": {
#            "equipment": [
#                {

                        # "EquipmentConnections", "ZoneControl", "ZoneHVAC:IdealLoadsAirSystem"
                        # "ZoneHVAC:" # VERY important that this is checked last. Otherwise, you'll query ZoneHVAC:EquipmentList and ZoneHVAC:EquipmentConnections (DONT WANY)
                        # TESTING: Get all ZoneHVAC:* objects
                        # json_temp = load_json_template( epJSON_template )
                        # all_keys=list(json_temp.keys())
                        # [_k for _k in all_keys if 'ZoneHVAC:' in _k]

                    # ZoneHVAC:IdealLoadsAirSystem

                    # ZoneHVAC:EquipmentList

                    # ZoneControl:Thermostat

                #templ,defal,requ=get_template_defaults_required( ep_key )
                ##zone_nms=[_nm for _nm in _get_zone_names( objs_all[iter_over] ) if _nm.lower() not in omit_zones]
                #if iter_dict['defaults']:
                #    defaults=_get_defaults( iter_dict['defaults'] )
                #else:
                #    defaults={}
                # SB TODO: refactor into a common function with "elif directive=='for_iter'" above
                #_get_zone_names=lambda x: list(x.keys())
                #templ,defal,requ=get_template_defaults_required( ep_key )
                ##zone_nms=[_nm for _nm in _get_zone_names( objs_all[iter_over] ) if _nm.lower() not in omit_zones]
                #if iter_dict['defaults']:
                #    defaults=_get_defaults( iter_dict['defaults'] )
                #else:
                #    defaults={}

                #iter_nms=[_nm for _nm in _get_zone_names( objs_all[iter_over] )]



            # ITERATE over NAMES, add template (with defaults), OVERIDE key info based on directive types (eg. AirLoop vs ZoneHVAC)
            # src/defaults/zone_exclude

            # AirLoop:SupplySide
            # AirLoop:DemandSide
            # ** CAN iterate over zones
            # WaterLoop:SupplySide
            # WaterLoop:DemandSide
            # ** CAN iterate over zones
            # EvaporatorWaterLoop:SupplySide
            # EvaporatorWaterLoop:DemandSide
            # CondensorWaterLoop:SupplySide
            # CondensorWaterLoop:DemandSide
            # PlantLoop:SupplySide
            # PlantLoop:DemandSide
            # ZoneHVAC
            # ** CAN iterate over zones


            #for payld in paylds:
            #    printc("Processing directive '%s' with payload '%s'"%(directive, str(payld)), 'blue')

         else:
             printc("Requested directive '%s' NOT SUPPORTED in present version"%(directive), "red")

    return new_objs

def dispatch_HVAC_file(to_file=to_file):
    """Modified version of `dispatch_HVAC` which creates an IDF output for testing purposes. File output uses suffix `_dispatchHVAC.idf` by default."""
    return __abstract_add_objs2file(dispatch_HVAC, to_file=to_file, suffix='dispatchHVAC')

def dispatch_HVAC(objs_all, args={ 'add_HVAC_fn': lambda x,y: x, 'use_DOAS': None, 'use_district': False } ):
    """Coordinate addition of a mechanical and ventilation system at the same time.

    Allows a user to specify external district system with a set loop temperature while using a variety of ventilation/conditioning strategies.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `add_HVAC_fn` genEPJ function to add a mechanical system. `use_DOAS` Flag to specify a dedicated outdoor air system. `use_district` Flag to specify all mechanical systems will be served by a central loop.

    Returns:

    * `new_objs`: genEPJ object list with added HVAC, ventilation and district systems (Python `List`)
    """

    # SB: Need to rebuild objects since many are cluster together
    #new_objs=list(objs_all)
    new_objs=get_IDF_objs_raw(objs_all)

    add_HVAC_fn  = args['add_HVAC_fn']
    use_DOAS     = args['use_DOAS']
    use_district = args['use_district']

    printc("\nRemoving HVAC objects!", 'blue')
    print("Count new_objs [Orig]: ", len(new_objs))
    # Keep Sizing:Parameters (rm_all_HVAC removes this...)
    new_objs= [obj for obj in new_objs if 'hvactemplate' not in get_obj_type(obj).lower()]
    new_objs= [obj for obj in new_objs if 'hvactemplate' not in get_obj_type(obj).lower()]
    new_objs= [obj for obj in new_objs if 'sizing:zone'  not in get_obj_type(obj).lower()]
    new_objs= [obj for obj in new_objs if 'zonecontrol:thermostat' not in get_obj_type(obj).lower()]
    print("Count new_objs [No HVACtemp]: ", len(new_objs))
    ## Remove pesky heating/cooling setpoint objects
    #new_objs1= [obj for obj in new_objs if (('schedule:compact' != get_obj_type(obj).lower()) and ('temperature,' not in obj))]
    ## Symmetric difference of the two sets
    #print( "\n".join(set(new_objs) ^ set(new_objs1)) )
    # NAND: not (x:schedule:compact and y:setp-sch)
    #        y
    #      F  T
    # x  F 1  1
    #    F 1  0
    #new_objs= [obj for obj in new_objs if (('schedule:compact' != get_obj_type(obj).lower()) and ('temperature,' not in obj))]
    #new_objs= [obj for obj in new_objs if (('schedule:compact' != get_obj_type(obj).lower()) and ('Temperature,' not in obj))]
    new_objs= [obj for obj in new_objs if not (('schedule:compact' in obj.lower()) and ('setp-sch' in obj.lower()))]
    new_objs= [obj for obj in new_objs if not (('schedule:compact' in obj.lower()) and ('doas' in obj.lower()))]
    new_objs= [obj for obj in new_objs if not (('schedule:constant' in obj.lower()) and ('ptac' in obj.lower()))]
    #new_objs= [obj for obj in new_objs if not (('schedule:compact' in obj.lower()) and ('ventschedcont' in obj.lower()))]
    new_objs= [obj for obj in new_objs if not (('schedule:compact' in get_obj_type(obj).lower()) and
                                               ('fanavailsched' in get_obj_name(obj).lower())) ]
    new_objs= [obj for obj in new_objs if not (('schedule:compact' in get_obj_type(obj).lower()) and
                                               ('min oa sched' in get_obj_name(obj).lower())) ]
    print("Count new_objs [No Schedules]: ", len(new_objs))
    #new_objs=rm_all_HVAC(objs_all)

    if use_DOAS:
        new_objs = add_HVAC_DOAS(new_objs, args={ 'need_boiler': False, 'need_chiller': False, 'use_coils': False, 'to_file': args['to_file'] } )
    else:
        pass
        ### NO DOAS. Need to add extra ventilation
        ### Assume kitchen fans are already implemented (need to remove them and readd)
        ###  Need to remove existing schedule: 'VentSchedCont'
        #iii=len(new_objs)
        #new_objs= [obj for obj in new_objs if 'zoneventilation:designflowrate'  not in get_obj_type(obj).lower()]
        #iii2=len(new_objs)
        #print("DISPATCH: REMOVED %d ZoneVent objects. No DOAS"%(iii2))
        #new_objs= [obj for obj in new_objs if not (('schedule:compact' in obj.lower()) and ('ventschedcont' in obj.lower()))]
        #new_objs = add_vent_loads(new_objs, bath=2, kitch=1)
        ##new_objs = add_vent_loads(new_objs, bath=0, kitch=1)
        ##pass

    new_objs = add_HVAC_fn(new_objs, args)
    #if use_district:
    #    new_objs = add_HVAC_fn(new_objs, use_DOAS=use_DOAS, use_district=use_district)
    #else:
    #    new_objs = add_HVAC_fn(new_objs, use_DOAS=use_DOAS)

    return new_objs

def mod_radfloor_flow_rates_file(to_file=to_file):
    """Modified version of `mod_radfloor_flow_rates` which creates an IDF output for testing purposes. File output uses suffix `_modRadFloor.idf` by default."""
    return __abstract_add_objs2file(mod_radfloor_flow_rates, to_file=to_file, suffix='modRadFloor')

# Added for CANSOFCOM project
def mod_radfloor_flow_rates(objs_all, args={}):
    """Modify radiant floor rates via E+ `ZoneHVAC:LowTemperatureRadiant:ConstantFlow` for each `Zone` based on floor area.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with modified flow in `ZoneHVAC:LowTemperatureRadiant:ConstantFlow` objects (Python `List`)
    """

    # ZoneHVAC:LowTemperatureRadiant:ConstantFlow
    # rated_flow_rate

    new_objs=list( objs_all )

    radfloor_objs = [obj for obj in new_objs if get_obj_type(obj)=='ZoneHVAC:LowTemperatureRadiant:ConstantFlow' ]

    for i,obj in enumerate(objs_all):

        if get_obj_type(obj)=='ZoneHVAC:LowTemperatureRadiant:ConstantFlow':
            old_line=get_obj_abstract(obj, 8)
            zone_nm=get_obj_abstract(obj, 3)
            zone_area=_calc_area_zone(zone_nm)
            printc("Modding 'ZoneHVAC:LowTemperatureRadiant:ConstantFlow', ZoneName: '{}', Area '{}'m2".format(zone_nm, zone_area), 'yellow')
            printc(old_line)
            # Changing values
            old_vl = float( trim_comments(old_line).strip(',') )
            # From Modelkit doas-radiant.imf
            # radiant_flow_rate = radiant_flow_sizing * zone_area / 1000000.0
            radiant_flow_sizing=0.6 #  Rated flow rate sizing factor (m3/s per 1000000 m2); default from Modelkit
            #rated_flow=radiant_flow_sizing*zone_area/1e6 # Results in 209 EUI
            #rated_flow=radiant_flow_sizing*zone_area/1e7 # Results in 105 EUI
            rated_flow=radiant_flow_sizing*zone_area/5e6 # Results in 119 EUI
            #new_line=" {:.2e},  !- Rated Flow Rate {{m3/s}}".format(rated_flow)
            new_line=" Autosize,  !- Rated Flow Rate {{m3/s}}"
            printc("Modifying Radiant Flow Rates: '%s' to '%s'"%(mkcolor("%.2e"%(old_vl),'red'), mkcolor("%.2e"%(rated_flow), 'yellow')), 'blue')
            new_objs[i]= obj.replace(old_line, new_line)

    return new_objs


def add_exteriorlights_file(to_file=to_file):
    """Modified version of `add_exteriorlights` which creates an IDF output for testing purposes. File output uses suffix `_extlights.idf` by default."""
    return __abstract_add_objs2file(add_exteriorlights, to_file=to_file, suffix='extlights')

# TODO- Write a more sophisticated way to determine exterior lighting requirements. Maybe use gross building surface area instead of footprint area OR linear perimeter along the ground floor?
def add_exteriorlights(objs_all, args={} ):
    """Add E+ `Exterior:Lights` to Building. If peak light power isn't supplied, estimate it using building area (determined using SQL query).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `ext_light_power` user specified light power (Watts)

    Returns:

    * `new_objs`: genEPJ object list with `Exterior:Lights` (Python `List`)
    """

    new_objs=list(objs_all)

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    #=========================
    # Template Exterior Lights
    #=========================
    li_name="EXTLIGHT_ALWAYS_ON"
    extavail_temp, extavail_defs = templ.HVACtemplate_schedule_alwaysON()

    # VD: If an exterior light power (W) is given, use it, otherwise use the area method
    if 'ext_light_power' in args:
        pk_light = args['ext_light_power']
    else:
        sql_area="SELECT Value FROM TabularDataWithStrings WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND RowName='Total Building Area';"
        bldg_area=float(c.execute(sql_area).fetchone()[0])
        print("Total building area: %.2f"%(bldg_area))

    #    # UserDefinedRoomAirPatterns.idf:
    #    9 floor
    #    296.985, W
    #    2,000 m2
    #    .14849250 W/m2/floor
    #    1.3364325 W/m2
    #
    #
    #    RetailPackagedTESCoil.idf
    #    1 floor
    #    8266, W
    #    2,294 m2
    #    3.60331299 W/m2
    #
    #    RefBldgMediumOfficeNew2004_Chicago.idf
    #    3 floor
    #    14804, W
    #    4,982 m2
    #    2.971497 W/m2
    #
    #    RefBldgMidriseApartmentNew2004_Chicago.idf
    #    4 floor
    #    5357, W
    #    3,135 m2
    #    1.7087719 W/m2

        #ext_lpd = 1.7087719
        #ext_lpd = 1.1, Too large, roughly 18% of total lighting
        ext_lpd = 0.6
        pk_light = bldg_area * ext_lpd


    #=========================
    # Template Exterior:Lights
    #=========================
    printc("Adding Exterior:Lights object with output of: %.1f W"%(pk_light), 'blue')
    extlights_temp, extlights_defs = templ.Equipment_ExteriorLighting()
    new_objs.insert(-1, idf_templater({'power': "%.1f"%(pk_light)}, extlights_temp, extlights_defs ) )
    new_objs.insert(-1, idf_templater({'name': li_name}, extavail_temp, extavail_defs ) )

    return new_objs

# SB: Should be executed in prep_model
def add_parkinglights_file(to_file=to_file):
    """Modified version of `add_parkinglights` which creates an IDF output for testing purposes. File output uses suffix `_parkinglights.idf` by default."""
    return __abstract_add_objs2file(add_parkinglights, to_file=to_file, suffix='parkinglights')

def add_parkinglights(objs_all, args={} ):
    """Add parking garage lights to model. Peak lighting output is estimated by the total garage area (and available parking spots).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with added Parking Garage Lights (Python `List`)
    """

    new_objs=list(objs_all)

    li_name="Parking Garage Lights"
    lische_name="PARKLIGHT_ALWAYS_ON"

    ## SB TODO: Figure this out by number of parkign spaces?
    #sql_area="SELECT Value FROM TabularDataWithStrings WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND RowName='Total Building Area';"
    #bldg_area=float(c.execute(sql_area).fetchone()[0])
    #print("Total building area: %.2f"%(bldg_area))

    #ext_lpd = 0.6
    #pk_light = bldg_area * ext_lpd

    # Number of Cars/Parking spaces
    cars_per_unit=1.15 ## EEI number, see 10 Lisa
    objs_zonlist=filter_IDF_objs_raw(objs_all, 'ZoneList')
    zone_guestrm=extract_nms_from_zonelist(objs_zonlist, ' apartment')
    units= len(zone_guestrm)
    cars = cars_per_unit * units
    printc("Adding Parking:Lights: Identified: %.1f Residential Units"%(units), 'blue')
    printc("Adding Parking:Lights: Estimating: %.1f Cars or %.2f Car/unit"%(cars, cars_per_unit), 'blue')

    # Lighting power:
    light_power_per_car = 16.0 # W/car; one 32 T8 per two car
    pk_light = light_power_per_car * cars # W

    #================================================================================
    #printc("Adding Parking:Lights object with output of: %.1f W"%(pk_light), 'blue')
    #================================================================================
    d={
      'name': li_name,
      'avail_name': lische_name,
      'control_opt': "ScheduleNameOnly",
      'category': "Parking Lighting",
      'power': "%.1f"%(pk_light),
    }
    parkli_temp, parkli_defs = templ.Equipment_ExteriorLighting()
    new_objs.insert(-1, idf_templater(d, parkli_temp, parkli_defs ) )
    #800,                     !- Design Level {W}

    scheparkli_temp, scheparkli_defs = templ.HVACtemplate_schedule_alwaysON()
    new_objs.insert(-1, idf_templater({'name': lische_name}, scheparkli_temp, scheparkli_defs ) )

    return new_objs

# SB: Should be executed in prep_model
def add_parkingexhaust_file(to_file=to_file):
    """Modified version of `add_parkingexhaust` which creates an IDF output for testing purposes. File output uses suffix `_parkingexhaust.idf` by default."""
    return __abstract_add_objs2file(add_parkingexhaust, to_file=to_file, suffix='parkingexhaust')

def add_parkingexhaust(objs_all, args={} ):
    """Add parking garage ventilation fans to model. Peak fan output is estimated by the total garage area (and available parking spots/CO emissions).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with added Parking Fans (Python `List`)
    """

    new_objs=list(objs_all)

    fan_sche_nm="PARKFAN_ALWAYS_ON"

    # Number of Cars/Parking spaces
    cars_per_unit=1.15 ## EEI number, see 10 Lisa
    objs_zonlist=filter_IDF_objs_raw(objs_all, 'ZoneList')
    zone_guestrm=extract_nms_from_zonelist(objs_zonlist, ' apartment')
    units= len(zone_guestrm)
    cars = cars_per_unit * units
    printc("Adding Exterior:Garage:Fan: Identified: %d Residential Units"%(units), 'blue')
    printc("Adding Exterior:Garage:Fan: Estimating: %.1f Cars or %.2f Car/unit"%(cars, cars_per_unit), 'blue')

    # CO from 10 Lisa EEI
    # Total Area: 24,108.339 m2
    # Parking Area: 2500 m2
    # 230 cars
    # Fans: 0.75HP * 4 = 0.746kW/hp / 0.8?? * 0.75*4 = 2.7975 kW
    #     : Fan power per car = 2.7975/230 = 0.01216 # kW/car
    # Hours Existing: 8760 hrs
    # Hours Retrofit: 2690 hrs (30.7078 %)

    # Fan Power per car:
    power_per_car = 0.01216 # kW/car
    fan_power = power_per_car * cars # kW

    #=========================================================================================
    printc("Adding Exterior:Garage:Fan object with output of: %.1f W"%(fan_power*1e3), 'blue')
    #=========================================================================================
    parkfan_temp, parkfan_defs = templ.Equipment_ParkFans()
    d={
      'power': "%.1f"%(fan_power),
      'name': "Parking Garage Fans",
      'sche_name': fan_sche_nm,
    }
    new_objs.insert(-1, idf_templater(d, parkfan_temp, parkfan_defs ) )
    fanavail_temp, fanavail_defs = templ.HVACtemplate_schedule_alwaysON()
    new_objs.insert(-1, idf_templater({'name': fan_sche_nm}, fanavail_temp, fanavail_defs ) )

    return new_objs

#SB: Models electricity reductions from using CO control in parking garages. NOTE: savings from heating/cooling are ignores. EEI suggest savings should be 50% electricity, 50% heating reduction
def mod_ext_parkingexhaust_file(to_file=to_file):
    """Modified version of `add_ext_parkingexhaust` which creates an IDF output for testing purposes. File output uses suffix `_MODexteriorExhaust.idf` by default."""
    return __abstract_add_objs2file(mod_ext_parkingexhaust, to_file=to_file, suffix='MODexteriorExhaust')

def mod_ext_parkingexhaust(objs_all, args={} ):
    """Modify exterior parking garage exhaust base power demand.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with modified parking garage fan (Python `List`)
    """

    new_objs=list(objs_all)

    # Name: Parking Garage Fans
    #exh_objs = [obj for obj in new_objs if get_obj_type(obj)=='Exterior:FuelEquipment']
    exh_objs = [obj for obj in new_objs if ( (get_obj_type(obj)=='Exterior:FuelEquipment') and ('parking garage fans' in get_obj_name(obj).lower()) ) ]
    #exh_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='Exterior:FuelEquipment']
    exh_idxs = [i for i,obj in enumerate(new_objs) if ( (get_obj_type(obj)=='Exterior:FuelEquipment') and ('parking garage fans' in get_obj_name(obj).lower()) )]
    if len(exh_objs) != 1 :
        printc("Modify Parking Exhaust ERROR: ZERO Exterior:Fuel/Fan objects found. Expected only one. Do Nothing", 'red')
        return objs_all
    #%.1f,                    !- Design Level {W}
    exhfan_obj = exh_objs[0]
    old_ln = exhfan_obj.split('\n')[4]
    print("old_ln: ", old_ln)
    old_vl = float( trim_comments(old_ln).strip(',') )
    frac = 0.307078 # Hours reduction by using CO control. See add_exhaust_file above. Based on EEI data
    new_vl = old_vl*frac
    temp_new_ln = "    %.1f,                    !- Design Level {W}"
    new_ln = temp_new_ln%( new_vl )
    print("new_ln: ", new_ln)
    printc("Modifying Parking Garage Fans: '%s' to '%s'"%(mkcolor("%.1f"%(old_vl),'red'), mkcolor("%.1f"%(new_vl), 'yellow')), 'blue')
    new_objs[ exh_idxs[0] ] = exhfan_obj.replace( old_ln, new_ln)

    return new_objs


def mod_exteriorlights_file(to_file=to_file):
    """Modified version of `mod_exteriorlights` which creates an IDF output for testing purposes. File output uses suffix `_modextlights.idf` by default."""
    return __abstract_add_objs2file(mod_exteriorlights, to_file=to_file, suffix='modextlights')

#def mod_exteriorlights(objs_all, frac=0.6, match_txt='Parking Garage Lights'):
def mod_exteriorlights(objs_all, args={ 'frac': 0.6, 'match_txt': 'Exterior Facade Lighting' } ):
    """Modified E+ `Exterior:Lights` object by multiplying peak power by fraction (ex. `frac=0.8`==20% reduction).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `frac` Fraction to reduce lighting peak power by. `match_txt` Name of exterior lighting object.

    Returns:

    * `new_objs`: genEPJ object list with modified exterior lighting (Python `List`)
    """

    new_objs=list(objs_all)
    match_txt = args['match_txt']
    frac = args['frac']

    #exli_objs = [obj for obj in new_objs if get_obj_type(obj)=='Exterior:Lights']
    #exli_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='Exterior:Lights']
    exli_objs = [obj for obj in new_objs if ( (get_obj_type(obj)=='Exterior:Lights') and (match_txt in obj) )]
    exli_idxs = [i for i,obj in enumerate(new_objs) if ( (get_obj_type(obj)=='Exterior:Lights') and (match_txt in obj) )]
    if len(exli_objs) != 1 :
        printc("Modify Exterior Lights ERROR: %d lighting objects found. Expected only one. Do Nothing" %( len(exli_objs) ), 'red')
        return objs_all
    #%.1f,                   !- Design Level {W}
    extlight_obj = exli_objs[0]
    old_ln = extlight_obj.split('\n')[3]
    print("old_ln: ", old_ln)
    old_vl = float( trim_comments(old_ln).strip(',') )
    new_vl = old_vl*frac
    temp_new_ln = "    %.1f,                   !- Design Level {W}"
    new_ln = temp_new_ln%( new_vl )
    print("new_ln: ", new_ln)
    printc("Modifying Exterior:Lights: '%s' to '%s'"%(mkcolor("%.1f"%(old_vl),'red'), mkcolor("%.1f"%(new_vl), 'yellow')), 'blue')
    new_objs[ exli_idxs[0] ] = extlight_obj.replace( old_ln, new_ln)

    return new_objs

def mod_ERV_specs_file(to_file=to_file):
    """Modified version of `mod_ERV_specs` which creates an IDF output for testing purposes. File output uses suffix `_modERV.idf` by default."""
    return __abstract_add_objs2file(mod_ERV_specs, to_file=to_file, suffix='modERV')

def mod_ERV_specs(objs_all, args={ 'mytype': 'Enthalpy', 'sens_eff': 0.85, 'lat_eff': 0.7 } ):
    """Modify HVACTemplate of DedicatedOutdoorAir system changing sensible/latent efficiency and mode (`Sensible` meaning heat recovery only (HRV mode) or `Latent` meaning sensible and latent/enthalpy recovery (ERV).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `mytype` Mode of heat exchange (Sensible/Latent). `sens_eff` Sensible heat recovery efficiency. `lat_eff` Latent enthalpy recovery efficiency.

    For meaningful results, values should be taken from manufacturer specification sheets.

    Returns:

    * `new_objs`: genEPJ object list with modified HRV/ERV details via changing parameters in `HVACTemplate:System:DedicatedOutdoorAir` (Python `List`)
    """

    new_objs=list(objs_all)
    # Need to rebuild list of E+ objects
    new_objs=get_IDF_objs_raw(new_objs)

    mytype=args['mytype']
    sens_eff=args['sens_eff']
    lat_eff=args['lat_eff']

    #exli_objs = [obj for obj in new_objs if get_obj_type(obj)=='Exterior:Lights']
    #exli_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='Exterior:Lights']
    doas_objs = [obj for obj in new_objs if get_obj_type(obj)=='HVACTemplate:System:DedicatedOutdoorAir' ]
    doas_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='HVACTemplate:System:DedicatedOutdoorAir' ]
    if len(doas_objs) != 1 :
        printc("Modify DOAS ERV Specs: ERROR: %d DOAS objects found. Expected only one. Do Nothing" %( len(doas_objs) ), 'red')
        return objs_all
    #Enthalpy,                    !- Heat Recovery Type
    #Sensible,                    !- Heat Recovery Type
    #0.7,                     !- Heat Recovery Sensible Effectiveness
    #0.65,                    !- Heat Recovery Latent Effectiveness
    doas_obj = doas_objs[0]

    old_type_ln   = doas_obj.split('\n')[33]
    old_sens_ln   = doas_obj.split('\n')[34]
    old_latent_ln = doas_obj.split('\n')[35]

    old_ln = old_type_ln
    print("old_ln: ", old_ln)
    old_vl = trim_comments(old_ln).strip(',')
    new_vl = mytype
    temp_new_ln = "    %s,                  !- Heat Recovery Type"
    new_ln = temp_new_ln%( new_vl )
    print("new_ln: ", new_ln)
    new_objs[ doas_idxs[0] ] = doas_obj.replace( old_ln, new_ln)
    printc("Modifying DOAS ERV Recovery Type: '%s' to '%s'"%(mkcolor(old_vl,'red'), mkcolor(new_vl, 'yellow')), 'blue')

    # fn used to format both floats/strings given as options
    def format_value(myflt):
        if myflt==0.0: return ''
        elif isinstance(myflt, str): return myflt # already a string
        else: return '%.2f'%(myflt)

    doas_obj = new_objs[ doas_idxs[0] ]
    old_ln = old_sens_ln
    print("old_ln: ", old_ln)
    old_vl = trim_comments(old_ln).strip(',')
    new_vl = format_value(sens_eff) # Formats given float to string
    temp_new_ln = "    %s,                  !- Heat Recovery Sensible Effectiveness"
    new_ln = temp_new_ln%( new_vl )
    print("new_ln: ", new_ln)
    new_objs[ doas_idxs[0] ] = doas_obj.replace( old_ln, new_ln)
    #printc("Modifying DOAS ERV Sensible Effectiveness: '%s' to '%s'"%(mkcolor("%.2f"%(old_vl),'red'), mkcolor("%.2f"%(new_vl), 'yellow')), 'blue')
    printc("Modifying DOAS ERV Sensible Effectiveness: '%s' to '%s'"%(mkcolor(old_vl,'red'), mkcolor(new_vl, 'yellow')), 'blue')

    doas_obj = new_objs[ doas_idxs[0] ]
    old_ln = old_latent_ln
    print("old_ln: ", old_ln)
    old_vl = trim_comments(old_ln).strip(',')
    new_vl = format_value(lat_eff) # Formats given float to string
    temp_new_ln = "    %s,                   !- Heat Recovery Latent Effectiveness"
    new_ln = temp_new_ln%( new_vl )
    print("new_ln: ", new_ln)
    new_objs[ doas_idxs[0] ] = doas_obj.replace( old_ln, new_ln)
    #printc("Modifying DOAS ERV Latent Effectiveness: '%s' to '%s'"%(mkcolor("%.2f"%(old_vl),'red'), mkcolor("%.2f"%(new_vl), 'yellow')), 'blue')
    printc("Modifying DOAS ERV Latent Effectiveness: '%s' to '%s'"%(mkcolor(old_vl,'red'), mkcolor(new_vl, 'yellow')), 'blue')

    return new_objs


def enforce_ashrae62_file(to_file=to_file):
    """Modified version of `enforce_ashrae62` which creates an IDF output for testing purposes. File output uses suffix `_ashrae62.idf` by default."""
    return __abstract_add_objs2file(enforce_ashrae62, to_file=to_file, suffix='ashrae62')

# SB NOTE: Breaks if not using HVACTemplate:Zone
# SB TODO: Enforce exhaust requirements: Mechanical, Electrical, Bathrooms, etc
# SB TODO: Check Zone Name: Ex. SiftonHQ: Corridors part of Office ZoneList  but not
def enforce_ashrae62(objs_all, args={}):
    """Ensure that ASHRAE62 ventilation rules are followed for all `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with enforced ASHRAE 62 ventilation guidelines (Python `List`)
    """

    new_objs=list(objs_all)

    # Implementation based on ASHRAE 62.1 2010, pg 12 OR 14/59
    ashrae62_rules={
    #   type    vent_per_area (cfm/ft2)   vent_per_person (cfm/p)  order
     "retail": [   0.12,                  7.5                    , 11],
     "office": [   0.06,                  5.0                    , 10],
     # Requires exhaust not ventilation
     "mechanical": [   0.03,              0.0                    , 10],
    # Residential corridors
     "lobby":  [   0.06,                  5.0                    , 10],
     "pool":  [    0.48,                  0.0                    , 10],
     "apart":  [   0.06,                  5.0                    , 10],
     "market": [   0.06,                  7.5                    , 10],
     # SB: Not based on standards
     "stair": [   0.00,                   0.0                    , 2],
     "tower": [   0.00,                   0.0                    , 1],
     "corridor": [ 0.06,                  0.0                    , 0],
     "parking":  [ 0.00,                  0.0                    , 12],
    }

    cfmft2_to_m3sm2=1/196.85039
    cfm_to_m3s=1/2118.88
    ashrae62_rules_SI={}
    for k in ashrae62_rules.keys():
        ashrae62_rules_SI[k] = [ ashrae62_rules[k][0]*cfmft2_to_m3sm2, ashrae62_rules[k][1]*cfm_to_m3s, ashrae62_rules[k][2]]

    #Flow/Person,             !- Outdoor Air Method
    #0.00944,                 !- Outdoor Air Flow Rate per Person {m3/s}
    #0.0,                     !- Outdoor Air Flow Rate per Zone Floor Area {m3/s-m2}
    #0.0,                     !- Outdoor Air Flow Rate per Zone {m3/s}
    oameth_regex=re.compile(r'[\w\d/.]*,[ ]+!- Outdoor Air Method')
    oapers_regex=re.compile(r'[\w\d/.]*,[ ]+!- Outdoor Air Flow Rate per Person')
    oaznfa_regex=re.compile(r'[\w\d/.]*,[ ]+!- Outdoor Air Flow Rate per Zone Floor Area')

    objs_filt_hvac=[obj for obj in new_objs if 'HVACTemplate:Zone' in get_obj_type(obj)]

    # SB TODO: Refactor, ugly but it works
    objs_zonlist=filter_IDF_objs_raw(objs_all, 'ZoneList')
    objs_zone=filter_IDF_objs_raw(objs_all, 'Zone')
    modded_zones=[]
    # ORDER DOESNT matter
    #for key in ashrae62_rules_SI.keys():
    # ORDER DOES matter
    for key in sorted(ashrae62_rules_SI, key=lambda k: ashrae62_rules_SI[k][2]):
        # Get all Zone object names from Zonelist with ASHRAE keyword in them
        zl_obj=[zl for zl in objs_zonlist if key in get_obj_name(zl).lower()]
        #print("ZoneList: %s"%(zl_obj))
        try:
            #zone_nms=extract_nms_from_zonelist(zl_obj[0], key)
            zone_nms=extract_nms_from_zonelist(zl_obj, key)
        except:
            zone_nms=[]
        # Get all Zone object names with ASHRAE keyword in them
        other_zone_nms = [get_obj_name(o) for o in objs_zone if key in get_obj_name(o).lower()]
        # Join ZoneList and Zone names
        # SB: Prioritize names found in Zones (very intentional: Tower will match to 'office' instead of 'tower')
        zone_nms = other_zone_nms+zone_nms
        # SB: Use set so we dont count zone names twice. Now handled by modded_zones. set() screws up order
        #zone_nms = list( set( other_zone_nms+zone_nms ) )
        #print("other ZN: %s"%(other_zone_nms))
        #for znm in zone_nms:
        for znm in zone_nms:
            if znm not in modded_zones:
                objs_filt_hvac=[obj for obj in new_objs if 'HVACTemplate:Zone' in get_obj_type(obj)]
                hvac_objs = [o for o in objs_filt_hvac if znm in get_obj_name(o)]
                if len(hvac_objs)>0 :
                    printc("Modifying Zone: '%s' which matches ASHRAE key: %s"%(mkcolor(znm,'red'), mkcolor(key, 'yellow')), 'blue')
                    hvac_obj=hvac_objs[0]
                    _meth_ln = oameth_regex.findall(hvac_obj)[0]
                    _meth = trim_comments(_meth_ln).strip()
                    _pers_ln = oapers_regex.findall(hvac_obj)[0]
                    _pers = trim_comments(_pers_ln).strip()
                    _znfa_ln = oaznfa_regex.findall(hvac_obj)[0]
                    _znfa = trim_comments(_znfa_ln).strip()
                    _idx=[ jj for jj,obj in enumerate(new_objs) if hvac_obj==obj][0]
                    o = hvac_obj
                    o = o.replace( _meth_ln, _meth_ln.replace( _meth, "Sum,"))
                    o = o.replace( _znfa_ln, _znfa_ln.replace( _znfa, str(ashrae62_rules_SI[key][0])+',') )
                    o = o.replace( _pers_ln, _pers_ln.replace( _pers, str(ashrae62_rules_SI[key][1])+',') )
                    new_objs[_idx] = o
                    modded_zones.append(znm)

    return new_objs


def add_internalmass_file(to_file=to_file):
    """Modified version of `add_internalmass` which creates an IDF output for testing purposes. File output uses suffix `_IntMass.idf` by default."""
    return __abstract_add_objs2file(add_internalmass, to_file=to_file, suffix='IntMass')


# Internal Mass Options: (Used in E+/ExampleFiles)
#  1) Light Partitions
#   Construction,
#    Light Partitions,        !- Name
#    G01a 19mm gypsum board,  !- Outside Layer
#    F04 Wall air space resistance,  !- Layer 2
#    G01a 19mm gypsum board;  !- Layer 3
#  2) Furniture (Various)
# MediumFurniture
# FurnitureConstruction (SuperMarkets)
# FURNITURE "Furniture is modeled as 8 inches of wood covering 1/2 the floor area"
#  3) Frozen Fruit (Freezers)
#  4) "InteriorFurnishings" Ex. Shops/RefBldg (Std Wood 6inch: Partition walls?)
def add_internalmass(objs_all, args={}):
    """Add E+ `InternalMass` objects to all `Zones` with non-zero surface areas. The default surface area of the `InternalMass` is based on the `Zone` area. Using defaults as per the DOE building archetypes. The physical details of the `InternalMass` objects is dictated by the `InteriorFurnishings` object in the template file located in `sim/templates/{ref,prop}_constructions_materials.idf` file.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `zone_selective_add` Add `InternalMass` only to this list of `Zones`. `zone_selective_all_except` Add `InternalMass` objects to all `Zones` except this list of `zones`.

    Returns:

    * `new_objs`: genEPJ object list with `InternalMass` objects added to specified `Zones`(Python `List`)
    """

    new_objs=list(objs_all)

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    #temp_intfin, defs_intfin=  templ.Material_InteriorFinish()
    #new_objs.insert(-1, templater( {}, temp_intfin, defs_intfin) )

    obj_version=filter_IDF_objs_raw(objs_all, 'Version')[0]
    version=get_obj_abstract(obj_version,1)
    #print("TEST Version",version)
    vers_ma,vers_mi=version.split('.')
    vers_ma, vers_mi = int( vers_ma ), int( vers_mi )
    # E+ v9.6 changed InternalMass object
    if ( (vers_ma>9) or ( (vers_ma==9) and (vers_mi>=6)) ) :
        temp_intmass, defs_intmass=templ.Material_InternalMassv96()
    else:
        temp_intmass, defs_intmass=templ.Material_InternalMass()

    # Zones to add internal mass to
    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    # VD TODO: Repeat this block of code for other functions.
    # VD: Add specific zones if specified
    if 'zone_selective_add' in args:
        zone_selective_add = args['zone_selective_add']
        zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon if zone_selective_add in get_obj_name(myobj).lower()]
        # VD NOTE: Haven't tested this yet. For multiple zones requiring the same mass.
        # zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon if is_in(zone_selective_add, get_obj_name(myobj).lower()]
    # VD: Add to all except for specified zones
    elif 'zone_selective_all_except' in args:
        zone_selective_all_except = args['zone_selective_all_except']
        zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon if zone_selective_all_except not in get_obj_name(myobj).lower()]
        # VD NOTE: Haven't tested this yet. For multiple zones requiring the same mass, except for a list.
        # zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon if not is_in(zone_selective_add, get_obj_name(myobj).lower()]
    # VD: Otherwise, apply to every zone
    else:
        zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon]

    # Implement based on SA/m2 FA?
    for zone_nm in zone_use_nms:
        intmass_area = float( _calc_area_intmass( zone_nm.upper() ) )
        # Only add thermal mass if area > 0
        if intmass_area > 0 :
            printc("Adding InternalMass objects with Surface Area of %s to Zone %s"%( mkcolor("%.2f"%(intmass_area), 'blue'), mkcolor(zone_nm,'yellow')) ,'green' )
            d={
              'surf_area': "%.2f"%(intmass_area),
              'zone_name': zone_nm,
            }

            # VD: Use non-default construction if a construction is supplied
            if 'const_name' in args: d['const_name'] = args['const_name']
            if 'suffix' in args: d['suffix'] = " "+args['suffix']

            new_objs.insert(-1, idf_templater( d, temp_intmass, defs_intmass) )
        else:
            printc("NOT Adding InternalMass objects with ZERO Surface Area Zone %s"%( mkcolor(zone_nm,'yellow')) ,'red' )

    return new_objs

#TODO Refactors Generator list using Templates
def add_PV_by_azi_file(to_file=to_file):
    """Modified version of `add_PV_by_azi` which creates an IDF output for testing purposes. File output uses suffix `_PV.idf` by default."""
    return __abstract_add_objs2file(add_PV_by_azi, to_file=to_file, suffix='PV')

#def add_PV_by_azi(myobjs, frac=0.8, azi=180, pm=180, Model=feat_dict['pv_model'], PVcoupled=feat_dict['pv_couple']):
def add_PV_by_azi(myobjs, args={ 'frac': 0.8, 'azi': 180, 'pv_eff': 0.16, 'pm': 180, 'Model': feat_dict['pv_model'], 'PVcoupled': feat_dict['pv_couple'],} ):
    """Add Photovoltaic (PV) Panels to cardinal directions.
    Allow user to specify PV model (`Simply`, `OneDiode`, `Sandia`, etc) and thermal coupling to surface via feature list.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `azi` cardinal direction that PV is to added. `pv_eff` PV panel efficiency (fraction). `pm` plus/minus variation (typically +/- 45deg). `frac` Area fraction that PV will cover surface. `Model` Overrides feature dictionary specified PV solver model.

    E+ surfaces determined using a SQL query.

    Returns:

    * `new_objs`: genEPJ object list with PV panels added for specified cardinal direction (Python `List`)
    """

    frac=args['frac']
    azi=args['azi']
    pm=args['pm']
    Model=args['Model']
    PVcoupled=args['PVcoupled']

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    if Model==1 :    Model='Simple'
    elif Model==2 :  Model='OneDiode'
    elif Model==3 :  Model='Sandia'

    if frac==0 :
        printc("Given zero area for PV azi %.0f! Nothing to do!"%(azi), 'red')
        return myobjs

    temp_pvgen, defs_pvgen=  templ.Equipment_PVGenerator()

    start_PVgenlist="""\n
  ElectricLoadCenter:Generators,
    PV list %d,                 !- Name
"""
    ## Get all exterior surfaces
    #objs_filt_sur=filter_IDF_objs_raw(myobjs, 'BuildingSurface:Detailed')
    #objs_surf_ext=[surf for surf in objs_filt_sur if _get_surf_BC(surf)=='Outdoors']
    ## Get all exterior shading devices
    #objs_shading=filter_IDF_objs_raw(myobjs, 'Shading:Zone:Detailed')
    #objs_surf_ext.extend(objs_shading)

    ## Get all Ballasted racking surfaces
    objs_shading=filter_IDF_objs_raw(myobjs, 'Shading:Building')
    rack_nms = [get_obj_name(obj) for obj in objs_shading if 'ballast' in get_obj_name(obj).lower()]

    #sql_file=to_file.replace('idf','sql').replace('data_temp/','data_temp/Output/')
    #conn = sqlite3.connect(sql_file)
    #c = conn.cursor()

    ## Get all exterior surfaces by Azimuth
    # TODO- Implement PV on all shading
    # TODO- Requires presimulation!! WWR will affect PV surf area
    # Only add BIPV to higher wall sections: MinimumZ>0
    #pvwall_sql_sel='SELECT a.SurfaceName FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Wall" AND a.Azimuth>=%d AND a.Azimuth<=%d AND a.ExtBoundCond=0 AND a.ZoneIndex=b.ZoneIndex AND b.MinimumZ>0 AND b.ZoneName NOT LIKE "#TOWER#"'
    pvwall_sql_sel='SELECT a.SurfaceName FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Wall" AND a.Azimuth>=%d AND a.Azimuth<=%d AND a.ExtBoundCond=0 AND a.ZoneIndex=b.ZoneIndex AND b.MaximumZ>0 AND b.ZoneName NOT LIKE "#TOWER#"'
    # SB NOTE: Need to change such that the Tower isnt included
    pvroof_sql_sel='SELECT a.SurfaceName FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Roof" AND a.ExtBoundCond=0 AND a.ZoneIndex=b.ZoneIndex AND b.ZoneName NOT LIKE "#TOWER#"'

    # SB: Hack: %TOWER% is read in as a substitution. Update for Python string formatting
    subbed_pvwall=pvwall_sql_sel%(azi-pm/2., azi+pm/2. )
    pv_wall_names=c.execute(subbed_pvwall.replace('#','%')).fetchall()
    #pv_wall_nms=map(lambda x: x[0], pv_wall_names)
    pv_wall_nms=list( map(lambda x: x[0], pv_wall_names) )
    pv_roof_names=c.execute(pvroof_sql_sel).fetchall()
    #pv_roof_nms=map(lambda x: x[0], pv_roof_names)
    pv_roof_nms=list( map(lambda x: x[0], pv_roof_names) )

    ## NOTE: Wall facing azimuth must be due south for Ballasted PV to be added
    #if ( (len(rack_nms)>0) and (azi-pm/2. <= 180 <= azi+pm/2.)):
    #    print("Using Rack Names: ",rack_nms)
    #    pv_roof_nms=rack_nms # Use ballasted PV not roof surfaces
    #elif ( (len(rack_nms)==0) and (azi-pm/2. <= 180 <= azi+pm/2.)): # No ballasted PV racks, use roof surface
    #    pv_roof_nms=pv_roof_nms
    #else: # SB: don't use roof space unless south PV area specified and ballasts specified
    #    pv_roof_nms=[]


    # SB: Hack to sepecify roof areas using Azi==0 (normally north faced surfaces [reset using pv_wall_nms=[])
    if ( (len(rack_nms)>0) and (azi==0)):
        print("Using Rack Names: ",rack_nms)
        pv_roof_nms=rack_nms # Use ballasted PV not roof surfaces
        pv_wall_nms=[]
    elif ( (len(rack_nms)==0) and (azi==0)): # No ballasted PV racks, use roof surface
        pv_roof_nms=pv_roof_nms
        pv_wall_nms=[]
    else: # SB: don't use roof space unless south PV area specified and ballasts specified
        pv_roof_nms=[]

    pv_surf_nms=pv_wall_nms+pv_roof_nms

    old_pv_surf_nms = list( pv_surf_nms )
    # Add or remove surfaces provided a list in args
    # add_surface_list, omit_surface_list
    # surface_add_list, surface_omit_list
    # Side-effects: Add or remove surfaces from pv_surf_nms
    if 'add_surface_list' in args:
        add_surface_list = args['add_surface_list']
        add_surf_nms = [s for s in add_surface_list if not is_in2(pv_surf_nms, s.upper())]
        pv_surf_nms = pv_surf_nms + add_surf_nms
    if 'omit_surface_list' in args:
        omit_surface_list = args['omit_surface_list']
        omit_surface_list = [ s.upper() for s in omit_surface_list ]
        pv_surf_nms = [s for s in pv_surf_nms if not is_in(omit_surface_list, s)]
    # Debug:
    diff=list(set(old_pv_surf_nms) - set(pv_surf_nms))
    #print(diff)
    for d in diff:
        printc("  PV omit_surface: REMOVED surface: %s"%(mkcolor(d,'red')),'yellow')
    diff=list(set(pv_surf_nms) - set(old_pv_surf_nms))
    for d in diff:
        printc("  PV add_surface: ADDED surface: %s"%(mkcolor(d,'yellow')),'green')

    #printc("Adding PV objects on %s surfaces"%(mkcolor(str(len(objs_surf_ext)),'yellow')),'green')

    def _handle_PVcoupling(sn, type):
        if PVcoupled:
            #return temp_PVgen%(sn, sn, type, azi, frac, 'IntegratedSurfaceOutsideFace' )
            mode="IntegratedSurfaceOutsideFace"
        else:
            #return temp_PVgen%(sn, sn, type, azi, frac, 'Decoupled')
            mode="Decoupled"
        d={
          'name': "PV %s"%(sn),
          'surf_name': sn,
          'pv_type': type,
          'pv_name': "16percentEffPV Azi %d Frac %0.2f"%(azi, frac),
          'mode': mode,
        }
        return idf_templater( d, temp_pvgen, defs_pvgen)

    obj_idx=-1
    new_objs=list(myobjs)

    #new_objs.insert(obj_idx, sche_PV%(azi))
    load_sche_nm="ALWAYS ON PV %d"%(azi)
    loadsche_temp, loadsche_defs = templ.HVACtemplate_schedule_alwaysON2()
    new_objs.insert(-1, idf_templater({'name': load_sche_nm, 'limits': "ANY"}, loadsche_temp, loadsche_defs ) )


    PVgen_lst=[start_PVgenlist%(azi)]

    for j,surf_nm in enumerate(pv_surf_nms):
        # SB: j is unspecific to direction. Need this for PV diagnostics
        if Model=='Simple':
            new_objs.insert(obj_idx, _handle_PVcoupling(surf_nm, 'PhotovoltaicPerformance:Simple') )

            if j==0 :
                printc("Using PV fractional area of %s percent for direction %s"%(mkcolor(str(100*frac),'yellow'), mkcolor(str(azi),'yellow')),'green')
                #new_objs.insert(obj_idx, temp_PV%(azi, frac, frac))
                temp_pv, defs_pv=  templ.Equipment_PV()
                d={
                  'name': "16percentEffPV Azi %d Frac %.2f"%(azi, frac),
                  'frac': "%.2f"%(frac),
                  'pv_eff': "0.16",
                }
                if 'pv_eff' in args:
                    d['pv_eff']=args['pv_eff']
                new_objs.insert(-1, idf_templater( d, temp_pv, defs_pv) )
        elif Model=='OneDiode':
            new_objs.insert(obj_idx, _handle_PVcoupling(surf_nm, 'PhotovoltaicPerformance:EquivalentOne-Diode') )

            if j==0 :
                printc("Using PV fractional area of %s percent for direction %s"%(mkcolor(str(100*frac),'yellow'), mkcolor(str(azi),'yellow')),'green')
                #new_objs.insert(obj_idx, temp_OD_PV%(azi))
                temp_pvOD, defs_pvOD=  templ.Equipment_PVonediode()
                d={
                  'name': "16percentEffPV Azi %d Frac %.2f"%(azi, frac),
                }
                new_objs.insert(-1, idf_templater( d, temp_pvOD, defs_pvOD) )

        elif Model=='Sandia':
            new_objs.insert(obj_idx, _handle_PVcoupling(surf_nm, 'PhotovoltaicPerformance:Sandia') )
            if j==0 :
                printc("Using PV fractional area of %s percent for direction %s"%(mkcolor(str(100*frac),'yellow'), mkcolor(str(azi),'yellow')),'green')
                #new_objs.insert(obj_idx, temp_Sandia_PV%(azi))
                temp_pvsan, defs_pvsan=  templ.Equipment_PVsandia()
                d={
                  'name': "16percentEffPV Azi %d Frac %.2f"%(azi, frac),
                }
                new_objs.insert(-1, idf_templater( d, temp_pvsan, defs_pvsan) )

        else:
            raise ValueError("Invalid model type given to PVgenerate! Must be in set: ['Simple', 'OneDiode', 'Sandia']")
        #if j+1<=len(objs_surf_ext):
        printc("Adding PV objects to %s"%(mkcolor(surf_nm)),'green')
        temp_PVgenlist, defs_PVgenlist=  templ.Equipment_LoadCenterGeneratorsParts()
        d={
          'name': surf_nm,
          'gen_type': "Generator:Photovoltaic",
          'azi': "%d"%(azi),
          'iter': "%d"%(j+1),
        }
        if len(pv_surf_nms)>j+1 :
            #PVgen_lst.append(temp_PVgenlist%{"nm": surf_nm, "iter": j+1, "azi": azi})
            PVgen_lst.append( idf_templater( d, temp_PVgenlist, defs_PVgenlist) )
        else: # Last element in the Generation List. Special treatment required
            # NOTE: how to replace ',' with ';' at the last generator in genlist
            #_t=temp_PVgenlist%{"nm": surf_nm, "iter": j+1, "azi": azi}
            _t = idf_templater( d, temp_PVgenlist, defs_PVgenlist)
            _t=_t.replace(',',';').replace(';',',',4)
            PVgen_lst.append(_t)

    new_objs.insert(obj_idx, ''.join(PVgen_lst))

    #new_objs.insert(obj_idx, temp_PVinv%(azi, azi))
    temp_pvinv, defs_pvinv=  templ.Equipment_PVInverter()
    d={'name': "Simple Ideal Inverter %d"%(azi),
       'avail_sche': "ALWAYS ON PV %d"%(azi),
       'inv_eff': "0.90", }
    new_objs.insert(-1, idf_templater( d, temp_pvinv, defs_pvinv) )

    #new_objs.insert(obj_idx, temp_PVdist%(azi, azi, azi))
    temp_dist, defs_dist=  templ.Equipment_LoadCenterDistribution()
    d={'name': "Simple Electric Load Center %d"%(azi),
       'gen_name': "PV list %d"%(azi),
       'inv_name': "Simple Ideal Inverter %d"%(azi),
       'bus_type': "DirectCurrentWithInverter", }
    new_objs.insert(-1, idf_templater( d, temp_dist, defs_dist) )

    if options.debugpv:
        printc("Adding PV specific Output Variables", 'yellow')

        temp_output, output_defs =templ.template_output()

        output_vars=[
          'Generator Produced DC Electric Power',
          'Generator Produced DC Electric Energy',
          'Inverter AC Output Electric Energy',
          'Inverter AC Output Electric Power',
          'Site Horizontal Infrared Radiation Rate per Area',
          'Site Diffuse Solar Radiation Rate per Area',
          'Site Direct Solar Radiation Rate per Area',
          'Site Ground Reflected Solar Radiation Rate per Area',
        ]

        for v in output_vars:
            #new_objs.insert(obj_idx, idf_templater( {'name': v}, temp_output, {} ) )
            new_objs.insert(obj_idx, idf_templater( {'name': v, 'timestep': "hourly"}, temp_output, {} ) )

    return new_objs

# SB: NOT WORKING: TODO test it: Thu Jul  7 10:52:58 EDT 2016
# Challenge: Shading:Zone:Detailed
def add_ballastedPVrack_file(to_file=to_file):
    """Modified version of `add_ballastedPVrack` which creates an IDF output for testing purposes. File output uses suffix `_BallPV.idf` by default."""
    return __abstract_add_objs2file(add_ballastedPVrack, to_file=to_file, suffix='BallPV')

# TODO: Add x,y, ballast length offsets
#def add_ballastedPVrack(objs_all, space_mul=2.0, angle=15):
def add_ballastedPVrack(objs_all, args={'space_mul':2.0, 'angle':45}):
    """Add PV objects on to ballasts located in rows (shading surface objects in E+).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `space_mul` height/width from previous ballasted row of PVs, `angle` angle of ballasts

    Returns:

    * `new_objs`: genEPJ object list with Ballasted PV added (Python `List`)
    """
    space_mul=args['space_mul']
    angle=args['angle']

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    # Format vertices for below template
    def form4(v): return "%.4f"%(v)
    def form2(v): return "%.2f"%(v)
    def form3(v): return "%d"%(v)
    temp_pvball, defs_pvball=  templ.ShadingBallastPV()

    new_objs=list(objs_all)

    _z_if_none = lambda x: 0 if x is None else x

    ### Get max z-corr on near south facing surface
    objs_filt_surf=filter_IDF_objs_raw(new_objs, 'BuildingSurface:Detailed')
    pm=2 # pm in degress
    azi=180
    maxz_sql_sel = 'SELECT MAX(b.MaximumZ) FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Wall" AND a.Azimuth==0 AND a.ExtBoundCond=0 AND a.ZoneIndex=b.ZoneIndex AND b.MinimumX==0 AND b.ZoneName NOT LIKE "%TOWER%"'
    # South facing largest X-axis with same height as maxZ (Length of PV Ballast Array)
    maxx_sql_sel = 'SELECT MAX(b.MaximumX) FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Wall" AND a.Azimuth==0 AND a.ExtBoundCond=0 AND a.ZoneIndex=b.ZoneIndex AND b.MaximumZ==%d AND b.ZoneName NOT LIKE "#TOWER#"'
    maxy_sql_sel = 'SELECT MAX(b.MaximumY) FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Wall" AND a.Azimuth==0 AND a.ExtBoundCond=0 AND a.ZoneIndex=b.ZoneIndex AND b.MinimumX==0 AND b.MaximumZ==%d AND b.ZoneName NOT LIKE "#TOWER#"'
    maxz = c.execute(maxz_sql_sel).fetchone()[0]
    maxx_sql_sel_subbed = maxx_sql_sel%(maxz)
    maxy_sql_sel_subbed = maxy_sql_sel%(maxz)
    maxx = c.execute(maxx_sql_sel_subbed.replace('#','%')).fetchone()[0]
    maxy = c.execute(maxy_sql_sel_subbed.replace('#','%')).fetchone()[0]
    print(maxz, maxx, maxy)
    maxz, maxx, maxy= list(map(_z_if_none, [maxz, maxx, maxy]))

    ## Calc Max number of ballast rows
    panel_h=2
    # Angle set by function now... Testing below only...
    #angle=45.0
    #angle=15
    #angle=0
    proj_h = panel_h*sin(angle * pi/180.)
    proj_x = panel_h*cos(angle * pi/180.)
    spacing = space_mul*proj_h #Old rule of thumb for spacing of solar panels
    proj_h,proj_x,proj_x= list(map(_z_if_none, [proj_h, proj_x, proj_x])) # Map to zero if value is None
    rows=floor(maxy/(proj_x+spacing))
    print("Proj h: %f, Proj x: %f, Spacing: %f, Rows: %f"%(proj_h, proj_x, spacing, rows))

    for rw in range(int(rows)):
        #new_objs.insert(-1, temp_ballPV_simple%(rw+1, 180-angle, 0, (proj_x+spacing)*rw, maxz, -maxx, panel_h))
        d={
          'row_num': form3(rw+1),
          'length': form2(-maxx),
          'height': form2(panel_h),
          'tilt': form2(180-angle),
          'x': form4(0), 'y': form4((proj_x+spacing)*rw), 'z': form4(maxz),
        }
        new_objs.insert(-1, idf_templater( d, temp_pvball, defs_pvball) )
        last_space=(proj_x+spacing)*rw
        printc("Adding Ballast objects to row %s"%(mkcolor(str(rw+1),'yellow')),'green')
        print("Last Space: ",last_space)

    # Add more PV on 2nd rectangle (Sifton HQ only...)
    minx_sql_sel = 'SELECT MIN(b.MinimumX) FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Roof" AND a.ExtBoundCond=0 AND a.ZoneIndex=b.ZoneIndex AND b.MaximumZ==%d AND b.MinimumY>=%d AND b.ZoneName NOT LIKE "#TOWER#"'
    maxx2_sql_sel = 'SELECT MAX(b.MaximumX) FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Roof" AND a.ExtBoundCond=0 AND a.ZoneIndex=b.ZoneIndex AND b.MaximumZ==%d AND b.MinimumY>=%d AND b.ZoneName NOT LIKE "#TOWER#"'
    maxy2_sql_sel = 'SELECT MAX(b.MaximumY) FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Roof" AND a.ExtBoundCond=0 AND a.ZoneIndex=b.ZoneIndex AND b.MaximumY>=0 AND b.MaximumZ==%d AND b.ZoneName NOT LIKE "#TOWER#"'
    minx_sql_sel_subbed = minx_sql_sel%(maxz,maxy)
    maxx2_sql_sel_subbed = maxx2_sql_sel%(maxz,maxy)
    maxy2_sql_sel_subbed = maxy2_sql_sel%(maxz)
    maxx2 = c.execute(maxx2_sql_sel_subbed.replace('#','%')).fetchone()[0]
    maxy2 = c.execute(maxy2_sql_sel_subbed.replace('#','%')).fetchone()[0]
    minx = c.execute(minx_sql_sel_subbed.replace('#','%')).fetchone()[0]
    maxx2, maxy2, minx= list(map(_z_if_none, [maxx2, maxy2, minx]))
    rows2=floor((maxy2-maxy)/(proj_x+spacing))
    length=abs(maxx2-minx)
    print("X-coord: ",[minx, maxx2])
    print("Y-coord: ",[maxy, maxy2])

    y_start=maxy
    for rw in range(int(rows2)):
        #new_objs.insert(-1, temp_ballPV_simple%(rows+rw+1, 180-angle, minx, y_start+(proj_x+spacing)*rw, maxz, -length, panel_h))
        d={
          'row_num': form3(rows+rw+1),
          'length': form2(-length),
          'height': form2(panel_h),
          'tilt': form2(180-angle),
          'x': form4(minx), 'y': form4(y_start+(proj_x+spacing)*rw), 'z': form4(maxz),
        }
        new_objs.insert(-1, idf_templater( d, temp_pvball, defs_pvball) )
        last_space=(proj_x+spacing)*rw
        printc("Adding Ballast objects to row %s"%(mkcolor(str(int(rows)+rw+1),'yellow')),'green')
        print("Last Space: ",last_space)

    #printc("Adding Exterior Static Shading objects on %s surfaces"%(mkcolor(str(len(objs_win)),'yellow')),'green')
    #obj_idx=-1

    return new_objs


def add_PVarray_file(to_file=to_file):
    """Modified version of `add_PVarray` which creates an IDF output for testing purposes. File output uses suffix `_PVarr.idf` by default."""
    return __abstract_add_objs2file(add_PVarray, to_file=to_file, suffix='PVarr')


def add_PVarray(objs_all, args={ 'area': 1500, 'ang': 45, 'pv_eff': 0.16 } ):
    """Add large PV array beside the building. Assume only used if PV area on building is insufficient"""

    # Implementation:
    # 1. Template for PV objects
    #    * Trying using a flat surface first z=0
    #    * Then implement of angled surface
    # 2. Build a large surface (ang x?) to put PV on. Adiabatic?
    # 3. Add PV to surface
    # 4. Building a separate inverter and generator list
    ## Reference: ShopWithSimplePVT.idf

    if ( args['area']==0 or args['pv_eff']==0):
        printc("add_PVarray: Nothing to do, PV array size/efficiency is zero", 'yellow')
        return objs_all

    area=args['area']
    ang=args['ang']
    new_objs=list(objs_all)

    load_sche_nm="ALWAYS ON PV 2"
    surf_nm="Collector Surface"
    pv_nm="16percentEffPV0.8Area2"

    # Area to Wattage conversion:
    # Canadian Solar: ELPS CS6P-MM, 260W, 1638 x 982 x 40mm (1.608516m2)
    # P = 161.64 W/m2

    objs_zn=filter_IDF_objs_raw(new_objs, 'Zone')

    try:
        coors=map(_get_zone_coordin, objs_zn)

        # Get building depth (max y)
        ycoors=map(lambda m: m[1], coors)
        y=max(ycoors)

        # Get building height (max z)
        zcoors=map(lambda m: m[2], coors)
        h=max(zcoors)
    except:
        y=1000
        h=100

    #print("Max Y (m), Max Z (m): ", (y,h))
    s1=sqrt(area) # Side length, in meters

    # SB NOTE- Likely 2*h is sufficient for no building shading, use 3*h to be careful
    #    * Installation is shifted on y-axis to max point out

    # IF Sloped
    y2=s1*cos( ang*pi/180.)
    z2=s1*sin( ang*pi/180.)
    v1_x, v1_y, v1_z= 0, y+3*h+y2, z2
    v2_x, v2_y, v2_z= 0, y+3*h   , 0
    v3_x, v3_y, v3_z= s1,y+3*h   , 0
    v4_x, v4_y, v4_z= s1,y+3*h+y2, z2

    ## IF FLAT
    #v1_x, v1_y, v1_z= 0, y+3*h+s1, 0
    #v2_x, v2_y, v2_z= 0, y+3*h   , 0
    #v3_x, v3_y, v3_z= s1,y+3*h   , 0
    #v4_x, v4_y, v4_z= s1,y+3*h+s1, 0

    printc("Adding PV Field to surface: %s (Area: %.1f, Angle, %.0f)"%(mkcolor("Shading:Site:Detailed",'green'), area, ang), "blue")

    # Format vertices below
    def f(v): return "%.4f"%(v)
    temp_siteobs, defs_siteobs=  templ.ShadingSiteObstruction()
    d={
      'name': "Collector Surface",
      'x11': f(v1_x), 'x12': f(v1_y), 'x13': f(v1_z),
      'x21': f(v2_x), 'x22': f(v2_y), 'x23': f(v2_z),
      'x31': f(v3_x), 'x32': f(v3_y), 'x33': f(v3_z),
      'x41': f(v4_x), 'x42': f(v4_y), 'x43': f(v4_z),
    }
    new_objs.insert(-1, idf_templater( d, temp_siteobs, defs_siteobs) )

    temp_pv, defs_pv=  templ.Equipment_PV()
    d={
      'name': pv_nm,
      'frac': "0.8",
      'pv_eff': "0.16",
    }
    if 'pv_eff' in args:
        d['pv_eff']=args['pv_eff']
    new_objs.insert(-1, idf_templater( d, temp_pv, defs_pv) )

    loadsche_temp, loadsche_defs = templ.HVACtemplate_schedule_alwaysON2()
    new_objs.insert(-1, idf_templater({'name': load_sche_nm, 'limits': "ANY"}, loadsche_temp, loadsche_defs ) )

    temp_pvinv, defs_pvinv=  templ.Equipment_PVInverter()
    d={
      'name': "Simple Ideal Inverter big array",
      'frac': "0.8",
      'avail_sche': load_sche_nm,
      'inv_eff': "0.90",
    }
    new_objs.insert(-1, idf_templater( d, temp_pvinv, defs_pvinv) )

    temp_pvgen, defs_pvgen=  templ.Equipment_PVGenerator()
    d={
      'name': "Simple PV Field",
      'surf_name': surf_nm,
      'pv_type': "PhotovoltaicPerformance:Simple",
      'pv_name': pv_nm,
    }
    new_objs.insert(-1, idf_templater( d, temp_pvgen, defs_pvgen) )

    temp_ldcentr, defs_ldcentr=  templ.Equipment_LoadCenterGenerators()
    d={
      'name': "PV list big array",
      'gen_name': "Simple PV Field",
      'gen_type': "Generator:Photovoltaic",
      'pk_power': "200000",
      'avail_sche': load_sche_nm,
    }
    new_objs.insert(-1, idf_templater( d, temp_ldcentr, defs_ldcentr) )

    temp_dist, defs_dist=  templ.Equipment_LoadCenterDistribution()
    d={
      'name': "Simple Electric Load Center big array",
      'gen_name': "PV list big array",
      'inv_name': "Simple Ideal Inverter big array",
      'bus_type': "DirectCurrentWithInverter",
    }
    new_objs.insert(-1, idf_templater( d, temp_dist, defs_dist) )

    if options.debugpv:
        obj_idx=-1
        printc("Adding PV specific Output Variables", 'yellow')

        temp_output, output_defs =templ.template_output()

        output_vars=[
          'Generator Produced DC Electric Power',
          'Generator Produced DC Electric Energy',
          'Inverter AC Output Electric Energy',
          'Inverter AC Output Electric Power',
          'Site Horizontal Infrared Radiation Rate per Area',
          'Site Diffuse Solar Radiation Rate per Area',
          'Site Direct Solar Radiation Rate per Area',
          'Site Ground Reflected Solar Radiation Rate per Area',
        ]

        for v in output_vars:
            #new_objs.insert(obj_idx, idf_templater( {'name': v}, temp_output, {} ) )
            new_objs.insert(obj_idx, idf_templater( {'name': v, 'timestep': "hourly"}, temp_output, {} ) )

    return new_objs

def add_misc_baseload_file(to_file=to_file, frac=1.0):
    """Modified version of `add_misc_baseload` which creates an IDF output for testing purposes. File output uses suffix `_miscbase.idf` by default."""
    return __abstract_add_objs2file(add_misc_baseload, to_file=to_file, suffix='miscbase')

# SB NOTE- Intentional Hack. Not happy with ASHRAE standards for Baseloads
def add_misc_baseload(objs_all, args={ 'frac': 1.0, 'load': 2.15278, 'enduse': "ElectricEquipment", 'suffix': "" }):
    """Add miscellaneous electric baseload using E+ `ElectricEquipment` objects in specified `Zones` with a specified enduse type (for E+ energy accounting).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `frac` Fraction of specified load to implement. `load` specified baseload. `enduse` E+ Equipment type to attribute load to (Electric by default). `zone_selective_add` Add baseload only to this list of `Zones`. `zone_selective_all_except` Add `baseload` objects to all `Zones` except this list of `zones`.

    Returns:

    * `new_objs`: genEPJ object list with miscellaneous baseload (Python `List`)
    """

    new_objs=list(objs_all)

    frac=args['frac']
    load=args['load']
    enduse=args['enduse']
    suffix=args['suffix']

    #=========================================================
    # Template: Add Baseload schedule availability (always ON)
    #=========================================================
    load_sche_nm="ALWAYS ON BLOAD"+suffix
    loadsche_temp, loadsche_defs = templ.HVACtemplate_schedule_alwaysON2()
    new_objs.insert(-1, idf_templater({'name': load_sche_nm}, loadsche_temp, loadsche_defs ) )

    # Zones to add baseload to
    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    # zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon if 'plenum' not in get_obj_name(myobj).lower()]
    # VD TODO: Repeat this block of code for other functions.
    # VD: Add specific zones if specified
    if 'zone_selective_add' in args:
        zone_selective_add = args['zone_selective_add']
        zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon if zone_selective_add in get_obj_name(myobj).lower()]
        # VD NOTE: Haven't tested this yet. For multiple zones requiring the same mass.
        # zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon if is_in(zone_selective_add, get_obj_name(myobj).lower()]
    # VD: Add to all except for specified zones
    elif 'zone_selective_all_except' in args:
        zone_selective_all_except = args['zone_selective_all_except']
        zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon if (zone_selective_all_except not in get_obj_name(myobj).lower() and 'plenum' not in get_obj_name(myobj).lower() ) ]
        # VD NOTE: Haven't tested this yet. For multiple zones requiring the same mass, except for a list.
        # zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon if not is_in(zone_selective_add, get_obj_name(myobj).lower()]
    # VD: Otherwise, apply to every zone
    else:
        zone_use_nms = [get_obj_name(myobj) for myobj in objs_zon]
    zones_add_bload= [myobj for myobj in objs_zon if get_obj_name(myobj) in zone_use_nms]

    #==============================
    # Template: ElectricalEquipment
    #==============================
    # Add extra baseload to all zones
    temp_bload, defs_bload = templ.Equipment_Baseload()
    baseload=float(load)
    j=1
    for i,obj in enumerate(objs_all):
        if obj in zones_add_bload:
            zone_nm = get_obj_name(obj)
            printc("Adding Misc Baseload ElectricEquipment to Zone: %s"%(mkcolor(zone_nm,'green')), "blue")
            d={
              'zone_name': zone_nm,
              'avail_sche': load_sche_nm,
              'load': "%.5f"%(frac*baseload),
              'enduse': enduse,
              'frac': frac,
              'suffix': suffix,
            }

            if 'frac_lost' in args: d['frac_lost'] = args['frac_lost']

            add_obj=idf_templater(d, temp_bload, defs_bload)
            new_objs.insert(i+j, add_obj)
            j=j+1

    return new_objs

def remove_DHW_loads_file(to_file=to_file):
    """Modified version of `remove_DHW_loads` which creates an IDF output for testing purposes. File output uses suffix `_rmDWHeq.idf` by default."""
    return __abstract_add_objs2file(remove_DHW_loads, to_file=to_file, suffix='rmDHWeq')

def remove_DHW_loads(objs_all, args={}):
    """Remove all DHW load related objects from genEPJ List.

    Types include: `WaterUse:Equipment, `Water Equipment`, and enduse schedules.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with DHW Loads removed (Python `List`)
    """
    new_objs=list(objs_all)

    new_objs= [obj for obj in new_objs if 'wateruse:equipment' not in get_obj_type(obj).lower()]
    new_objs= [obj for obj in new_objs if not (('schedule:compact' in get_obj_type(obj).lower()) and
                                               ('water equipment' in get_obj_name(obj).lower())) ]
    new_objs= [obj for obj in new_objs if not (('schedule:compact' in get_obj_type(obj).lower()) and
                                               ('apt_dhw_sch' in get_obj_name(obj).lower())) ]
    return new_objs

def add_DHW_loads_file(to_file=to_file, frac=1.0):
    """Modified version of `add_DHW_loads` which creates an IDF output for testing purposes. File output uses suffix `_DHWLoad.idf` by default."""
    return __abstract_add_objs2file(add_DHW_loads, to_file=to_file, suffix='DHWLoad')

# TODO- calc DHW use based on occupancy (presently by floor area)
#     - NOTE- Occupancy is also based on FA, just its better to know people #'s
#def add_DHW_loads(objs_all, frac=1.0, water_temp=43.3):
def add_DHW_loads(objs_all, args={ 'frac': 1.0, 'water_temp': 43.3, 'zones':[] }):
    """Add `WaterUse:Equipment` objects with temperatures and end-use schedule. Peak volume of water use determined by floor area (via SQL query). Adding `WaterUse:Equipment` objects is a prerequiste for DHW Tanks objects be to be added.


    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: Dictionary of default loop temperatures, ZoneList to add `WaterUse:Equipment` objects to, etc (Python Dict)

    Returns:

    * `new_objs`: genEPJ object list with newly added `WaterUse:Equipment` objects (Python `List`)
    """

    frac = args['frac']
    water_temp = args['water_temp']
    if 'zones' in args:
        zones = args['zones']
    else:
        zones = None

    if 'file_name' in args:
        global c
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    new_objs=list(objs_all)

    #objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')

    objs_zonlist=filter_IDF_objs_raw(objs_all, 'ZoneList')
    #print(objs_zonlist)
    zone_guestrm=[]
    if not zones: zones=['restroom']
    for nm in zones:
        printc("Adding Zone to DHW add list: %s"%(mkcolor(nm,'green')), "blue")
        zone_guestrm= zone_guestrm + extract_nms_from_zonelist(objs_zonlist, nm)

    ## SB: Get a list of thermal zones which meet a name criteria
    #objs_zonlist=filter_IDF_objs_raw(objs_all, 'ZoneList')
    #if 'Sifton' in to_file:
    #    zone_guestrm=extract_nms_from_zonelist(objs_zonlist, 'restroom')
    #elif '6A' in to_file:
    #    zone_guestrm=extract_nms_from_zonelist(objs_zonlist, 'mid-riseapartment apartment')
    #elif 'BID_L' in to_file:
    #    zone_guestrm=extract_nms_from_zonelist(objs_zonlist, 'restroom')
    #elif 'BID_B' in to_file:
    #    zone_guestrm=extract_nms_from_zonelist(objs_zonlist, 'restroom')
    #elif 'BID_Tower' in to_file:
    #    zone_guestrm1=extract_nms_from_zonelist(objs_zonlist, 'restroom')
    #    zone_guestrm2=extract_nms_from_zonelist(objs_zonlist, 'guestroom')
    #    zone_guestrm = zone_guestrm1 + zone_guestrm2
    #elif 'bldg' in to_file:
    #    zone_guestrm=extract_nms_from_zonelist(objs_zonlist, 'mid-riseapartment apartment')
    #else:
    #    zone_guestrm=extract_nms_from_zonelist(objs_zonlist, 'guestroom')
    #print("Zones to add DHW to:",zone_guestrm)
    print(zone_guestrm)

    obj_idx=-1

    new_objs.insert(obj_idx, '\n! generate_IDF.py: Adding DHW Profiles to IDF file\n')
    # Adding DHW relevant schedules
    #new_objs.insert(obj_idx, sche_dhw%(water_temp, water_temp))
    #new_objs.insert(obj_idx, sche_dhw%(frac, water_temp, water_temp))
    temp_dhwsch, defs_dhwsch=  templ.Schedule_DHWLoad()
    new_objs.insert(-1, idf_templater( {'frac': "%.1f"%(frac)}, temp_dhwsch, defs_dhwsch) )

    latsche_temp, latsche_defs = templ.HVACtemplate_schedule_alwaysON()
    d={
      'frac':       "0.05",
      'type':       "Fraction",
      'name':       "Apartment Water Equipment Latent fract sched",
    }
    new_objs.insert(-1, idf_templater(d, latsche_temp, latsche_defs ) )

    senssche_temp, senssche_defs = templ.HVACtemplate_schedule_alwaysON()
    d={
      'frac':       "0.2",
      'type':       "Fraction",
      'name':       "Apartment Water Equipment Sensible fract sched",
    }
    new_objs.insert(-1, idf_templater(d, senssche_temp, senssche_defs ) )

    watersche_temp, watersche_defs = templ.HVACtemplate_schedule_alwaysON()
    d={
      'frac':       "%.1f"%(water_temp),
      'type':       "Temperature",
      'name':       "Apartment Water Equipment Temp Sched",
    }
    new_objs.insert(-1, idf_templater(d, watersche_temp, watersche_defs ) )

    supplysche_temp, supplysche_defs = templ.HVACtemplate_schedule_alwaysON()
    d={
      'frac':       "%.1f"%(water_temp),
      'type':       "Temperature",
      'name':       "Apartment Water Equipment Hot Supply Temp Sched",
    }
    new_objs.insert(-1, idf_templater(d, supplysche_temp, supplysche_defs ) )

    for nm in zone_guestrm:
        printc("Adding WaterUse:Equipment to Zone: %s"%(mkcolor(nm,'green')), "blue")
        #base_DHW_use=6.198e-006*frac # m3/s
        ### FROM ASHRAE HVAC APPLICATIONS 2007 p14
        ## SB: Need to iterate over 'extract_schedules' until the numbers work out
        ### Apartment units
        ##units = [ 20, 50, 75, 100, 200]
        ##avg_daily = [42, 40, 38, 37, 35] # Gal/Apartment
        ##avg_daily = [ 158.9872956,  151.416472 ,  143.8456484,  140.0602366,  132.489413 ] # L/Apartment
        #base_DHW_use=6.198e-006*frac # m3/s
        #base_DHW_use=5.198e-006*frac # m3/s -> 190.6 L/day average across all units
        #if args.has_key('peak_use'):
        if 'peak_use' in args:
            base_DHW_use=float(args['peak_use'])*frac
        else:
            base_DHW_use=4.198e-006*frac # m3/s -> 153.9 L/day average across all units

        area_per_unit=100.0 # Assume 100m2 per unit
        ## Test print of BuildingSurf types
        objs_surf=filter_IDF_objs_raw(objs_all, 'BuildingSurface:Detailed')
        surf_zone=filter_surf_by_zone(objs_surf, nm)
        surf_zn_floor= _filter_surf_obj_by_type('Floor', surf_zone)
        #print("_FLOOR?",surf_zn_floor)
        surf_area=sum(_calc_areas(surf_zn_floor, 'Floor'))
        print('Floor Area for %s: %.2fm2'%(mkcolor(nm,'yellow'),surf_area))

        # Calc approx number of units
        units=surf_area/area_per_unit
        DHW_use=base_DHW_use*units
        print('Estimated # of Units in %s: %.1f; Peak DHW flow: %s'%(mkcolor(nm,'yellow'),units, str(DHW_use)))

        enduse_temp, enduse_defs = templ.Schedule_WaterUse()
        d={
          'zone_name': nm,
          'peak_flow': "%.5g"%(DHW_use),
          'frac': "%.1f"%(frac),
          'water_sche': "Apartment Water Equipment Temp Sched",
          'supply_sche': "Apartment Water Equipment Hot Supply Temp Sched",
          'lat_sche': "Apartment Water Equipment Latent fract sched",
          'sens_sche': "Apartment Water Equipment Sensible fract sched",
        }
        new_objs.insert(obj_idx, idf_templater(d, enduse_temp, enduse_defs ) )
        #new_objs.insert(obj_idx, temp_dhw_zone%(nm, DHW_use, frac,  nm))
        #new_objs = align_IDF_objs(new_objs)

    if options.debugdhw:
        new_objs.insert(-1, "Output:Variable,*,Water Use Equipment Heating Rate,timestep;")

    return new_objs


def add_vent_loads_file(to_file=to_file):
    """Modified version of `add_vent_loads` which creates an IDF output for testing purposes. File output uses suffix `_VENT.idf` by default."""
    return __abstract_add_objs2file(add_vent_loads, to_file=to_file, suffix='VENT')

# Ventilation includes:
# 1. Exhaust (exfiltration)
# 2. Infiltration
# 3. Ventilation
## TWO Approaches: Reference building, Proposed building
# NOTE: EPlus allows for the use of multiple ZoneVentilation:(DesignFlowRate) objects, vent is additive
def add_vent_loads(objs_all, args={ 'kitch':1, 'bath':2} ): # Number of kitches/bathrooms
    """Add Exhaust ventilation objects in bathrooms and kitchens. Primarily used in residential buildings. Assumed that ventilation should be added to mechanical and apartment spaces (`Zone` names need to reflect intended enduse).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with exhaust fan ventilation objects (Python `List`)
    """
    # ASHRAE 62.1: bathrooms: 20cfm continuous, kitchens: 5cfm continuous

    new_objs=list(objs_all)

    kitch= args['kitch']
    bath= args['bath']

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    # SB: Get a list of thermal zones which meet a name criteria
    objs_zonlist=filter_IDF_objs_raw(objs_all, 'ZoneList')
    ##zone_guestrm=extract_nms_from_zonelist(objs_zonlist, 'guestroom')
    #zone_guestrm=extract_nms_from_zonelist(objs_zonlist, 'restroom')
    zone_mech=extract_nms_from_zonelist(objs_zonlist, 'mechanical')
    #ASHRAE_90.1-2004 ClimateZone 1-8 Mid-riseApartment Apartment
    zone_guestrm=extract_nms_from_zonelist(objs_zonlist, ' apartment')
    print("Mech Zones:",zone_mech)

    obj_idx=-1

    new_objs.insert(obj_idx, '\n! generate_IDF.py: Adding Exhaust Profiles to IDF file\n')
    #=====================================
    # Template Vent Availability schedules
    #=====================================
    # Adding Exhaust relevant schedules
    # NOTE: 5cfm/unit CONTINUOUS
    ventavail_temp, ventavail_defs = templ.HVACtemplate_schedule_alwaysON()
    new_objs.insert(obj_idx, idf_templater({'name': "VentSchedCont"}, ventavail_temp, ventavail_defs ) )

    # Create a central zone file
    all_zones=list(zone_guestrm)
    all_zones.extend(zone_mech)

    printc("Adding ExhaustFans: Kitchen Fans %s, Bathroom Fans: %s"%(mkcolor(str(kitch),'yellow'), mkcolor(str(bath),'yellow')), "green")

    #=========================
    # Template ZoneVentilation
    #=========================
    # NOTE: 1cfm = 1/2118.88 m3/s
    zonevent_temp, zonevent_defs = templ.HVAC_ZoneVentilation()
    for nm in all_zones:
        printc("Adding ZoneVentilation:DesignFlowRate to Zone: %s"%(mkcolor(nm,'green')), "blue")

        ## Test print of BuildingSurf types
        area_per_unit=100.0 # Assume 100m2 per unit
        objs_surf=filter_IDF_objs_raw(objs_all, 'BuildingSurface:Detailed')
        surf_zone=filter_surf_by_zone(objs_surf, nm)
        surf_zn_floor= _filter_surf_obj_by_type('Floor', surf_zone)
        surf_area=sum(_calc_areas(surf_zn_floor, 'Floor'))
        print('Floor Area for %s: %.2fm2'%(mkcolor(nm,'yellow'),surf_area))

        # SB: TODO- units=1.0 is a hack to make this function run (June 2016). See april 28 note below
        units=1.0
        # Calc approx number of units
        if nm in zone_guestrm:
            # ASHRAE 62.1: bathrooms: 20cfm continuous, kitchens: 5cfm continuous
            #exh_use_per_unit=(2*20+5)/2118.88 # Convert units: cfm->m3/s
            exh_use_per_unit=(20.0*bath+5.0*kitch)/2118.88 # Convert units: cfm->m3/s
            #units=surf_area/area_per_unit; SB: removed April 28, 2015. Script iterates over each resi zone
            #exh_use=exh_use_per_unit*units
            #printc("ADD Exhaust: Identified %s Residential Units"%( mkcolor(units,'green')), "blue")
            exh_use=exh_use_per_unit*units
            deltaP=15*units # Assume fans have a deltaP of 15Pa per unit when all fans are one
            #deltaP=20 # Assume fans have a deltaP of 15Pa per unit when all fans are one
        elif nm in zone_mech:
            exh_use_per_unit=200.0/2118.88 # Conver units: cfm->m3/s
            exh_use=exh_use_per_unit # Only one fan in each mech room
            deltaP=300 # Assume fans have a deltaP of 15Pa per unit when all fans are one

        print('Estimated # of Units in %s: %.1f; Continuous Exhaust flow: %s'%(mkcolor(nm,'yellow'),units, exh_use))
        d={
           'name': nm+" Ventl",
           'zone_name': nm,
           'flow_rate': "%.6f"%(exh_use),
           'fan_pressure': deltaP,
        }
        new_objs.insert(obj_idx, idf_templater(d, zonevent_temp, zonevent_defs ) )

    return new_objs


def add_natural_ventilation_file(to_file=to_file):
    """Modified version of `add_natural_ventilation` which creates an IDF output for testing purposes. File output uses suffix `_NV.idf` by default."""
    return __abstract_add_objs2file(add_natural_ventilation, to_file=to_file, suffix='NV')

# SB NOTE: How to turn off heating during summer:
#  1. Create new daily heating schedule
#  2. Create weekly schedule from daily
#  3. Create Year schedule from weekly
def add_natural_ventilation(objs_all, args={}):
    """Add Natural Ventilation (ie. Free Cooling via E+ `ZoneVentilation:DesignFlowRate` objects)  to `Zones` with wall area >15m2 (via SQL Query).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with Natural Ventilation (Python `List`)
    """

    printc("Adding FREE COOLING ZoneVentilation:DesignFlowRate objects",'yellow')

    NV_sche="Night Free Cooling Schedule"

    new_objs=list(objs_all)


    obj_idx=-1

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    ZM_sql_sel = "SELECT ZoneName, OriginX, OriginY, OriginZ from Zones WHERE ExtGrossWallArea>15"
    ZM_nms_data=c.execute(ZM_sql_sel).fetchall()
    ZM_nms=map(lambda x: x[0], ZM_nms_data)
    NV_eff_rad=10 # meters: Add all zones within +-
    ZM_sql_sel_temp="SELECT ZoneName from Zones WHERE OriginZ=%.1f AND OriginX<%.1f AND OriginX>%.1f AND OriginY<%.1f AND OriginY>%.1f AND ZoneName!='%s'"

    #ZM_data=[]
    temp_ZM, defs_ZM=  templ.ZoneMixing()
    for i,nm in enumerate(ZM_nms):
        _nm,X,Y,Z=ZM_nms_data[i]
        mix_znms=c.execute(ZM_sql_sel_temp%(Z, X+NV_eff_rad,X-NV_eff_rad, Y+NV_eff_rad,Y-NV_eff_rad, nm ) ).fetchall()
        mix_znms=map(lambda x: x[0], mix_znms)
        #print(dat)
        print([_nm, nm, X,Y,Z])
        for n in mix_znms:
            #ZM_data.append( [nm, n] )
            printc("Adding ZoneMixing: %s->%s"%(mkcolor(nm,'green'), mkcolor(n,'yellow')), "blue")
            d={
               'zoneA': nm,
               'zoneB': n,
               'sche_name': NV_sche
            }
            new_objs.insert(-1, idf_templater( d, temp_ZM, defs_ZM) )

    all_zones=filter_IDF_objs_raw(objs_all, 'Zone')
    objs_filt_NV=[obj for obj in all_zones if is_in(ZM_nms, get_obj_name(obj).upper())]

    #new_objs.insert(obj_idx, '\n! generate_IDF.py: Adding Exhaust Profiles to IDF file\n')

    # Adding relevant Free Cooling schedules
    temp_NVsche, defs_NVsche=  templ.Schedule_NV()
    new_objs.insert(-1, idf_templater( {'sche_name': NV_sche}, temp_NVsche, defs_NVsche) )


    # NOTE: 1cfm = 1/2118.88 m3/s
    #for obj in all_zones:
    #============
    # Template NV
    #============
    temp_NV, defs_NV=  templ.NaturalVentilation()
    for obj in objs_filt_NV:
        nm=get_obj_name(obj)
        printc("Adding FREE COOLING ZoneVentilation:DesignFlowRate to Zone: %s"%(mkcolor(nm,'green')), "blue")
        #new_objs.insert(obj_idx, temp_zone_NV%(nm, nm))
        new_objs.insert(-1, idf_templater( {'sche_name': NV_sche, 'zone_name': nm}, temp_NV, defs_NV) )

    return new_objs


def add_window_shading_file(to_file=to_file):
    """Modified version of `add_window_shading` which creates an IDF output for testing purposes. File output uses suffix `_winshd.idf` by default."""
    return __abstract_add_objs2file(add_window_shading, to_file=to_file, suffix='winshd')
    #return __abstract_add_objs2file(add_window_shading, to_file=to_file, suffix='winshdext')
    #return __abstract_add_objs2file(add_window_shading, to_file=to_file, suffix='winshdint')

# TODO: Add '!- Frame and Divider Name'
# TODO: Add exterior shading by Unique Construction type
#def add_window_shading(objs_all):
def add_window_shading(objs_all, args={ 'shade_type': "ExteriorShade", 'max_temp': 25, 'max_sr': 500 } ):
    """Add Window Shading system to all `FenestrationSurface:Detailed` objects. Controller used to close blinds when room temperature exceeds a specfied value (default 25C) or solar radiation exceeds a given value (default 500W/m2).

    Allows comparison of interior vs exterior shading strategies

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `shade_type` user can specify interior/exterior shading and materials. `max_temp` close blinds when room temperature exceeds this value. `max_sr` close blinds when solar radiation hitting shade exceeds this value.

    Returns:

    * `new_objs`: genEPJ object list with Window Shading to all `FenestrationSurface:Detailed` objects (tested on Python version 8 only). (Python `List`)
    """
    ## Steps:
    # 0. Add Shading Objects
    #    . Add Shade Material
    #    . Add new Construction Glazing object (copy existing glazing objects)
    #      + Add shade construction into Window construction (on exterior if exteior, on interior if interior)
    #    . WindowProperty:ShadingControl object
    # 1. Filter all FenestrationSurface:Detailed (by Azimuth: South, East, West windows only)
    #    . foreach win: Add reference to WindowProperty:ShadingControl object in FenestrationSurface:Detailed
    shade_type=args['shade_type']
    max_temp=args['max_temp']
    max_sr=args['max_sr']

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    # WindowMaterial:Shade
    # WindowProperty:ShadingControl
    if max_sr==0 :
        printc("SHADING CONTROL W BLIND: Given zero for max SR! Nothing to do!", 'red')
        return objs_all

    #shade_type="InteriorShade"
    ##shade_type="ExteriorShade"

    obj_idx=-1
    new_objs=list(objs_all)

    new_objs.insert(obj_idx, '\n! generate_IDF.py: Adding Win Shading to IDF file\n')
    #================================
    # Template: Adding Shade Material
    #================================
    shade_temp, shade_defs = templ.Material_WindowShade()
    new_objs.insert(obj_idx, idf_templater({}, shade_temp, shade_defs ) )

    objs_filt_win=filter_IDF_objs_raw(new_objs, 'FenestrationSurface:Detailed')
    azi=180
    pm=180 # Grab all windows except north facing ones
    win_sql_sel='SELECT SurfaceName from Surfaces WHERE ClassName=="Window" AND Azimuth>%d AND Azimuth<=%d AND ExtBoundCond=0'
    win_names=c.execute(win_sql_sel%(azi-pm/2., azi+pm/2. )).fetchall()
    win_names=map(lambda x: x[0], win_names)
    objs_filt_win=[obj for obj in objs_filt_win if is_in(win_names,get_obj_name(obj).upper())]
    print("FOUND %d WINDOWS TO ADD SHADING TO!"%(len(objs_filt_win)))


    # SB: Get all unique window construction objects
    win_cons_nms= list( set(map(get_surf_cons_name, objs_filt_win)) )
    print( list(win_cons_nms))

    wincontr_temp, wincontr_defs = templ.WindowControl()
    for wcn in win_cons_nms:
        # Add Shade Material into the copied Window Construction obj
        win_cons_nm=wcn
        new_win_cons_nm=win_cons_nm+" "+shade_type
        objs_filt_cons=filter_IDF_objs_raw(new_objs, 'Construction')
        win_cons_objs=[obj for obj in objs_filt_cons if get_obj_name(obj).lower() == win_cons_nm.lower()]
        print("Win cons objects: ",win_cons_objs)
        win_cons_obj=win_cons_objs[0]
        win_cons_obj=win_cons_obj.replace(win_cons_nm, new_win_cons_nm)
        if 'Interior' in shade_type:
            win_cons_obj=win_cons_obj.replace(';', ',')+"\n  Shade;           !- Layer 4"
        else:
            win_cons_obj=win_cons_obj.replace('!- Name', '!- Name\n  Shade,           !- Layer 1')
        new_objs.insert(obj_idx, win_cons_obj)

        # Add WindowProperty:ShadingControl
        #  + For each window glazing construction?
        shdcntrl_nm='Shade Control '+ win_cons_nm
        #max_sr=500 # W/m2, Max solar radiation before blind deployment (only if temp is sufficiently high)
        #max_temp=25 # C, Max temp before blind deployment (only if SR is sufficiently high)
        printc("Adding Shading Control object '%s' using: Max SR: %.0f, Max Temp: %.0f"%(shdcntrl_nm, max_sr, max_temp), 'blue')
        d={
          'name': shdcntrl_nm,
          'type': shade_type,
          'constr_name': get_obj_name(win_cons_obj),
          'max_temp': "%.1f"%(max_temp),
          'max_SR': "%.0f"%(max_sr),
        }
        new_objs.insert(obj_idx, idf_templater(d, wincontr_temp, wincontr_defs ) )

    nm_regex=re.compile(r'[ ]*,[ ]+!- Shading Control Name')
    objs_iter=list(new_objs)
    for j,obj in enumerate(objs_iter):
        if ((obj in objs_filt_win) and ('interior' not in get_surf_cons_name(obj).lower())):
            nm=get_obj_name(obj)
            _shdcntrl_nm='Shade Control '+get_surf_cons_name(obj)
            printc("Adding Shading Control '%s' to FenestrationSurface: %s"%(mkcolor(new_win_cons_nm,'yellow') ,mkcolor(nm,'green')), "blue")
            nmline=nm_regex.findall(obj)[0]
            myobj=obj.replace(nmline, "    %s,      !- Shading Control Name"%(_shdcntrl_nm))
            #myobj=myobj.replace(win_cons_nm, new_win_cons_nm) # SB: Step isn't necessary!
            new_objs[j]= myobj

    if options.debugshade:
        printc("Adding Shading specific Output Variables", 'yellow')

        temp_output, output_defs =templ.template_output()

        output_vars=[
          'Surface Shading Device Is On Time Fraction',
          'Surface Window Shading Device Absorbed Solar Radiation Rate',
        ]

        for v in output_vars:
            new_objs.insert(obj_idx, idf_templater( {'name': v}, temp_output, {} ) )


    return new_objs

def add_Daylight_zones_file(to_file=to_file):
    """Modified version of `add_Daylight_zones` which creates an IDF output for testing purposes. File output uses suffix `_DayL.idf` by default."""
    return __abstract_add_objs2file(add_Daylight_zones, to_file=to_file, suffix='DayL')

# NOTE/TODO- SLOW: Block of code below is VERY slow
#   * Likely double for loops that is killing me: [ for i in ii for k in kk if ...]
#TODO- Add reference in 'Lights,' which allows for dimmable controls (0/1: On,Off) (Field FractionReplacable)
#TODO- Fix coordinates of sensor in opposing wall (Presently [0,0,0])
#      * PLACE sensor: 0.5*x, 0.5*y, 0.8
#      OR
#      * PLACE 2 sensors: [0.5*x, 0.25*y, 0.8] AND  [0.5*x, 0.75*y, 0.8]
#TODO- Debug total # of zones with daylighting oppotunities (100% seems doubtful)
#TODO- Try and use DELight controls instead of Daylighting:Controls
def add_Daylight_zones(objs_all, args={}):
    """Add `Daylighting:Control` objects to `Zones`. Use is considered *experimental* due to issues to coordinate calculations.


    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `file_name` is the IDF file to base SQL query bases on (ie, `'s/.idf/.sql/`)

    Returns:

    * `new_objs`: genEPJ object list with newly added `Daylighting:Control` objects (Python `List`)
    """

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    xy_sql_sel='SELECT ZoneName,MinimumX,MaximumX,MinimumY,MaximumY from Zones;'
    zone_xy_nm=c.execute(xy_sql_sel).fetchall()

    new_objs=list(objs_all)

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    zone_nms = [get_obj_name(myobj) for myobj in objs_zon if 'plenum' not in get_obj_name(myobj).lower()]
    objs_filt_win=filter_IDF_objs_raw(objs_all, 'FenestrationSurface:Detailed')
    objs_filt_surf=filter_IDF_objs_raw(objs_all, 'BuildingSurface:Detailed')
    objs_filt_wall= [surf for surf in objs_filt_surf if get_surf_type(surf)=='Wall']
    objs_filt_flr = [surf for surf in objs_filt_surf if get_surf_type(surf)=='Floor']

    # GET exterior wall surface name (with a window in it)
    # GET zone name with exterior wall AND window in it
    wall_with_windows=[wl for wl in objs_filt_wall for win_obj in objs_filt_win if get_obj_name(wl) == get_obj_abstract(win_obj,4)]
    zones_with_windows=[zn for zn in objs_zon for wl_obj in wall_with_windows if get_obj_name(zn) == get_obj_abstract(wl_obj,4)]
    print([get_obj_name(wl) for wl in wall_with_windows])
    #print(zones_with_windows)

    # SQL: get direction of largest window area in zone
    sql_get_azi='SELECT a.Azimuth FROM Surfaces as a, Zones as b WHERE a.ClassName=="Window" AND b.ZoneIndex=a.ZoneIndex AND b.ZoneName="%s" ORDER BY a.GrossArea DESC LIMIT 1'
    ignore_illum_map=['Corridor', 'Stairs', 'WashRm', 'Tower', 'Showers', 'Mechanical', 'Retail']

    j=0
    zns_with_daylight_cntrl=[]
    for i,obj in enumerate(objs_all):
        if ((obj in zones_with_windows) and (obj not in zns_with_daylight_cntrl)):
            #get zone object name
            zone_nm=get_obj_name(obj)
            printc("\nAdding 'Daylighting:Control' to zone: %s"%(mkcolor(zone_nm,'yellow')), 'green')
            #print("Index:",i+j+1)

            # Calculate positioning of daylight sensors for the given zone
            #  GET surface name which has the window in it
            wall_obj=[wl for wl in wall_with_windows if zone_nm in wl]
            flr_obj =[fl for fl in objs_filt_flr if zone_nm in fl]
            if len(flr_obj)>1 :
                printc("WARNING: Found multiple floor objects for zone: %s"%(zone_nm), 'yellow')
            wall_nm=get_obj_name(wall_obj[0])
            printc("Found wall surface with window: %s"%(mkcolor(wall_nm,'yellow')), 'green')
            win_obj =[wn for wn in objs_filt_win if wall_nm in wn]
            printc("Found %d window surface(s) associated to wall %s"%(len(win_obj),mkcolor(wall_nm,'yellow')), 'green')
            wall_coor=_get_surf_coordin(wall_obj[0])
            wall_coor=array(wall_coor)
            win_coor=_get_surf_coordin(win_obj[0])
            win_coor=array(win_coor)
            flr_coor=_get_surf_coordin(flr_obj[0])
            flr_coor=array(flr_coor)
            zn_coor=_get_surf_coordin(obj)
            print("Wall Coor:",wall_coor)
            print("Win Coor:",win_coor)
            #print("Zone Coor:",zn_coor)
            print("Floor Coor:",flr_coor)

            # METHOD 4: Calc from 0.5*width (same axis as ext win) and 0.5*depth vectors
            #  1. Find vector a (same axis as exterior window), take 1/2
            #  2. Find vector b or depth vector, take 1/2
            #  3. Add them
            # Show rotational properties of the space (useful for QA)
            a=array(flr_coor[0,:])
            b=array(flr_coor[1,:])
            theta_a=arctan( a[1]/a[0] )
            theta_b=arctan( b[0]/b[1] )
            if theta_a!=theta_b:
                printc("Angles off x,y axis are not equal (x, y): (%.2f, %.2f)"%(theta_a*180./pi, theta_b*180./pi), "yellow")
            # Works since floor coordinates always have a (0,0,0) basis [ie no scaling required]
            t=win_coor[0,:]
            r=win_coor[3,:]
            #k=(t+(r-t)/2.)
            k=(r-t) #window vector at height h2
            print("win vector:",k)
            # Cross product is zero only if vector lie on the same access
            flr_win_vec=[x for x in flr_coor if ((len3D(x)>0.8) and (len3D(cross3D(x,k))<=5.0))]
            #flr_win_vec=[x for x in flr_coor if (len3D(x)>0.8)]
            ## TRICK: no guarantee coordinates are exactly ||, sort by vec len to find shortest
            #print("flr_win vector (all):",flr_win_vec)
            #def mylencross(x): return map(lambda o: len3D(cross3D(o,k)), x)
            #def mylencross(x): return len3D(cross3D(x,k))
            #sorted(flr_win_vec, mylencross)
            #flr_win_vec.sort(mylencross)
            print("flr_win vector (cross 0):",flr_win_vec)
            # If not in null cross-product set, it's a depth vector
            #flr_depth_vec=[y for x in flr_win_vec for y in flr_coor if ((y[0]!=x[0]) and (y[1]!=x[1]) and (y[2]!=x[2]))]
            #flr_depth_vec=[y for x in flr_win_vec for y in flr_coor if str(y)!=str(x)]
            try:
                flr_depth_vec=[y for y in flr_coor if ((str(y)!=str(flr_win_vec[0])) and (len3D(y)>0.8))]
                print("flr_depth vectors:",flr_depth_vec)
                dayl_vec=0.5*flr_win_vec[0]+0.5*flr_depth_vec[0]
            except IndexError:
                printc("ERROR! Unable to ID depth vector in zone: %s"%(zone_nm), "red")
                flr_win_vec=None
                dayl_vec=array([0.0,0.0,0.8])

            # Method 5: Use SQL database
            x1,y1=calc_centroid(obj, c)
            dayl_vec=[x1,y1,0.8]


            ## Desk height is typically 0.8m (E+ Input/Output reference)
            x,y,z=dayl_vec[0], dayl_vec[1], 0.8
            print("Using coordinates [%f,%f,%f] for daylight sensor"%(x,y,z))
            flr_win_vec=1

            # INSERT daylight object in to list
            temp_daylight, defs_daylight = templ.DaylightControl()
            if flr_win_vec:
                #azi=0
                # SQL: get direction of largest window area in zone
                azi=c.execute(sql_get_azi%(zone_nm.upper())).fetchone()[0]
                print("%s: Found Azimuth: %.1f "%(zone_nm,azi))
                d={
                  'zone_name': zone_nm,
                  'x': "%.3f"%(x),
                  'y': "%.3f"%(y),
                  'z': "%.3f"%(z),
                  'glare_azi': "%.1f"%(azi),
                }
                new_objs.insert(i+j+1, idf_templater( d, temp_daylight, defs_daylight) )
                zns_with_daylight_cntrl.append(obj)
                #Need to use j to inject AFTER the next themal zone

                j=j+1

    temp_output, output_defs =templ.template_output()
    if options.debuglight:
        # Adding daylighting performance maps

        #Reports hourly daylight factors for each exterior window for four sky types
        new_objs.insert(-1, "Output:DaylightFactors,SizingDays;")

        output_vars=[
            "Daylighting Reference Point Illuminance",
            "Daylighting Lighting Power Multiplier",
        ]

        for v in output_vars:
            new_objs.insert(-1, idf_templater( {'name': v}, temp_output, {} ) )

    printc("Added 'Daylighting:Control' to %d/%d zone(s)"%(len(zns_with_daylight_cntrl),len(objs_zon)), 'yellow')
    return new_objs


def add_site_BC_file(to_file=to_file):
    """Modified version of `add_site_BC` which creates an IDF output for testing purposes. File output uses suffix `_siteBC.idf` by default."""
    return __abstract_add_objs2file(add_site_BC, to_file=to_file, suffix='siteBC')

# TODO- Check that GroundTemp objects on a single line doesnt screw up comment removal or auto-classifying of objs
def add_site_BC(objs_all, args={}):
    """Add `Site:GroundTemperature` objects for Building (site boundary conditions (BC)). Extracts average temperature profiles from EPW data (offset ground temperature based on average air temperatures).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with `Site:GroundTemperature` set based on specified weather data (Python `List`)
    """

    printc("Adding Boundary Condition Objects", 'green')
    new_objs=list(objs_all)
    len_all=len(new_objs)

    # ID where in file existing BC objects are
    obj_idxs = [i for i,obj in enumerate(objs_all) if get_obj_type(obj)=='Site:GroundTemperature:BuildingSurface']
    if obj_idxs:
        obj_idx = obj_idxs[0] # Take first occurrence of BC object
    else:
        obj_idx=-1 # No objects found. Append to end of file

    # Remove existing BCs if present:
    #  1. Ground temperatures
    new_objs= [obj for obj in objs_all if 'site:groundtemperature:deep' not in get_obj_type(obj).lower()]
    new_objs= [obj for obj in objs_all if 'site:groundtemperature:buildingsurface' not in get_obj_type(obj).lower()]
    #  2. Water main temperatures
    new_objs= [obj for obj in objs_all if 'site:watermainstemperature' not in get_obj_type(obj).lower()]
    #  3 ...
    printc("Removed %d BC objects!\n"%(len_all-len(new_objs)), 'yellow')

    # Load relevant details from weather file
    epwinfo = {
      #0: "Year",
      1: "Month",
      #2: "Day",
      #3: "Hour",
      6: "Dry Bulb Temperature, C",
      #14: "Direct Normal Radiation, Wh/m2",
      #15: "Diffuse Horizontal Radiation, Wh/m2",
      #22: "Wind Speed, m/s",
    }
    #wfile='/home/sb/energyplus/EnergyPlus-8-1-0/WeatherData/CAN_ON_Ottawa.716280_CWEC.epw'
    wfile_dir = environ['ENERGYPLUS_WEATHER']
    wfile=wfile_dir+'/CAN_ON_Ottawa.716280_CWEC.epw'
    data = loadtxt( wfile, delimiter=",", usecols=epwinfo.keys(), skiprows=8)
    # Setting up monthly t_db data
    t_db_mnth=[[],[],[],[],[],[],[],[],[],[],[],[]]
    junk=[t_db_mnth[int(mnth)-1].append( tdb ) for mnth,tdb in data]
    t_db=data[:,1]
    t_db_avg=average(t_db)
    t_grnd_deep = [t_db_avg]*12
    t_grnd_shal= map(average, t_db_mnth)
    t_grnd_shal= deque(t_grnd_shal)
    # Rotate array by 3, meaning a three month delay to avg grnd temps
    t_grnd_shal.rotate(3)


    # Site BCs:
    #  1. Shallow/Deep Ground temperatures
    # Defined as the average monthly ground temperature, delayed by 3 months
    grnd_deep_temp="""
  Site:GroundTemperature:Deep,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f;
"""

    # Defined as the average annual ground temperature
    grnd_shal_temp="""
  Site:GroundTemperature:BuildingSurface,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f;
"""

    printc("Adding Ground Temperature BCs", 'blue')
    #print(t_grnd_deep, t_grnd_shal )
    # TODO- Better way to unpack x12 arrays into template
    new_objs.insert(obj_idx, grnd_deep_temp%(t_grnd_deep[0], t_grnd_deep[1], t_grnd_deep[2], t_grnd_deep[3], t_grnd_deep[4], t_grnd_deep[5], t_grnd_deep[6], t_grnd_deep[7], t_grnd_deep[8], t_grnd_deep[9], t_grnd_deep[10], t_grnd_deep[11]))
    new_objs.insert(obj_idx, grnd_shal_temp%(t_grnd_shal[0], t_grnd_shal[1], t_grnd_shal[2], t_grnd_shal[3], t_grnd_shal[4], t_grnd_shal[5], t_grnd_shal[6], t_grnd_shal[7], t_grnd_shal[8], t_grnd_shal[9], t_grnd_shal[10], t_grnd_shal[11]))


    #  2. Humidity capacitance factors
    #  3. Vacation days (load from CSV)

    return new_objs

def add_condfd_file(to_file=to_file):
    """Modified version of `add_condfd` which creates an IDF output for testing purposes. File output uses suffix `_condfd.idf` by default."""
    return __abstract_add_objs2file(add_condfd, to_file=to_file, suffix='condfd')

# Set conduction finite difference as HeatBalanceAlgorithm
def add_condfd(objs_all, args={}):
    """Add `ConductionFiniteDifference` as the `HeatBalanceAlgorithm`. Place after `SimulationControl` object in IDF if possible.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with CFD specified (Python `List`)
    """

    new_objs= list(objs_all)

    temp_hbCFD, defs_hbCFD=templ.Simulation_HeatBalanceCFD()

    # replace existing (if any)
    printc("Setting FiniteDifference as HeatBalanceAlgorithm:",'blue')
    try:
        obj_hb_idx= [i for i,obj in enumerate(new_objs) if get_obj_type(obj).upper()=='HEATBALANCEALGORITHM'][0]
        new_objs[obj_hb_idx] = "HeatBalanceAlgorithm,ConductionFiniteDifference;"
    except:
        new_objs.insert(-1, "HeatBalanceAlgorithm,ConductionFiniteDifference;")
    #HeatBalanceAlgorithm,ConductionTransferFunction,200;

    # Add FD control directly after SimulationControl object
    obj_sc_idx= [i for i,obj in enumerate(new_objs) if get_obj_type(obj).upper()=='SIMULATIONCONTROL'][0]
    printc("Adding FiniteDifference settings: %s"%(mkcolor('HeatBalanceSettings:ConductionFiniteDifference','green')),'blue')
    new_objs.insert(obj_sc_idx+1, idf_templater( {}, temp_hbCFD, defs_hbCFD) )

    return new_objs

def get_timesteps(objs_all):
    """Helper function which returns E+ `Timestep`. Used to modify timestep in `mod_timesteps` (know which line to replace).
    """
    obj_ts_idx= [i for i,obj in enumerate(objs_all) if get_obj_type(obj).upper()=='TIMESTEP']
    if len(obj_ts_idx)>1 :
        # Intentially do nothing
        printc("ERROR! Found more than one 'Timestep' object", "red")
    elif len(obj_ts_idx)==0 :
        printc("ERROR! No 'Timestep' object found", "red")
    else:
        obj=objs_all[obj_ts_idx[0]]
        obj = trim_comments( recursive_strip(obj) )
        ts=int( obj.split(',')[1].replace(';','') )
#    try:
#    # Added in support of OS version 1.4
#    except:
#        ts=
    return ts

def mod_timesteps_file(to_file=to_file):
    """Modified version of `mod_timesteps` which creates an IDF output for testing purposes. File output uses suffix `_modTS.idf` by default."""
    return __abstract_add_objs2file(mod_timesteps, to_file=to_file, suffix='modTS')

def mod_timesteps(objs_all, args={ "new_TS": 4 } ):
    """Modify `Timestep` in specified `Building`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `new_TS` New timestep for simulation (default 4 timesteps per hour, or once per 15min)

    Returns:

    * `new_objs`: genEPJ object list with modified `Timestep` (Python `List`)
    """

    new_objs=list(objs_all)

    # RESET number of timesteps
    #new_ts=1
    #new_ts=20
    new_TS=args['new_TS']
    new_ts=new_TS
    obj_ts_idx= [i for i,obj in enumerate(new_objs) if get_obj_type(obj).upper()=='TIMESTEP']
    #=============================
    # Template for TIMESTEP object
    #=============================
    temp_timestep, defs_timestep = templ.template_timestep()
    timestep_formatted = idf_templater( {'timestep': new_ts}, temp_timestep, defs_timestep)
    if len(obj_ts_idx)>1 :
        # Intentionally do nothing
        printc("ERROR! Found more than one 'Timestep' object", "red")
        exit(1)
    elif len(obj_ts_idx)==1 :
        obj_ts_idx=obj_ts_idx[0]
        printc("Found existing Timestep: %d"%(get_timesteps(objs_all)), 'blue')
        printc("Changing Time step to: %d"%(new_ts), 'blue')
        new_objs[obj_ts_idx]=timestep_formatted
    else:
        obj_ts_idx=-1
        new_objs.insert(3, timestep_formatted)

    return new_objs

def add_PCM_file(to_file=to_file):
    """Modified version of `add_PCM` which creates an IDF output for testing purposes. File output uses suffix `_PCM.idf` by default."""
    return __abstract_add_objs2file(add_PCM, to_file=to_file, suffix='PCM')

# TODO: No present method to comment out PCM construction (must be defined in template file)
#  SB: Link this within the code? Not friendly for window users... Better to glob for in templates dir?
# NOTE: Challenge:
#  1. Ceiling/Floor constructions must match each other exactly
#  2. Name of PCM material in prop template must match that spec'd in this file
#     OR just specify PCM properties in template file (purge if not used)
def add_PCM(objs_all, args={'new_TS': 20}):
    """Add Phase Change Materials (PCM) to specified `Construction` via `use_PCM`. Forces Finite Difference in solver.
    Appropriate `Materials` and `Construction` objects must be provided in user templates via `sim/templates/prop_constructions_materials.idf`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with PCM added (Python `List`)
    """

    printc("Adding PCM to building surfaces", 'green')
    new_objs=list(objs_all)


    new_TS=args['new_TS']
    # Add FD control directly after SimulationControl object
    temp_hbCFD, defs_hbCFD=templ.Simulation_HeatBalanceCFD()
    obj_sc_idx= [i for i,obj in enumerate(new_objs) if get_obj_type(obj).upper()=='SIMULATIONCONTROL'][0]
    printc("Adding FiniteDifference settings: %s"%(mkcolor('HeatBalanceSettings:ConductionFiniteDifference','green')),'blue')
    new_objs.insert(obj_sc_idx+1, idf_templater( {}, temp_hbCFD, defs_hbCFD) )


    # Get idx of last Construction, put PCM list after this
    obj_cons_idx= [i for i,obj in enumerate(new_objs) if get_obj_type(obj).upper()=='CONSTRUCTION'][-1]
    #=================================
    # Template for PCM SurfaceProperty
    #=================================
    temp_PCMprop, defs_PCMprop=templ.Material_PCMSurfaceProperty()
    use_PCM=[
             #"AllInteriorWalls",
             "AllInteriorCeilings",
             "AllInteriorFloors",
             #"AllInteriorSurfaces",
            ]
    index=1
    for ii,nm in enumerate(use_PCM):
        printc("Adding PCM list for: %s"%(mkcolor(nm,'green')), "blue")
        d={
          'surf_num': "%s"%(ii+1),
          'surf_type': nm,
        }
        new_objs.insert(obj_cons_idx+index, idf_templater(d, temp_PCMprop, defs_PCMprop) )
        index=index+1

    # Modify timesteps: condFD needs 20+ TS per hour
    new_objs = mod_timesteps(new_objs, {'new_TS': new_TS})

    # Add construction objects (only if not previously inserted)
    objs_cons=[obj for obj in new_objs if get_obj_type(obj)=='Construction']
    idx_PCM_cons=[obj for obj in objs_cons if 'PCM' in get_obj_name(obj)]
    if len(idx_PCM_cons)==0 :
        # Adding Constructions/Materials from Template file
        from_file='templates/prop_constructions_materials.idf'
        objs_all_fr=get_IDF_objs_raw(from_file)
        if len(objs_all_fr)<1 :
            ValueError("Unable to find objects in file ",from_file)
        new_objs = copy_IDF_constr(objs_all_fr, new_objs)

    return new_objs


def add_elevator_file(to_file=to_file):
    """Modified version of `add_elevator` which creates an IDF output for testing purposes. File output uses suffix `_ELEV.idf` by default."""
    return __abstract_add_objs2file(add_elevator, to_file=to_file, suffix='ELEV')

def add_elevator(objs_all, args={'frac':1.0}):
    """Add `Elevator` to specified `Zones` using E+ `Exterior:FuelEquipment` object.
    Assumed that a 20HP elevator is used with a 91% efficient electric motor with a preset schedule.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `frac` of base elevator performance to simulate an elevator upgrade.

    Returns:

    * `new_objs`: genEPJ object list with Elevator added (Python `List`)
    """

    new_objs=list(objs_all)

    # VD NOTE: Added a fractional component (XXX: Hack: to remove afterwards)
    frac=args['frac']

    elev_hp=20
    elev_W=elev_hp*745.69987*frac # In Watts (1hp=745.69987W)
    elev_eff=0.91
    printc("Adding %.0f HP @%.0f eff Elevator to building"%(elev_hp, elev_eff*100), 'green')

    d={
      'elev_name': "Elevators",
      'sche_name': "BLDG_ELEVATORS",
      'power': "%.3f"%(elev_W/elev_eff),
    }

    idx_eleceq=[i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='ElectricEquipment']
    try:
        use_idx=idx_eleceq[-1]
    except:
        use_idx=-1
    printc("Adding: Exterior:FuelEquipment object",'blue')
    temp_elev, defs_elev=  templ.Equipment_ExteriorElevators()
    new_objs.insert(use_idx+1, idf_templater( d, temp_elev, defs_elev) )

    # NOTE- Based on a Hotel/Commercial/... schedule
    printc("Adding Elevator Schedule: %s"%(mkcolor("BLDG_ELEVATORS",'green')),'blue')
    temp_elevsch, defs_elevsch=  templ.Schedule_Elevators()
    new_objs.insert(use_idx+2, idf_templater( d, temp_elevsch, defs_elevsch) )

    return new_objs

def add_ExtShading_file(to_file=to_file):
    """Modified version of `add_ExtShading` which creates an IDF output for testing purposes. File output uses suffix `_ExtShd.idf` by default."""
    return __abstract_add_objs2file(add_ExtShading, to_file=to_file, suffix='ExtShd')

# TODO: Expand to work with any Azimuth (presently ONLY windows due south)
# NOTE: Doesn't require presim since window names don't change with rediminsioning
#def add_ExtShading(objs_all, args={ 'wid': 0.76, 'file_name': to_file } ):
def add_ExtShading(objs_all, args={ 'wid': 0.76} ):
    """Add Exterior Shading (`Shading:Zone:Detailed`) objects to all windows.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `wid` Width of Exterior window overhangs.

    Returns:

    * `new_objs`: genEPJ object list with newly added Exterior Shading objects (Python `List`)
    """

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    if 'wid' not in args: # Override by ExtShading_file
        args['wid']=0.76

    wid=args['wid']
    if wid==0 :
        printc("EXT SHADING: Given zero overhang width! Nothing to do!", 'red')
        return objs_all

    # SB- TODO- refactor to Template
    temp_extshd="""
  Shading:Zone:Detailed,
    %s Overhang,     !- Name
    %s,                 !- Base Surface Name
    ,               !- Transmittance Schedule Name
    %d,              !- Number of Vertices
"""
    temp_coor="    %.6f,%.6f,%.6f,  !- X,Y,Z ==> Vertex %d {m}"

    new_objs=list(objs_all)

    objs_filt_win=filter_IDF_objs_raw(new_objs, 'FenestrationSurface:Detailed')

    ## Get all windows surfaces by Azimuth
    pm=2 # pm in degress
    azi=180
    win_sql_sel='SELECT SurfaceName from Surfaces WHERE ClassName=="Window" AND Azimuth>=%d AND Azimuth<=%d AND ExtBoundCond=0'
    win_names=c.execute(win_sql_sel%(azi-pm/2., azi+pm/2. )).fetchall()
    win_surf_nms=map(lambda x: x[0], win_names)
    print("Matched Windows to add ext static shading: ",win_surf_nms)
    objs_win=[obj for obj in objs_filt_win if is_in(win_surf_nms, get_obj_name(obj).upper())]

    printc("Adding Exterior Static Shading objects on %s surfaces"%(mkcolor(str(len(objs_win)),'yellow')),'green')
    obj_idx=-1

    # NOTE: Doesnt work for generic directions
    temp_shadezone, defs_shadezone=  templ.ShadingZoneDetailed()
    for obj in objs_win:
        # STEPS:
        # 1. get coordinates of window (x1y1, x2y2)
        # 2. calc new coordinate of shading overhang
        # 3. form the new coordinate array
        coor=_get_surf_coordin(obj)
        if len(coor)>4 :
            printc('Warning!: More than 4 coordinates found for surface: %s'%(get_obj_name(obj)),'red')

        # HACK! works for south surfaces only
        if coor[0][1]==0 :
            base_nm=get_obj_abstract(obj, 4)
            #print("Coordinates: ",coor)
            # positions 0,3 stay identical (max height of window)
            new_coor = array(coor)
            new_coor[1]= new_coor[0]
            new_coor[1][1]= new_coor[1][1]-wid #neg since into y-axis
            new_coor[2]= new_coor[3]
            new_coor[2][1]= new_coor[2][1]-wid #neg since into y-axis
            #print("New Coordinates: ",new_coor)
            #shd_obj=temp_extshd%(get_obj_name(obj), base_nm, len(coor))
            d={
              'name': get_obj_name(obj),
              'surf_name': base_nm,
              'vert': len(coor),
            }
            shd_obj = idf_templater( d, temp_shadezone, defs_shadezone)
            coors_txt=[]

            for i,c in enumerate(new_coor):
                pass
                c=temp_coor%(new_coor[i][0], new_coor[i][1], new_coor[i][2], i+1)
                if i==3 :
                    c=c.replace(',  ',';  ')
                coors_txt.append(c)
            printc("Adding 'Shading:Zone' to Window: %s"%(mkcolor(get_obj_name(obj),'green')), 'blue')
            new_objs.insert(obj_idx, shd_obj+'\n'.join(coors_txt))


    return new_objs


def mod_wintype_file(to_file=to_file, wintypes=['TGLEAR','TGLEAR','DGLEAR','TGLEAR']):
    """Modified version of `mod_wintype` which creates an IDF output for testing purposes. File output uses suffix `_WinType.idf` by default."""
    return __abstract_add_objs2file(mod_wintype, to_file=to_file, suffix='WinType')

# SB TODO: Load in WindowProperty:FrameAndDivider if specified in COMMONWIN.csv file
def mod_wintype(objs_all, args={ 'wintypes': ['TGLEAR','TGLEAR','DGLEAR','TGLEAR'], 'use_win7': feat_dict['use_win7']} ):
    """Modify construction type of `FenestrationSurface:Detailed` objects to all windows.


    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `wintypes` Python `List` of window constructions for each cardinal direction `[north, east, south, west]` (templates located in `sim/templates`),`use_win7` Flag to use LBL Window templates ([site](https://windows.lbl.gov/software/window/)) instead of default E+ constructions.

    Returns:


    * `new_objs`: genEPJ object list with newly added Exterior Shading objects (Python `List`)
    """
    ## Steps:
    #   1. Add relevant Window constructions
    #   2. Get windows by Azimuth
    #   3. Substitute Construction of each window by direction

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    wintypes = args['wintypes']
    use_win7 = args['use_win7']

    printc("\nModifying window types by direction", "green")
    new_objs=list(objs_all)

    obj_cons_idx= [i for i,obj in enumerate(new_objs) if get_obj_type(obj).upper()=='CONSTRUCTION'][-1]
    index=1
    unique_wintypes=list(set(wintypes))

    if use_win7 :
        unique_wintypes.insert(0,'COMMONWINwin7') #Load up common window materials (Argon gas, etc)
    else:
        unique_wintypes.insert(0,'COMMONWIN') #Load up common window materials (Argon gas, etc)

    for wt in unique_wintypes:
        cons_file='templates/%s.csv'%(wt)
        objs_all_cons=get_IDF_objs_raw(cons_file)
        if len(objs_all_cons)<1 :
            ValueError("Unable to find objects in file ",cons_file)
        ## Remove pre-existing materials
        #set_new=set(map(lambda x: x.strip(), objs_all_cons))
        #set_idf=set(map(lambda x: x.strip(), new_objs))
        #objs_add=list( set_new-set_idf)
        #print("\n".join(objs_add))
        #new_objs.insert(obj_cons_idx+index, "\n\n".join(objs_add))
        #
        # Found previous Construction material?
        obj_cons_nm = [get_obj_name(obj) for i,obj in enumerate(new_objs) if (get_obj_type(obj).upper()=='CONSTRUCTION' or ('WINDOWMATERIAL' in get_obj_type(obj).upper()) )]
        print("TEST: Prev Cons Names: ", obj_cons_nm)
        # SB: Cant use wt... COMMONWIN isnt an object
        found_wt = list( map(get_obj_name, objs_all_cons) )[0] 
        print("TEST: Found existing construction object: ", found_wt)
        if is_in2(obj_cons_nm, found_wt):
            printc("Found previous Construction definition for '%s' Window Type"%(wt), "yellow")
        else:
            printc("Inserting '%s' Window Type"%(wt), "blue")
            new_objs.insert(obj_cons_idx+index, "\n\n".join(objs_all_cons))
            ## Remove pre-existing materials
            index=index+1

    # Reload newly joined construction objects into a list again
    new_objs=get_IDF_objs_raw(new_objs)
    objs_filt_frame=filter_IDF_objs_raw(new_objs, 'WindowProperty:FrameAndDivider')

    if len(objs_filt_frame)>0 :
        # Found a Frame and Divider property. Want its name to load into FenestrationSurface:Detailed objects
        frame_div_nm=get_obj_name(objs_filt_frame[0])
        printc("Found a 'WindowProperty:FrameAndDivider' object: %s"%(frame_div_nm),'yellow')
    else:
        frame_div_nm=None

    objs_filt_win=filter_IDF_objs_raw(objs_all, 'FenestrationSurface:Detailed')
    objs_filt_surf=filter_IDF_objs_raw(objs_all, 'BuildingSurface:Detailed')

    pm_azi=45 # Plus/Minus of Azimuth (Gets N,E, S ,W)
    win_sql_sel='SELECT SurfaceName from Surfaces WHERE ClassName=="Window" AND Azimuth>%d AND Azimuth<=%d AND ExtBoundCond=0'
    # Special select statement required for north face
    win_sql_sel_north='SELECT SurfaceName from Surfaces WHERE ClassName=="Window" AND Azimuth>=0 AND Azimuth<=%d OR Azimuth>=%d'
    mod_win_objs=[]
    def fix_angle(myang):
        if myang<0 : return myang+360
        else: return myang
    # Directions of Window Types: [north, east, south, west]
    cons_regex=re.compile(r'[\w\d.-]*,[ ]+!- Construction Name')
    frame_regex=re.compile(r'[\w\d.-]*,[ ]+!- Frame and Divider Name')
#myre = re.compile(r'[\n]*[\w\t\s\d\/.{}\(\)\[\]+,\'\n%=><#*:!@-]+;[ \t\w\d\/.{}\[\]\(\)%=><#+,:\?!@-]*')

    no_add_list=['Tower', 'Stairs']

    mycons_nm=""
    for idx,wtype in enumerate(wintypes):
    #for wn in objs_filt_win:
        azi=idx*90.
        if (azi-pm_azi)<=0 :
            nm_win = c.execute(win_sql_sel_north%(azi+pm_azi,fix_angle(azi-pm_azi))).fetchall()
        else:
            nm_win = c.execute(win_sql_sel%(fix_angle(azi-pm_azi),azi+pm_azi)).fetchall()
        #print([nm[0] for nm in nm_win])
        win_obj= [win for win in objs_filt_win for nm in nm_win if nm[0]==get_obj_name(win).upper()]
        print("Windows with azi: %.2f"%(azi),nm_win)
        print([get_obj_name(win) for win in win_obj])

        # TODO- refactor this block
        for obj in win_obj:
            # Surface that window is affixed to
            surf_nm=get_obj_abstract(obj, 4)
            surf_obj=[s for s in objs_filt_surf if surf_nm==get_obj_name(s)][0]
            # Names in no_add_list are not in Zones
            if is_not_in(no_add_list, get_obj_abstract(surf_obj, 4)):
                cons_line=cons_regex.findall(obj)
                cons_nm=get_obj_abstract(obj, 3)
                printc("Replacing Construction '%s' with '%s'"%(cons_nm, wtype), 'blue')
                obj=obj.replace(cons_nm, wtype)
                mycons_nm=cons_nm
                if frame_div_nm:
                    printc("Adding FrameAndDivider property: %s"%(frame_div_nm), 'yellow')
                    frame_line=frame_regex.findall(obj)[0]
                    #print("Frame Line: ",frame_line)
                    new_frame_line=frame_line.replace(',', frame_div_nm+',')
                    obj=obj.replace(frame_line, new_frame_line)
                mod_win_objs.append(obj)

    #print("\n".join(mod_win_objs))

    ## Finally, replace modified window objects
    # Reprocess file since new Construction/Material objects were added
    objs_all=get_IDF_objs_raw(new_objs)
    for idx,myobj in enumerate(objs_all):
        if 'FenestrationSurface:Detailed' in myobj:
            # TODO: SUPER Inefficient look up, Refactor
            for j,w in enumerate(mod_win_objs):
                if get_obj_name(myobj)==get_obj_name(w):
                    #print("TEST- OBJSALL-IDX and MOD-IDX: %s"%str([idx,j]))
                    printc("Replacing Modified Window: %s\n"%(get_obj_name(myobj)), 'yellow')
                    new_objs[idx]=w

    return new_objs


def mod_WWR_file(to_file=to_file, wwrs=[10,10,40,10]):
    """Modified version of `mod_WWR` which creates an IDF output for testing purposes. File output uses suffix `_WWR.idf` by default."""
    return __abstract_add_objs2file(mod_WWR, to_file=to_file, suffix='WWR')

# TODO: Give WWR dict (azi: WWR, ...) to have more than 4 directions
# TODO: Replace get_azi to NOT use SQL statements (assume e+ has been run)
# TODO: Test if Window spreads across full wall or partially
#       * Modify coordinates differently if partial coverage
# TODO: Modify window shading to match new window cordinates
#       * Shading placed directly over window (shifted down/up and/or left/right)
def mod_WWR(objs_all, args={ 'wwrs': [10,10,40,10] }):
    """Modify Window to Wall Ratios (WWRs) of (`FenestrationSurface:Detailed`) objects *for strip windows only` by modifying z-coordinates.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `wwrs` Python `List` of WWRs for each cardinal direction: `[north, east, south, west]`

    Returns:

    * `new_objs`: genEPJ object list with modified WWRs (Python `List`)
    """
    ## Steps:
    # * Given WWRper array
    # for each win_dir in WWRper
    # 0. Get info
    #    . window name
    #    . surf names (with windows)
    #    . calc existing WWR, calc width of window
    #    . calc new width of window (from WWR)
    #    .
    # 1.
    #    .

    new_objs=list(objs_all)

    wwrs = args['wwrs']

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    #objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    #zone_nms = [get_obj_name(myobj) for myobj in objs_zon if 'plenum' not in get_obj_name(myobj).lower()]
    objs_filt_win=filter_IDF_objs_raw(objs_all, 'FenestrationSurface:Detailed')
    objs_filt_surf=filter_IDF_objs_raw(objs_all, 'BuildingSurface:Detailed')
    objs_filt_wall= [surf for surf in objs_filt_surf if get_surf_type(surf)=='Wall']

    # GET exterior wall surface name (with a window in it)
    wall_with_windows=[wl for wl in objs_filt_wall for win_obj in objs_filt_win if get_obj_name(wl) == get_obj_abstract(win_obj,4)]
    #print(zones_with_windows)

    pm_azi=45 # Plus/Minus of Azimuth
    win_sql_sel='SELECT SurfaceName from Surfaces WHERE ClassName=="Window" AND Azimuth>%d AND Azimuth<=%d AND ExtBoundCond=0'
    # Special select statement required for north face
    win_sql_sel_north='SELECT SurfaceName from Surfaces WHERE ClassName=="Window" AND Azimuth>=0 AND Azimuth<=%d OR Azimuth>=%d'
    mod_win_objs=[]
    def fix_angle(myang):
        if myang<0: return myang+360
        else: return myang
    # Directions of wwrs: [north, east, south, west]
    for idx,wwr in enumerate(wwrs):
    #for wn in objs_filt_win:
        azi=idx*90.
        frac_wwr=wwr/100.
        if (azi-pm_azi)<=0 :
            nm_win = c.execute(win_sql_sel_north%(azi+pm_azi,fix_angle(azi-pm_azi))).fetchall()
        else:
            nm_win = c.execute(win_sql_sel%(fix_angle(azi-pm_azi),azi+pm_azi)).fetchall()
        #print([nm[0] for nm in nm_win])
        win_obj= [win for win in objs_filt_win for nm in nm_win if nm[0]==get_obj_name(win).upper()]
        #print("Windows with azi: %.2f"%(azi),nm_win)
        #print([get_obj_name(win) for win in win_obj])

        # EnergyPlus v9+ removes '!- Shading Control Name' from object
        if 'Shading Control Name' in win_obj:
            bs_idx=11
        else: bs_idx=10

        for obj in win_obj:
            # Get win coordinates and area
            win_coor=_get_surf_coordin(obj)
            olddh=win_coor[0][2]-win_coor[1][2]
            win_area=_calc_area(obj,'Wall')
            wid=win_area/olddh
            # Get wall coordinates and area
            wlobj= [wl for wl in objs_filt_wall if get_obj_abstract(obj,4)==get_obj_name(wl)]
            wlobj=wlobj[0]
            wall_coor=_get_surf_coordin(wlobj)
            wall_area=_calc_area(wlobj,'Wall')
            # Calc existing WWR, get width
            old_wwr= win_area/wall_area
            newh=wall_area*frac_wwr/wid
            hlf_h=win_coor[1][2]+(win_coor[0][2]-win_coor[1][2])/2.0
            new_coor=array(win_coor)
            printc("Recalculting Window Coordinates: %s\n"%(get_obj_name(obj)), 'yellow')
            new_coor[0][2]= hlf_h+newh/2.0
            new_coor[1][2]= hlf_h-newh/2.0
            new_coor[2][2]= hlf_h-newh/2.0
            new_coor[3][2]= hlf_h+newh/2.0
            #print("%s: OLD WWR: "%(get_obj_name(obj)),old_wwr)
            #print("%s: NEW WWR: "%(get_obj_name(obj)),frac_wwr)
            #print("%s: Wall Area: "%(get_obj_name(obj)),wall_area)
            obj_old=str(obj)
            obj_splt=obj.split("\n")
            def lstmap(_fn,_v): return list(map(_fn, _v))
            print("\n".join(obj_splt[bs_idx:bs_idx+4]))
            obj_splt[bs_idx]="    "+",".join(lstmap(str,new_coor[0]))+",  !- X,Y,Z ==> Vertex 1 {m}"
            obj_splt[bs_idx+1]="    "+",".join(lstmap(str,new_coor[1]))+",  !- X,Y,Z ==> Vertex 2 {m}"
            obj_splt[bs_idx+2]="    "+",".join(lstmap(str,new_coor[2]))+",  !- X,Y,Z ==> Vertex 3 {m}"
            obj_splt[bs_idx+3]="    "+",".join(lstmap(str,new_coor[3]))+";  !- X,Y,Z ==> Vertex 4 {m}"
            obj="\n".join(obj_splt)
            #print(obj)
            #print(obj_old)
            #new_win_area=_calc_area5(obj,'Wall')
            # NOTE: Doesnt work since it depends on a SQL select statement with old info
            #print("%s: MOD WWR: "%(get_obj_name(obj)),new_win_area/wall_area)
            #print("%s: MOD Height: "%(get_obj_name(obj)),newh)
            #print("\n\n")
            mod_win_objs.append(obj)
            # Calc new height
            # Set window coordinates

    # Finally, replace modified window objects
    for idx,myobj in enumerate(objs_all):
        if 'FenestrationSurface:Detailed' in myobj:
            # TODO: SUPER Innefficient look up, Refactor
            for w in mod_win_objs:
                if get_obj_name(myobj)==get_obj_name(w):
                    printc("Replacing Modified Window: %s\n"%(get_obj_name(myobj)), 'yellow')
                    new_objs[idx]=w


    return new_objs

def mod_insul_file(to_file=to_file, loc="ExtWall", resis=20):
    """Modified version of `mod_insul` which creates an IDF output for testing purposes. File output uses suffix `_insul.idf` by default."""
    return __abstract_add_objs2file(mod_insul, to_file=to_file, suffix='insul')

# TODO- Add SLAB insulation support
def mod_insul(objs_all, args={ 'loc': "ExtWall", 'resis': 30} ):
    """Modify R-Value/RSI of a wall in specified E+ `Construction`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `loc` Location where to update R-Value/RSI (eg. ExtWall, ExtRoof, etc)

    Steps:
    1. Get objects with loc specifier
    2. Get material object for insulation
    3. Sub U-val for new construction
    4. Rename copied material object
    5. Reference copied material object for all objects with loc specifier
    6. Return objs

    Returns:

    * `new_objs`: genEPJ object list with modified insulation in specified location  (Python `List`)
    """

    loc=args['loc']
    resis=args['resis']

    new_objs=list(objs_all)

    filt_surf_objs=filter_IDF_objs_raw(new_objs, 'BuildingSurface:Detailed')
    #print(len( filt_surf_objs))
    filt_surf_with_loc=[obj for obj in filt_surf_objs if loc in get_obj_abstract(obj, 3)]
    surf_cons_nms=list( map(lambda x: get_obj_abstract(x,3), filt_surf_with_loc) )
    #print("TEST Construction Names: ", surf_cons_nms)
    #TODO- Look at frequency and select most common name
    try:
        surf_cons_nm= surf_cons_nms[0]
    except:
        raise ValueError("No valid surface names found: surf_cons_nms[0] doesn't exist for %s"%(loc))
    print("Surf Const Name: ",surf_cons_nm)

    filt_cons_objs=filter_IDF_objs_raw(new_objs, 'Construction')
    filt_consIS_objs=filter_IDF_objs_raw(new_objs, 'Construction:InternalSource')
    filt_cons_objs.extend( filt_consIS_objs )
    #test_objnm=[i for i,obj in enumerate(new_objs) if isinstance (get_obj_name(obj), str)]
    try:
        #print("TEST: CONS objs names: ", list(map(get_obj_name, filt_cons_objs)))
        # Need to subsitute new Material Name into this
        cons_obj_idxs = [i for i,obj in enumerate(new_objs) if
            ((get_obj_name(obj)==surf_cons_nm) and
             (get_obj_type(obj)=="Construction" or get_obj_type(obj)=="Construction:InternalSource"))]
        #print("TEST: CONS FILTER: ",cons_obj_idxs)
        cons_obj_idx=cons_obj_idxs[0]
        #print(cons_obj_idxs)
        #print(cons_obj_idx)
    except IndexError:
        printc("No Construction objects found.", 'red')
        return None

    filt_cons_with_surfnm=[obj for obj in filt_cons_objs if get_obj_name(obj)==surf_cons_nm]
    raw_obj=trim_comments(filt_cons_with_surfnm[0])
    #print(raw_obj)
    mat_nm=[st for st in raw_obj.split(",\n") if "insul" in st.lower()]
    #print(mat_nm)
    mat_nm= mat_nm[0].replace(";","")
    print("Insulation Material Name: ",mat_nm)
    # MOD as in modified
    new_mat_nm=mat_nm+" MOD"+loc

    # Modify the material name in the Construction object
    new_objs[cons_obj_idx]=new_objs[cons_obj_idx].replace(mat_nm, new_mat_nm)

    # Modify the Material object with new properties
    filt_mat_objs=filter_IDF_objs_raw(new_objs, 'Material')
    old_mat_obj=[obj for obj in filt_mat_objs if get_obj_name(obj)==mat_nm][0]
    new_mat_obj=old_mat_obj.replace(mat_nm, new_mat_nm)
    # Get existing properties: thick, k-val
    #raw_mat=trim_comments(old_mat_obj).split(",\n")
    raw_mat=trim_comments(old_mat_obj).split(",")
    raw_mat=[ txt.strip() for txt in raw_mat]
    th=float(raw_mat[3]) # thickness in meters
    k =float(raw_mat[4]) # conductivity in W/m-K
    old_resis=th/k # Resistance in m2K/W
    print("Old Resis Val, R-val: ", old_resis*5.678263337)
    print("Old Conduc, W/m-K: ", k)
    print("Old Thickness, m: ", th)
    new_k=th/(resis/5.678263337) # conductivity in W/m-K
    #new_th=(resis/5.678263337)*k # thickness in meters
    print("New Resis, R-val: ", resis)
    print("New Conduc, W/m-K: ", new_k)
    #print("New Thickness, m: ", new_th)
    print("New Thickness, m: ", th)

    # Sub conductance
    new_mat_obj=new_mat_obj.replace(raw_mat[4], "%.5f"%(new_k))
    #print("Replace TEST: "+raw_mat[4]+" with "+"%.5f"%(new_k))

    ### Sub thickness
    #new_mat_obj=new_mat_obj.replace(raw_mat[3], "%.5f"%(new_th))

    # Insert right above Construction object
    new_objs.insert(cons_obj_idx, new_mat_obj)

    return new_objs

def mod_infil_file(to_file=to_file, frac=0.5):
    """Modified version of `mod_infil` which creates an IDF output for testing purposes. File output uses suffix `_Infil.idf` by default."""
    return __abstract_add_objs2file(mod_infil, to_file=to_file, suffix='Infil')

def mod_infil(objs_all, args={ 'frac': 0.5 }):
    """Modify E+ `ZoneInfiltration:DesignFlowRate` in specified `Zones`.


    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `frac` Fraction to modify infiltration by (ie. Improve/deteriorate enclosure air-tightness) (eg. `frac=0.8` implies a 20% reduction). `zone_selective_mod` Modify `ZoneInfiltration:DesignFlowRate` only to this list of `Zones`.

    Returns:

    * `new_objs`: genEPJ object list with modified infiltration in specified `Zones` (Python `List`)
    """
    # Steps:
    #  1. Get objects
    #  2. Conditional modifications: ACH, Flow/Area

    frac=args['frac']

    new_objs=list(objs_all)
    infil_filt_objs=filter_IDF_objs_raw(new_objs, 'ZoneInfiltration:DesignFlowRate')
    infil_filt_idxs=[idx for idx,obj in enumerate(objs_all) if get_obj_type(obj)=='ZoneInfiltration:DesignFlowRate']
    for obj_idx,obj in zip(infil_filt_idxs,infil_filt_objs):
        # VD: Modify infiltration for specific zone types
        if 'zone_selective_mod' in args:
            if args['zone_selective_mod'] in get_obj_name(obj):
                mod_obj=set_obj_Infil(obj,frac=frac)
                new_objs[obj_idx]=mod_obj
        else:
            mod_obj=set_obj_Infil(obj,frac=frac)
            new_objs[obj_idx]=mod_obj
        #print("Infil: "+ get_obj_abstract(new_objs[obj_idx], 7))
        #print("Infil: "+ str(obj_idx))

    #for i in infil_filt_idxs:
    #    print( "Infil: "+ get_obj_abstract(new_objs[i], 7))

    return new_objs

def add_output_control_file(to_file=to_file):
    """Modified version of `add_output_control` which creates an IDF output for testing purposes. File output uses suffix `_OutputCntrl'.idf` by default."""
    return __abstract_add_objs2file(add_output_control, to_file=to_file, suffix='OutputCntrl')

def add_output_control(objs_all, args={}):
    """Add/Modify (if previous found)  `OutputControl:ReportingTolerances` to E+ model. Default setting is to set heating/cooling setpoint tolerance (Default is 0.3C).

    Value with help determine if an heating/cooling setpoint is "unmet".

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list `OutputControl:ReportingTolerances` added (Python `List`)
    """
    new_objs=list(objs_all)

    obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='OutputControl:ReportingTolerances']

    temp_output, output_defs = templ.template_output_tolerance()

    oc_exists=[True for o in objs_all if 'OutputControl:ReportingTolerances'==get_obj_type(o)]
    if any(oc_exists): oc_exists=True
    else: oc_exists=False

    # Insert output control only if it doesnt exist
    if not oc_exists:
        new_objs.insert(-1, idf_templater( {}, temp_output, output_defs  ) )
        printc("\nInserting 'OutputControl:ReportingTolerances'", "green")
    else:
        #printc("\nNOT Inserting 'OutputControl:ReportingTolerances' (Previously Found)", "yellow")
        printc("\nOverwritting existing 'OutputControl:ReportingTolerances' object", "yellow")
        #new_objs[obj_idxs[0]] = temp_oc
        new_objs[obj_idxs[0]] = idf_templater( {}, temp_output, output_defs )


    return new_objs


def add_UFAD_file(to_file=to_file):
    """Modified version of `add_UFAC` which creates an IDF output for testing purposes. File output uses suffix `_UFAD.idf` by default."""
    return __abstract_add_objs2file(add_UFAD, to_file=to_file, suffix='UFAD')

def add_UFAD(objs_all, args={}):
    """Add Underfloor Air Distribution system in specified `Zones`.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with UFAD (Python `List`)
    """

    new_objs=list(objs_all)

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    print( len(objs_zon) )
    #zone_nm = [get_obj_name(myobj) for myobj in objs_zon if 'plenum' not in get_obj_name(myobj).lower()]
    no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'corridor']
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    obj_idx=-1

    temp_ufadmod, defs_ufadmod= templ.HVAC_RoomAirModel()
    temp_ufadset, defs_ufadset= templ.HVAC_UFAD_RoomAirSettings()
    for nm in zone_nm:

        d={
           'zone_name': nm,
           'type': "UnderFloorAirDistributionExterior",
        }
        printc("Adding Displacement Ventilation to Zone: %s"%(mkcolor(nm,'green')), "blue")
        #new_objs.insert(obj_idx, temp_roomair%(nm,nm))
        #new_objs.insert(obj_idx, temp_UFAD%(nm))
        new_objs.insert(obj_idx, idf_templater( d, temp_ufadmod, defs_ufadmod) )
        new_objs.insert(obj_idx, idf_templater( d, temp_ufadset, defs_ufadset) )

    return new_objs

def add_DV_file(to_file=to_file):
    """Modified version of `add_DV` which creates an IDF output for testing purposes. File output uses suffix `_DV.idf` by default."""
    return __abstract_add_objs2file(add_DV, to_file=to_file, suffix='DV')

def add_DV(objs_all, args={}):
    """Add Displacement Ventilation (DV) objects via `RoomAirModelType` and `ThreeNodeDisplacementVentilation` objects.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None` used

    Returns:

    * `new_objs`: genEPJ object list with newly added DV objects (Python `List`)
    """

    new_objs=list(objs_all)

    objs_zon=filter_IDF_objs_raw(objs_all, 'Zone')
    #zone_nm = [get_obj_name(myobj) for myobj in objs_zon if 'plenum' not in get_obj_name(myobj).lower()]
    #no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical']
    no_mech_lst=['plenum', 'tower', 'stairs', 'mechanical', 'corridor']
    zone_nm = [get_obj_name(myobj) for myobj in objs_zon if not is_in(no_mech_lst, get_obj_name(myobj).lower())]

    obj_idx=-1

    temp_dvmod, defs_dvmod= templ.HVAC_RoomAirModel()
    temp_dvset, defs_dvset= templ.HVAC_DV_RoomAirSettings()
    for nm in zone_nm:

        d={
           'zone_name': nm,
           'type': "ThreeNodeDisplacementVentilation",
        }
        printc("Adding Displacement Ventilation to Zone: %s"%(mkcolor(nm,'green')), "blue")
        new_objs.insert(obj_idx, idf_templater( d, temp_dvmod, defs_dvmod) )
        new_objs.insert(obj_idx, idf_templater( d, temp_dvset, defs_dvset) )

    return new_objs

def scale_xyz_file(to_file=to_file):
    """Modified version of `scale_xyz` which creates an IDF output for testing purposes. File output uses suffix `_xzyscale.idf` by default."""
    return __abstract_add_objs2file(scale_xyz, to_file=to_file, suffix='xyzscale')

# GOAL: scale all specified coordinates and return modified objects
#       * Effectively modify aspect ratios or heights
def scale_xyz(objs_all, xscale=0.5, yscale=1.0, zscale=1.0):
    """Scale coordinates (xyz) of all `Zone`, `BuildingSurface:Detailed`, and `FenestrationSurface:Detailed` objects.

    **Experimental** use. Not fully tested.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with scaled XYZ coordinates (Python `List`)
    """

    printc("\nScaling Surface/Zone objects", "green")

    new_objs = list(objs_all)
    #BuildingSurface:Detailed,
    #FenestrationSurface:Detailed
    #Zone

    #_get_surf_coordin(surf)
    #_get_zone_coordin(zn)
    objs_zn   = filter_IDF_objs_raw(new_objs, 'Zone')
    objs_surf = filter_IDF_objs_raw(new_objs, 'BuildingSurface:Detailed')
    objs_win  = filter_IDF_objs_raw(new_objs, 'FenestrationSurface:Detailed')

    def _mod_surfs(objs, bs_idx=11):
        # Modify Window objects
        iter_objs=list(objs)
        for i,obj in enumerate(iter_objs):
            if obj in objs_surf:
                j=bs_idx # position of first coordinate
                cor=_get_surf_coordin(obj)
                new_cor=cor*[xscale, yscale, zscale]
                print(obj)
                print(cor)
                for l in range(len(cor)):
                    txt_cor="%.6f,%.6f,%.6f"%tuple(new_cor[l])
                    #print("Trying to modify position: %d to %s"%(j, txt_cor))
                    objs[i]=set_obj_abstract(objs[i], txt_cor, pos=j)
                    j=j+1
        return objs

    # Both surfaces handled by same block
    # EnergyPlus v9+ removes '!- Shading Control Name' from object
    if not 'Shading Control Name' in objs_win[0]:
        new_objs=_mod_surfs(new_objs, bs_idx=10)
    else:
        objs_surf.extend(objs_win) # Subs made below

    # Modify Surface objects
    new_objs=_mod_surfs(new_objs, bs_idx=11)

    # Modify Zone objects: TODO-

    return new_objs

def add_floor_multiplier_file(to_file=to_file):
    """Modified version of `add_floor_multiplier` which creates an IDF output for testing purposes. File output uses suffix `_flr.idf` by default."""
    return __abstract_add_objs2file(add_floor_multiplier, to_file=to_file, suffix='flr')

def add_floor_multiplier(objs_all, args={"mul":2}):
    """Add floor multiplier to top floor of building.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `mul` Multiplier to apply to top story of building
    mul=args['mul']

    Steps:

     1. Select all zones with (n-1) height (one-floor down from roof)
     2. Modify zone multiplier to `Zone` object (eg. change from 1 to 2)

    Returns:

    * `new_objs`: genEPJ object list with `mul` new floors (Python `List`)
    """
    new_objs=list(objs_all)

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()

    mul=args['mul']

    # TODO: Implement the dont use list
    dont_use=["TOWER"]
    objs_zone=filter_IDF_objs_raw(new_objs, 'Zone')
    # Zones heights unique and sorted from least to greatest
    sql_sel_h = "select DISTINCT(OriginZ) from Zones WHERE ZoneName NOT LIKE '%TOWER%' ORDER BY OriginZ"
    zone_hs=c.execute(sql_sel_h).fetchall()
    try:
        zone_h = zone_hs[-2] # Get the second largest height
    except IndexError: # Added to make fn run on any file
        zone_h = 0 # Default to ground floor

    sql_sel_zonenm = "select ZoneName from Zones WHERE OriginZ = '%.1f'"%(zone_h)
    zonenms=c.execute(sql_sel_zonenm).fetchall()
    zonenms= list( map(lambda x: x[0], zonenms))
    #print(zonenms)
    objs_zone_mul=[obj for obj in objs_zone for znnm in zonenms if znnm == get_obj_name(obj).upper()]
    #print(objs_zone_mul)

    #j=0
    iter_objs=list(new_objs)
    for i,obj in enumerate(iter_objs):
        if obj in objs_zone_mul:
            new_objs[i]=set_obj_abstract(obj, mul, pos=7)
            #print(new_objs[i])
            #j=j+1

    #print(j, len(objs_zone_mul))
    #print(zonenms)

    return new_objs

def add_enduse_outputs_file(to_file=to_file):
    """Modified version of `add_enduse_outputs` which creates an IDF output for testing purposes. File output uses suffix `_EndUseOutput.idf` by default."""
    return __abstract_add_objs2file(add_enduse_outputs, to_file=to_file, suffix='EndUseOutput')

def add_enduse_outputs(new_objs, args={ 'timestep': "monthly"}):
    """Add E+ Output variables with a specified timestep. Create data necessary for diagnostic scripts.
    Function requires that Outputs adhere to strict template formatting rules.

    Parameters:

    * `new_objs`: genEPJ object list (Python `List`)
    * `args`: `output_vars` E+ variables to create outputs for. `timestep` specified timestep for Output (monthly, hourly, annual)

    Returns:

    * `new_objs`: genEPJ object list with Outputs added for specified variables (Python `List`)
    """

    temp_output, output_defs =templ.template_meter_output()
    #output_defs['timestep']=timestep
    output_defs['timestep']=args['timestep']
    timestep=args['timestep']

    if 'output_vars' not in args:
        output_vars=[
          "InteriorLights:Electricity",
          "ExteriorLights:Electricity",
          "InteriorEquipment:Electricity",
          "ExteriorEquipment:Electricity",
          "Pumps:Electricity",
          "Fans:Electricity",
          "Refrigeration:Electricity",
          "Heating:Electricity",
          "Heating:Gas",
          "Cooling:Electricity",
          "HeatRejection:Electricity",
          "HeatRecovery:Electricity",
          "Humidification:Electricity",
          "WaterSystems:Electricity",
          "WaterSystems:Gas",
          "Generators:Electricity",
        ]
        output_defs['timestep']="monthly"
    else:
        output_vars=args['output_vars']

    printc("Adding End-Use Meters for diagnostics!", "green")
    for v in output_vars:
        printc("  Adding End-Use Meter: %s"%(v), "yellow")
        new_objs.insert(-1, idf_templater( {'var': v, 'timestep': timestep}, temp_output, output_defs  ) )

    return new_objs

def add_misc_outputs_file(to_file=to_file):
    """Modified version of `add_misc_outputs` which creates an IDF output for testing purposes. File output uses suffix `_miscOutputs.idf` by default."""
    return __abstract_add_objs2file(add_misc_outputs, to_file=to_file, suffix='miscOutputs')

def add_misc_outputs(objs_all, args={}):
    """Add E+ Output variables with no script formatting rules (inserts E+ object directly). Create data necessary for diagnostic scripts.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `output_vars` E+ objects to insert directly into genEPJ List

    Returns:

    * `new_objs`: genEPJ object list with Outputs added for specified variables (Python `List`)
    """
    """Insert list of output variables as is with no template formating"""

    new_objs=list(objs_all)

    if 'output_vars' in args:
        output_vars=args['output_vars']
    else:
        output_vars=[]

    for v in output_vars:
        new_objs.insert(-1, v)

    return new_objs

def add_output_variables_file(to_file=to_file):
    """Modified version of `add_output_variables` which creates an IDF output for testing purposes. File output uses suffix `_OutputVariable.idf` by default."""
    return __abstract_add_objs2file(add_output_variables, to_file=to_file, suffix='OutputVariable')

def add_output_variables(objs_all, args={}):
    """Add E+ `Output:Variable` for all specified variable names.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `output_vars` `List` of output variables to create E+ objects for. `timestep` Report output using provided timestep (eg. 'timestep', 'hourly', 'daily', 'monthly')

    Returns:

    * `new_objs`: genEPJ object list with `Output:Variable` (Python `List`)
    """

    # SB: Updated to include debugall calls outside of generate_IDF2.py
    #[ add_output_variables , options.debugtherm , {'output_vars': hrly_output_vars , 'args_def': {'timestep': 'hourly'} } ]    ,
    #[ add_enduse_outputs   , options.debugall   , { 'timestep': "hourly"           , 'output_vars': output_vars_meter_debug} ] ,
    new_objs=list(objs_all)

    if 'output_vars' in args:
        output_vars=args['output_vars']
    else:
        output_vars=[]

    temp_output, output_defs =templ.template_output()

    for v in output_vars:
        #new_objs.insert(-1, idf_templater( {'name': v}, temp_output, {} ) )
        #new_objs.insert(-1, idf_templater( {'name': v}, temp_output, {} ) )
        d={
           'name': v,
           'timestep': args['timestep'],
        }
        new_objs.insert(-1, idf_templater( d, temp_output, output_defs ) )

    return new_objs

## SB: Tag for deletion?
#def prep_basement_to_parking_file(to_file=to_file):
#    """Modified version of `prep_basement_to_parking` which creates an IDF output for testing purposes. File output uses suffix `_prepPark.idf` by default."""
#    return __abstract_add_objs2file(prep_basement_to_parking, to_file=to_file, suffix='prepPark')
#
# NOTE- TODO- This wont work. All -z-axis zones are ALREADY affilated with Zonelists (ex. Lights, Ventilation, etc)
#def prep_basement_to_parking(objs_all):
#
#    new_objs = list(objs_all)
#    objs_zns =filter_IDF_objs_raw(objs_all, 'Zone')
#    objs_zns_negz   = [ o for o in objs_zns if _get_zone_coordin(o)[3]<0.0 ]
#    objs_znsnm_negz = [ get_obj_name(o) for o in objs_zns_negz ]
#
#    fansch_nm="ScheduleParkingCont"
#
#    # Build ZoneList for ParkingGarage
#
#    schepark_temp, schepark_defs = templ.HVACtemplate_schedule_alwaysON()
#    new_objs.insert(-1, idf_templater({'name': fansch_nm}, schepark_temp, schepark_defs ) )
#
#    # Add Lights object for Zonelist: ParkingGarage
#    vent_temp, vent_defs = templ.HVAC_ZoneVentilation()
#    d={
#       'name': nm+" ParkingVent",
#       'zone_name': nm,
#       'flow_rate': exh_use,
#       'fan_pressure': deltaP,
#       'avail_sche': fansch_nm,
#       'fan_pressure': "300", #Pa
#       'method': "Flow/Area",
#    }
#    new_objs.insert(-1, idf_templater(d, vent_temp, vent_defs ) )
#
#    lights_temp, lights_defs = templ.Equipment_InteriorLighting()
#    d={
#      'name': nm+" Lights",
#      'zone_name': nm,
#      'avail_name': fansch_nm,
#      'watt_per_area': "2.1527821",
#    }
#    new_objs.insert(-1, idf_templater(d, lights_temp, lights_defs ) )
#
#    return new_objs

def set_primary_energy_factors_file(to_file=to_file):
    """Modified version of `set_primary_energy_factors` which creates an IDF output for testing purposes. File output uses suffix `_PEF.idf` by default."""
    return __abstract_add_objs2file(set_primary_energy_factors, to_file=to_file, suffix='PEF')

# TODO: Fine tune for Quebec vs Ontario
def set_primary_energy_factors(objs_all, args={'location': "Quebec"} ):
    """Set Primary Energy Factors (PEF) by selecting a region (limited to Ontario/Quebec).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `location` Specified location which determines PEFs

    Returns:

    * `new_objs`: genEPJ object list with PEF specified (Python `List`)
    """
    new_objs = list(objs_all)

    #Field: Units of Measure
    #Units in mass with kg or by volume in m3.

    #Field: Energy per Unit Factor
    #The higher heating value of the fuel type.

    #Field: Source Energy Factor
    #Multiplied by the fuel consumption to compute the source energy contribution for the fuel. If a
    #schedule is also specified in the next field, the value specified here, the schedule value, and
    #the fuel consumption are multiplied together for each timestep to determine the source
    #energy contribution for the fuel. If the multipliers in the schedule specified in the next field fully
    #represent the source energy conversion factor, the value in this field should be set to one. If

    printc("set_primary_energy_factors: Inserting Primary Energy Factors", 'blue')

    # District Energy systems (Heating)
    # OLD: 0.663
    # Assumptions: 20% from NaturalGas network (1.092 weight), 80% Heat Recovered content (0 weight). Assume 15% HL through network
    # PEF = "(1.15)*0.2*1.092" = .251160 ^-1 = 3.98153
    # SB TODO: Need to know conincidental factor, is 20% natural gas reasonable?
    distPEF_temp, distPEF_defs=templ.add_district_PEF()
    new_objs.insert(-1, idf_templater( {'dist_PEF': "3.982"}, distPEF_temp, distPEF_defs) )

    # Elec: 96% Hydro in Quebec, 5% loss over tranmission lines
    # FROM: PEF-finalreport.pdf PEF(non-renew)=0.5; TotalHydro==1.5 (embodied energy in dam)
    # PEF = calc "1-0.97*0.95" =  0.0880
    # PEF = 1.06*3*(1-0.96) = 0.1272
    # "Quebec: the factor is 0.06 for electricity since it is pretty much all hydroelectric and the distribution loss in the grid is around 6%."
    # http://www.greenbuildingforum.co.uk/newforum/comments.php?DiscussionID=3749
    d={
       'elec_PEF': "1.0",
       #'elec_PEF': 0.0785,
       #'elec_PEF': 0.785,
       #'elec_PEF': 1.5,
    }
    elecPEF_temp,elecPEF_defs=templ.add_elec_PEF()
    new_objs.insert(-1, idf_templater( d, elecPEF_temp, elecPEF_defs) )

    # Natural Gas (left at defaults)
    d={
       'ngas_PEF': "1.0",
       #'ngas_PEF': 1.092,
    }
    ngasPEF_temp,ngasPEF_defs=templ.add_ngas_PEF()
    new_objs.insert(-1, idf_templater( d, ngasPEF_temp, ngasPEF_defs) )

    return new_objs

def turn_off_comfort_warnings_file(to_file=to_file):
    """Modified version of `turn_off_comfort_warnings` which creates an IDF output for testing purposes. File output uses suffix `_noplp55warn.idf` by default."""
    return __abstract_add_objs2file(turn_off_comfort_warnings, to_file=to_file, suffix='noplp55warn')

def turn_off_comfort_warnings(objs_all, args={}):
    "Disable ASHRAE 55 warnings for all `People` schedules"
    new_objs = list(objs_all)

    # Turning off ASHRAE 55 Comfort Warnings for some SpaceTypes
    objs_plp=filter_IDF_objs_raw(new_objs, 'People')
    idx_plp=[ jj for jj,obj in enumerate(new_objs) if get_obj_type(obj)=='People']
    for idx in idx_plp:
        no_lst=['storage', 'mechanical']
        if is_in(no_lst, get_obj_name(new_objs[idx]).lower()):
            printc("DISABLING ASHRAE 55 Comfort Warnings for People Type: %s"%(get_obj_name(new_objs[idx])), 'yellow')
            mod_obj=_mod_People_ASHRAE55_off(new_objs[idx])
            new_objs[idx]=mod_obj

    return new_objs

def define_essential_services_file(to_file=to_file):
    """Modified version of `define_essential_services` which creates an IDF output for testing purposes. File output uses suffix `_essen.idf` by default."""
    return __abstract_add_objs2file(define_essential_services, to_file=to_file, suffix='essen')

# SB TODO: Occupancy schedules aren't working yet
# SB TODO: DHW already set to 43C, should I set it lower?
# Reduce simulation to essential services:
#  1) Remove and recreate temperature setpoints
#  2) Reset DHW setpoints (warmish showers)
#  3) ...
def define_essential_services(objs_all):
    """Modify heating/cooling/thermostat/activity schedules to specify ONLY essential services. Use to study a Buildings free floating behaviour during outages.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with modified services (Python `List`)
    """
    new_objs=list(objs_all)

    hsp_sche = 'Htg-SetP-Sch-Essen'
    csp_sche = 'Clg-SetP-Sch-Essen'
    thermo_nm= 'All Zones Essential'
    act_sch_nm='Activity Sch Essential'

    # Common Thermostat template
    thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
    d={
      "thermo_nm": thermo_nm,
      "hsp_sche": heatsp_nm,
      "csp_sche": coolsp_nm,
    }
    new_objs.insert(-1, idf_templater(d, thermo_temp, thermo_defs ) )

    thermo_temp,thermo_defs=templ.HVACtemplate_thermosche_simple()
    # Heating
    d={
      "name": hsp_sche,
      'temp1':  "18.0",
      'temp2':  "13.0",
      'temp3':  "23.0",
    }
    new_objs.insert(-1, idf_templater(d, thermo_temp, thermo_defs ) )
    # Cooling
    d={
      "name": csp_sche,
      'temp1':  "30.0",
      'temp2':  "24.0",
      'temp3':  "32.0",
    }
    new_objs.insert(-1, idf_templater(d, thermo_temp, thermo_defs ) )

    # Occupant activity schedule template
    actavail_temp, actavail_defs = templ.HVACtemplate_schedule_alwaysON2()


    # SB TODO: Update all Temperature objects in : HVACTemplate:Zone,
    objs_filt_hvac=[obj for obj in new_objs if 'HVACTemplate:Zone' in get_obj_type(obj)]
    objs_filt_people=filter_IDF_objs_raw(new_objs, 'People')

    # TODO- refactor to be generic to building type
    if not 'Sifton' in to_file:
    #if 'Sifton' in to_file:
        occ_sch_nm='Office Occupancy Essential'
        d={
          'name': act_sch_nm,
          'type': "Any Number",
          'frac': "131.8",
          }
        new_objs.insert(-1, idf_templater(d, actavail_temp, actavail_defs ) )
        # Offices have Decreased occupancy (50% max)
        # NOTE: Increases heating loads, decreases cooling loads
        # NOTE: People are typically more active in an office
        comm_occ_temp,comm_occ_defs=templ.HVACtemplate_office_essen_avail()
        new_objs.insert(-1, idf_templater({'name': occ_sch_nm,}, comm_occ_temp, comm_occ_defs ) )
    else:
        occ_sch_nm='Residential Occupancy Essential'
        d={
          'name': act_sch_nm,
          'type': "Any Number",
          'frac': "120.0",
          }
        new_objs.insert(-1, idf_templater(d, actavail_temp, actavail_defs ) )
        # Residences have increased occupancy
        resi_occ_temp,resi_occ_defs=templ.HVACtemplate_resi_essen_avail()
        new_objs.insert(-1, idf_templater({'name': occ_sch_nm,}, resi_occ_temp, resi_occ_defs ) )


    for i,obj in enumerate(new_objs):
        if obj in objs_filt_people:
            occ_nm=get_obj_abstract(obj,3)
            act_nm=get_obj_abstract(obj,10)
            print("Found existing Occupancy schedule name: ",occ_nm)
            # Replace Occupancy Schedule and activity schedule
            new_objs[i] = obj.replace(occ_nm, occ_sch_nm).replace(act_nm, act_sch_nm+';')
            # Just replace Occupancy Schedule, not activity schedule
            #new_objs[i] = obj.replace(occ_nm, occ_sch_nm)

    return new_objs

def build_free_float_diagnostic_file(to_file=to_file):
    """Modified version of `build_free_float_diagnostic` which creates an IDF output for testing purposes. File output uses suffix `_freefloat.idf` by default."""
    return __abstract_add_objs2file(build_free_float_diagnostic, to_file=to_file, suffix='freefloat')

# GOAL: Turn off all HVAC, let building free float
def build_free_float_diagnostic(objs_all, args={}):
    """Build a free floating diagnostic by removing all heating/cooling schedules to the specified building. Allows the exploration of passive solar design effectiveness without required external heating/cooling inputs.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with Free Floating Temperatures (Python `List`)
    """
    new_objs=list(objs_all)

    printc("\nRemoving HVAC objects!", 'blue')
    print("Count new_objs [Orig]: ", len(new_objs))
    # Keep Sizing:Parameters (rm_all_HVAC removes this...)
    new_objs= [obj for obj in new_objs if 'hvactemplate' not in get_obj_type(obj).lower()]
    new_objs= [obj for obj in new_objs if 'sizing:zone'  not in get_obj_type(obj).lower()]
    new_objs= [obj for obj in new_objs if 'zonecontrol:thermostat' not in get_obj_type(obj).lower()]
    print("Count new_objs [No HVACtemp]: ", len(new_objs))
    ## Remove pesky heating/cooling setpoint objects
    #new_objs1= [obj for obj in new_objs if (('schedule:compact' != get_obj_type(obj).lower()) and ('temperature,' not in obj))]
    ## Symetric difference of the two sets
    #print( "\n".join(set(new_objs) ^ set(new_objs1)) )
    # NAND: not (x:schedule:compact and y:setp-sch)
    #        y
    #      F  T
    # x  F 1  1
    #    F 1  0
    #new_objs= [obj for obj in new_objs if (('schedule:compact' != get_obj_type(obj).lower()) and ('temperature,' not in obj))]
    #new_objs= [obj for obj in new_objs if (('schedule:compact' != get_obj_type(obj).lower()) and ('Temperature,' not in obj))]
    new_objs= [obj for obj in new_objs if not (('schedule:compact' in obj.lower()) and ('setp-sch' in obj.lower()))]
    new_objs= [obj for obj in new_objs if not (('schedule:compact' in obj.lower()) and ('ventschedcont' in obj.lower()))]
    new_objs= [obj for obj in new_objs if not (('schedule:compact' in get_obj_type(obj).lower()) and
                                               ('fanavailsched' in get_obj_name(obj).lower())) ]
    new_objs= [obj for obj in new_objs if not (('schedule:compact' in get_obj_type(obj).lower()) and
                                               ('min oa sched' in get_obj_name(obj).lower())) ]
    new_objs= [obj for obj in new_objs if not (('schedule:day' in obj.lower()) and ('setp' in obj.lower()))]
    new_objs= [obj for obj in new_objs if not (('schedule:week' in obj.lower()) and ('setp' in obj.lower()))]
    new_objs= [obj for obj in new_objs if not (('schedule:year' in obj.lower()) and ('setp' in obj.lower()))]
    new_objs= [obj for obj in new_objs if not ('thermostatsetpoint:dualsetpoint' in obj.lower())]
    print("Count new_objs [No Schedules]: ", len(new_objs))
    #new_objs=rm_all_HVAC(objs_all)

    ## This creates a metric shit-ton of output data
    temp_output, output_defs =templ.template_output()
    output_vars=[
      'Zone Mean Air Temperature',
      'Site Outdoor Air Drybulb Temperature',
    ]
    for v in output_vars:
        print(v)
        d={'name':  v,
           'timestep': "hourly", }
        new_objs.insert(-1, idf_templater( d, temp_output, output_defs ) )

    return new_objs

def interprete_schedule(sch_obj):
    "Convert E+ `Schedule` object to Python `List` to visualize schedules values."
    print('\n')
    sch_nm = get_obj_name(sch_obj)
    printc( "Processing Schedule: %s"%( mkcolor(sch_nm,'yellow')), 'green' )
    trim_sch = trim_comments(sch_obj).replace(';','')
    sch_lns = trim_sch.split(',')[4:]
    #print( "SCH LINES: ", sch_lns)
    times = [ int(sch_lns[i].split(':')[0]) for i in range(len(sch_lns)) if i%2 == 0 ]
    #myvals = [ float(sch_lns[i].strip('\n')) for i in range(len(sch_lns)) if not (i%2 == 0) ]
    myvals = [ float(sch_lns[i]) for i in range(len(sch_lns)) if not (i%2 == 0) ]
    # Filling in missing values
    prev_t = 0
    prev_vals = []
    for i, v in enumerate(myvals):
        v = [ v for t in range(prev_t, times[i]) ]
        prev_vals = prev_vals + v
        prev_t = times[i]
    #print( times, myvals)
    #print( range(1,24+1) )
    #print( prev_vals, len(prev_vals))
#[my_list[i] for i in range(len(my_list)) if i % 2 == 0]
    return list(prev_vals)

# SB: Only tested on DHW
def interprete_compact_schedule(sch_obj):
    "Convert E+ `Schedule:Compact` object to Python `List` to visualize values."
    print('\n')
    sch_nm = get_obj_name(sch_obj)
    printc( "Processing Schedule: %s"%( mkcolor(sch_nm,'yellow')), 'green' )
    trim_sch = trim_comments(sch_obj).replace(';','')
    trim_sch = trim_comments(trim_sch).replace('\nUNTIL: ','')
    sch_lns = trim_sch.split(',')[5:]
    #print("Raw Sch Lines: ",sch_lns)
    times = [  int(sch_lns[i].split(':')[0]) for i in range(len(sch_lns)) if i%2 == 0]
    myvals = [ float(sch_lns[i]) for i in range(len(sch_lns)) if not i%2 == 0]
    #print( times, myvals)
    # Filling in missing values
    prev_t = 0
    prev_vals = []
    for i, v in enumerate(myvals):
        v = [ v for t in range(prev_t, times[i]) ]
        prev_vals = prev_vals + v
        prev_t = times[i]
    #print( times, myvals)
    #print( range(1,24+1) )
    #print( prev_vals, len(prev_vals))
#[my_list[i] for i in range(len(my_list)) if i % 2 == 0]
    return list(prev_vals)

def extract_schedules_file(to_file=to_file):
    """Modified version of `extract_schedules` which creates an IDF output for testing purposes. File output uses suffix `_SCHEDULES.idf` by default."""
    return __abstract_add_objs2file(extract_schedules, to_file=to_file, suffix='SCHEDULES')

# Goal: Extract all necessary schedules for further analyses
# Future: modify schedules using best practices
# TODO:
#  1) Attribute proper amplitude to the given fractional schedule
#  2) Identify how much building area uses the given schedule
#  3) Extract DHW use for visualization
#  4) Extract ???
def extract_schedules(objs_all):
    """Extract all E+ schedules (Lighting, Equipment, People, etc) from E+ for quality assurance. Multiplies out fraction schedules to show actual values.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list identical to inputted `objs_all` (allow for use in genEPJ workflows)
    """
    new_objs=list(objs_all)

    num_star = 100

    #printc('\n'+'*'*num_star, 'blue')
    printc('\n'+'*'*num_star+'\n', 'blue')

    #sql_sel_zonenm='select b.ZoneName FROM NominalLighting AS a, Zones AS b WHERE a.ZoneIndex==b.ZoneIndex AND a.ObjectName LIKE "#%s#";'
    #def _get_lizone_areas(li_nm):
    #    statement=sql_sel_zonenm%( li_nm.upper() )
    #    statement=statement.replace("#","%")
    #    #res = c.execute(statement).fetchone()
    #    res = c.execute(statement).fetchall()
    #    #print("Raw Res: ", res)
    #    if len(res)>1 :
    #        printc("WARNING! More than one ZoneName returned for Light %s"%(mkcolor(li_nm, "blue")), "yellow")
    #    #nm=res[0]
    #    nms=map( lambda x: str(x[0]), res)
    #    #print(" Zones Names: ", nms)
    #    zn_areas=[ _calc_area_zone(o) for o in nms]
    #    #print(" Zones Areas: ", zn_areas)
    #    print(" Number of Zones Areas found: ", len(zn_areas))
    #    return sum(zn_areas)
    #
    ## LIGHTING
    #objs_light=filter_IDF_objs_raw(objs_all, 'Lights')
    #objs_day_sch=filter_IDF_objs_raw(objs_all, 'Schedule:Day:Interval')
    ## Schedule Name
    #objs_li_sch = [ get_obj_abstract( obj, 3) for obj in objs_light ]
    ## Assume W/m2
    #objs_li_nms = [ get_obj_name( obj) for obj in objs_light ]
    #objs_li_amp = [ get_obj_abstract( obj, 6) for obj in objs_light ]
    #print(" Lights Names: ", objs_li_nms)
    #print(" Lights Amplitudes: ", objs_li_amp)
    #zn_linm_areas=[ _get_lizone_areas(o) for o in objs_li_nms]
    #print(" Zones LiNM Areas: ", zn_linm_areas)
    #print(" Total Area: ", sum(zn_linm_areas) )
    ##objs_zn_areas=[ _calc_area_zone(o) for o in objs_zn_nms]
    ## Find all unique lighting schedules
    #all_li_sches = []
    #for j, li_obj in enumerate(objs_light):
    #    pass
    #    sche_nm = objs_li_sch[j]
    #    sche_objs = [ o for o in objs_day_sch if sche_nm in get_obj_name(o) ]
    #    #print("LEN LIGHT SCHE", len(sche_objs) )
    #    #print( "FOUND Schedule objects: ", sche_objs )
    #    #all_li_sches.append( sche_objs )
    #    all_li_sches = all_li_sches + sche_objs
    ## Process/Extract fractional info from all unique lighting schedules
    #sche_objs = list( set( all_li_sches ) )
    #for so in sche_objs:
    #    sch_frac_li = interprete_schedule( so )
    #    sch_nm = get_obj_name( so )
    #    #print(sch_nm)
    #    # Other Buildings
    #    #spl_schnm = sch_nm.split('Light')[0].strip(' ').strip('_').replace('_',' ')
    #    # Sifton Office
    #    spl_schnm = sch_nm.split('Bldg_Light')[0].strip(' ').strip('_').replace(' ','')
    #    amplitudes = [ objs_li_amp[j] for j,nm in enumerate(objs_li_nms) if spl_schnm in nm]
    #    if len(amplitudes) > 1 :
    #        printc("Warning: Multiple Amplitudes Found: %s"%( str(amplitudes) ), 'red')
    #    elif len(amplitudes)==1 :
    #        printc("Single Amplitude Found: %s"%( str(amplitudes) ), 'green')
    #    try:
    #        amp = float(amplitudes[0])
    #    except:
    #        amp = 1.0
    #    if len(amplitudes)>=1 :
    #        print( spl_schnm )
    #        print( sch_frac_li, len(sch_frac_li))
    #        print( "Amplitudes: ", amp*array(sch_frac_li) )
    #        #print( "Amplitudes: ", list(amp*array(sch_frac_li)) )

#    #printc('\n'+'*'*num_star, 'blue')
#    printc('\n'+'*'*num_star+'\n', 'blue')
#
#    # ElectricEquipment
#    objs_eleceq=filter_IDF_objs_raw(objs_all, 'ElectricEquipment')
#    objs_day_sch=filter_IDF_objs_raw(objs_all, 'Schedule:Day:Interval')
#    # Schedule Name
#    objs_eq_sch = [ get_obj_abstract( obj, 3) for obj in objs_eleceq ]
#    # Assume W/m2
#    objs_eq_nms = [ get_obj_name( obj) for obj in objs_eleceq ]
#    objs_eq_amp = [ get_obj_abstract( obj, 6) for obj in objs_eleceq ]
#    print(" ElectricEquipment Names: ", objs_eq_nms)
#    print(" ElectricEquipment Amplitudes: ", objs_eq_amp)
#    # Find all unique eleceqing schedules
#    all_eq_sches = []
#    for j, li_obj in enumerate(objs_eleceq):
#        pass
#        sche_nm = objs_eq_sch[j]
#        sche_objs = [ o for o in objs_day_sch if sche_nm in get_obj_name(o) ]
#        #print("LEN eleceq SCHE", len(sche_objs) )
#        #print( "FOUND Schedule objects: ", sche_objs )
#        all_eq_sches = all_eq_sches + sche_objs
#    # Process/Extract fractional info from all unique eleceqing schedules
#    sche_objs = list( set( all_eq_sches ) )
#    for so in sche_objs:
#        sch_frac_elec = interprete_schedule( so )
#        sch_nm = get_obj_name( so )
#        # Other building
#        #spl_schnm = sch_nm.split('Equip')[0].strip(' ').strip('_').replace('_',' ')
#        # Sifton office
#        spl_schnm = sch_nm.split('Bldg_Equip')[0].strip(' ').strip('_').replace(' ','')
#        amplitudes = [ objs_eq_amp[j] for j,nm in enumerate(objs_eq_nms) if spl_schnm in nm]
#        if len(amplitudes) > 1 :
#            printc("Warning: Multiple Amplitudes Found: %s"%( str(amplitudes) ), 'red')
#        elif len(amplitudes)==1 :
#            printc("Single Amplitude Found: %s"%( str(amplitudes) ), 'green')
#        try:
#            amp = float(amplitudes[0])
#        except:
#            amp = 1.0
#        if len(amplitudes)>=1 :
#            print( spl_schnm )
#            print( sch_frac_elec, len(sch_frac_elec))
#            print( "Amplitudes: ", amp*array(sch_frac_elec) )
#
#    printc('\n'+'*'*num_star+'\n', 'blue')
#
#    # People
#    objs_peop=filter_IDF_objs_raw(objs_all, 'People')
#    objs_day_sch=filter_IDF_objs_raw(objs_all, 'Schedule:Day:Interval')
#    # Schedule Name
#    objs_plp_sch = [ get_obj_abstract( obj, 3) for obj in objs_peop ]
#    # Assume people/m2
#    objs_plp_amp = [ get_obj_abstract( obj, 6) for obj in objs_peop ]
#    objs_plp_nm = [ get_obj_name( obj) for obj in objs_peop ]
#    print(" People Occupancy Names: ", objs_plp_nm)
#    print(" People Occupancy Amplitudes: ", objs_plp_amp)
#    # Find all unique People schedules
#    all_occ_sches = []
#    all_act_sches = []
#    for j, li_obj in enumerate(objs_peop):
#        pass
#        sche_nm = objs_plp_sch[j]
#        # SB: Doesnt work since names are inconsistent for People schedules
#        #sche_objs = [ o for o in objs_day_sch if sche_nm in get_obj_name(o) ]
#        sche_objs = [ o for o in objs_day_sch if ' Occ ' in get_obj_name(o) ]
#        sche_objs2 = [ o for o in objs_day_sch if ' Activity ' in get_obj_name(o) ]
#        #print("LEN peop SCHE", len(sche_objs) )
#        #print( "FOUND Schedule objects: ", sche_objs )
#        all_occ_sches = all_occ_sches + sche_objs
#        all_act_sches = all_act_sches + sche_objs2
#    # Process/Extract fractional info from all unique Occupancy schedules
#    sche_objs = list( set( all_occ_sches ) )
#    for so in sche_objs:
#        sch_frac_occ = interprete_schedule( so )
#        sch_nm = get_obj_name( so )
#        spl_schnm = sch_nm.split('Occ')[0].strip(' ').strip('_')
#        amplitudes = [ objs_plp_amp[j] for j,nm in enumerate(objs_plp_nm) if spl_schnm in nm]
#        if len(amplitudes) > 1 :
#            printc("Warning: Multiple Amplitudes Found: %s"%( str(amplitudes) ), 'red')
#        elif len(amplitudes)==1 :
#            printc("Multiple Amplitudes Found: %s"%( str(amplitudes) ), 'green')
#        try:
#            amp = float(amplitudes[0])
#        except:
#            amp = 1.0
#        if len(amplitudes)>1 :
#            print( spl_schnm )
#            print( sch_frac_occ, len(sch_frac_occ))
#            print( "Amplitudes: ", amp*array(sch_frac_occ) )
#    # Process/Extract fractional info from all unique Activity schedules
#    # SB: Already multplied out by amplitude
#    sche_objs2 = list( set( all_act_sches ) )
#    for so in sche_objs2 :
#        sch_frac_act = interprete_schedule( so )
#        print( "Amplitudes: ", array(sch_frac_act) )
#
#    #printc('\n*'*num_star, 'blue')
#    printc('\n'+'*'*num_star+'\n', 'blue')
#
#
#    # Infiltration
#    objs_infil=filter_IDF_objs_raw(objs_all, 'ZoneInfiltration:DesignFlowRate')
#    objs_day_sch=filter_IDF_objs_raw(objs_all, 'Schedule:Day:Interval')
#    # Schedule Name
#    objs_inf_sch = [ get_obj_abstract( obj, 3) for obj in objs_infil ]
#    # Assume W/m2
#    objs_inf_amp = [ get_obj_abstract( obj, 7) for obj in objs_infil ]
#    objs_inf_nm = [ get_obj_name( obj) for obj in objs_infil ]
#    print(" Infiltration Names: ", objs_inf_nm)
#    print(" Infiltration Amplitudes: ", objs_inf_amp)
#    # Find all unique infil schedules
#    all_inf_sches = []
#    for j, li_obj in enumerate(objs_infil):
#        sche_nm = objs_inf_sch[j]
#        sche_objs = [ o for o in objs_day_sch if sche_nm in get_obj_name(o) ]
#        #print("LEN infil SCHE", len(sche_objs) )
#        #print( "FOUND Schedule objects: ", sche_objs )
#        all_inf_sches = all_inf_sches + sche_objs
#    # Process/Extract fractional info from all unique infiling schedules
#    sche_objs = list( set( all_inf_sches ) )
#    for so in sche_objs:
#        sch_frac = interprete_schedule( so )
#        sch_nm = get_obj_name( so )
#        spl_schnm = sch_nm.split('Infil')[0].strip(' ').strip('_')
#        amplitudes = [ objs_inf_amp[j] for j,nm in enumerate(objs_inf_nm) if spl_schnm in nm]
#        if len(amplitudes) > 1 : printc("Warning: Multiple Amplitudes Found: %s"%( str(amplitudes) ), 'red')
#        try:
#            amp = float(amplitudes[0])
#        except:
#            amp = 1.0
#        #print( sch_frac, len(sch_frac))
#        #print( "Amplitudes: ", amp*array(sch_frac) )
#        if len(amplitudes)>=1 :
#            print( spl_schnm )
#            print( sch_frac, len(sch_frac))
#            print( "Amplitudes: ", amp*array(sch_frac) )
#
#    printc('\n'+'*'*num_star+'\n', 'blue')
#
#    # Domestic Hot Water Draw Profile (DHW)
#    objs_wtruse=filter_IDF_objs_raw(objs_all, 'WaterUse:Equipment')
#    objs_sch=filter_IDF_objs_raw(objs_all, 'Schedule:Compact')
#    # Schedule Name
#    objs_wu_sch = [ get_obj_abstract( obj, 4) for obj in objs_wtruse ]
#    # Units: m3/s
#    objs_wu_amp = [ get_obj_abstract( obj, 3) for obj in objs_wtruse ]
#    objs_wu_nm = [ get_obj_name( obj) for obj in objs_wtruse ]
#    print(" WaterUse Names: ", objs_wu_nm)
#    print(" WaterUse Amplitudes: ", objs_wu_amp)
#    #
#    # Find all unique infil schedules
#    all_wu_sches = []
#    for j, li_obj in enumerate(objs_wtruse):
#        sche_nm = objs_wu_sch[j]
#        sche_objs = [ o for o in objs_sch if sche_nm in get_obj_name(o) ]
#        #print("LEN infil SCHE", len(sche_objs) )
#        #print( "FOUND Schedule objects: ", sche_objs )
#        all_wu_sches = all_wu_sches + sche_objs
#    # Process/Extract fractional info from all unique infiling schedules
#    sche_objs = list( set( all_wu_sches ) )
#    #for so in sche_objs:
#    #    sch_frac = interprete_compact_schedule( so )
#    #    print("Raw DHW Amplitudes: ", sch_frac)
#    #    sch_nm = get_obj_name( so )
#    #    #spl_schnm = sch_nm.split('Infil')[0].strip(' ').strip('_')
#    #    spl_schnm = sch_nm#.split('DHW Eq')[1].strip(' ').strip('_')
#    #    #amplitudes = [ objs_wu_amp[j] for j,nm in enumerate(objs_wu_nm) if spl_schnm in nm]
#    #    amplitudes = objs_wu_amp
#    #    if len(amplitudes) > 1: printc("Warning: Multiple Amplitudes Found: %s"%( str(amplitudes) ), 'red')
#    #    #amp = float(amplitudes[0])*1000*3600
#    #    try:
#    #        # Convert m3/s to L/hr
#    #        # 1000L/m3, 3600s/hr
#    #        # Units: L/hr
#    #        amp = float(amplitudes[0])*1000*3600
#    #    except:
#    #        amp = 1.0
#    #    print( sch_frac, len(sch_frac))
#    #    print( "Amplitudes: ", amp*array(sch_frac) )
#    #    if len(amplitudes)>=1 :
#    #        print( spl_schnm )
#    #        print( sch_frac, len(sch_frac))
#    #        print( "Amplitudes: ", amp*array(sch_frac) )
#    #        print( "Daily Sum (L/day): ", sum(amp*array(sch_frac)) )
#    #
#    sch_frac = interprete_compact_schedule( sche_objs[0] )
#    print("DHW Schedule Frac: ", sch_frac )
#    for j,nm in enumerate(objs_wu_nm):
#        #sch_nm = get_obj_name( so )
#        ##spl_schnm = sch_nm.split('Infil')[0].strip(' ').strip('_')
#        #spl_schnm = sch_nm#.split('DHW Eq')[1].strip(' ').strip('_')
#        ##amplitudes = [ objs_wu_amp[j] for j,nm in enumerate(objs_wu_nm) if spl_schnm in nm]
#        amplitudes = objs_wu_amp[j]
#        if len(amplitudes) > 1 : printc("Warning: Multiple Amplitudes Found: %s"%( str(amplitudes) ), 'red')
#        #amp = float(amplitudes[0])*1000*3600
#        try:
#            # Convert m3/s to L/hr
#            # 1000L/m3, 3600s/hr
#            # Units: L/hr
#            amp = float(amplitudes)*1000*3600
#        except:
#            amp = 1.0
#        printc( "Daily Hot Water use in '%s': %.1f L/day"%(nm, sum(amp*array(sch_frac)) ), 'blue' )
#        print( "Amplitudes: ", amp*array(sch_frac) )
#        print( "Daily Sum (L/day): ", sum(amp*array(sch_frac)) )


    return new_objs

def add_suite_metering_file(to_file=to_file):
    """Modified version of `add_suite_metering` which creates an IDF output for testing purposes. File output uses suffix `_SuiteMeter.idf` by default."""
    return __abstract_add_objs2file(add_suite_metering, to_file=to_file, suffix='SuiteMeter')

# Goal: Add custom metering for Suite and Common areas
# NOTE: Zones need to have special identifier (OR all non-IDed zones are residential)
def add_suite_metering(objs_all, args={}):
    """Add Suite/Common area metering in appropriate `Zones`. Use to separate out energy meters of residential suites and common areas in reporting.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `None`

    Returns:

    * `new_objs`: genEPJ object list with Suite/Common area metering (Python `List`)
    """
    new_objs=list(objs_all)

    objs_zones=filter_IDF_objs_raw(objs_all, 'Zone')
    #dont_use_lst =["washrm", "corridor", "stairs", "mech", "elec", "tower", "retail", "showers", "storage"]
    #use_lst = [ "guestroom", "hotelroom", "apart" ]
    #if args.has_key('dont_use_lst'):
    if 'dont_use_lst' in args:
        dont_use_lst=args['dont_use_lst']
    else:
        dont_use_lst =["washrm", "corridor", "stairs", "mech", "elec", "tower", "retail", "showers", "storage"]

    zone_nms = [get_obj_name(myobj) for myobj in objs_zones if not is_in(dont_use_lst, get_obj_name(myobj).lower())]
    #zone_nms = [get_obj_name(myobj) for myobj in objs_zones if is_in(use_lst, get_obj_name(myobj).lower())]
    #print(zone_nms)

    mtr_d={ 'timestep': "hourly", }
    output_temp, output_defs =templ.template_meter_output()

    def _sub_suite(objs, mynm, mydict ):
        mtr_suite_nms = list(map( lambda x: mynm+x, zone_nms ))
        for ii in range( len(mtr_suite_nms) ): mydict['var%d'%(ii+1)] = mtr_suite_nms[ii]
        meter_temp,meter_defs=templ.template_meter_custom( N=len(mtr_suite_nms) )
        objs.insert(-1, idf_templater(mydict, meter_temp, meter_defs) )
        mtr_d['var']=mydict['name']
        objs.insert(-1, idf_templater( mtr_d, output_temp, output_defs) )
        return objs

    def _sub_common(objs, mydict):
        meterdec_temp,meterdec_defs=templ.template_meter_decrement()
        objs.insert(-1, idf_templater(mydict, meterdec_temp, meterdec_defs) )
        mtr_d['var']=mydict['name']
        objs.insert(-1, idf_templater( mtr_d, output_temp, output_defs) )
        return objs

    #==============================
    # Total suite electricity usage
    #==============================
    d={'name': "SuiteElectricity",
       'type': "Electricity", }
    new_objs = _sub_suite(new_objs, "Electricity:Zone:", d  )

    #==============================
    # Total common electricity usage
    #==============================
    d={'name': "CommonElectricity",
       'type': "Electricity",
       'src_mtr': "Electricity:Facility",
       'mtr_name': "SuiteElectricity", }
    new_objs = _sub_common(new_objs, d)

    #==============================
    # Suite Light electricity usage
    #==============================
    d={'name': "SuiteLightElectricity",
       'type': "Electricity", }
    new_objs = _sub_suite(new_objs, "InteriorLights:Electricity:Zone:", d  )

    #==============================
    # Common Light electricity usage
    #==============================
    d={'name': "CommonLightElectricity",
       'type': "Electricity",
       'src_mtr': "InteriorLights:Electricity",
       'mtr_name': "SuiteLightElectricity", }
    new_objs = _sub_common(new_objs, d)

    #====================
    # Suite Heating usage
    #====================
    d={'name': "SuiteHeating",
       'type': "Generic", }
    new_objs = _sub_suite(new_objs, "Heating:EnergyTransfer:Zone:", d  )

    #====================
    # Common Heating usage
    #====================
    d={'name': "CommonHeating",
       'type': "Generic",
       'src_mtr': "EnergyTransfer:Facility",
       'mtr_name': "SuiteHeating", }
    new_objs = _sub_common(new_objs, d)

    #====================
    # Suite Cooling usage
    #====================
    d={'name': "SuiteCooling",
       'type': "Generic", }
    new_objs = _sub_suite(new_objs, "Cooling:EnergyTransfer:Zone:", d  )

    #====================
    # Common Cooling usage
    #====================
    d={'name': "CommonCooling",
       'type': "Generic",
       'src_mtr': "EnergyTransfer:Facility",
       'mtr_name': "SuiteCooling", }
    new_objs = _sub_common(new_objs, d)

    #====================
    # Suite Equipment usage
    #====================
    d={'name': "SuiteEquipElectricity",
       'type': "Electricity", }
    new_objs = _sub_suite(new_objs, "InteriorEquipment:Electricity:Zone:", d  )

    #====================
    # Common Equipment usage
    #====================
    d={'name': "CommonEquipElectricity",
       'type': "Electricity",
       'src_mtr': "InteriorEquipment:Electricity",
       'mtr_name': "SuiteEquipElectricity", }
    new_objs = _sub_common(new_objs, d)

    return new_objs


# Originally created for Windmill 8 page summary document
def calc_suite_area(myfile=to_file):
    """ Calculate suite area as a percentage of total conditioned area."""

    objs_all=get_IDF_objs_raw(myfile)

    sql_file=myfile.replace('idf','sql').replace('data_temp/','data_temp/Output/')
    conn = sqlite3.connect(sql_file)
    c = conn.cursor()

    # Total conditioned area
    sql_area="SELECT Value FROM TabularDataWithStrings WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND RowName='Net Conditioned Building Area';"
    # Total Building Area
    #sql_area="SELECT Value FROM TabularDataWithStrings WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND RowName='Total Building Area';"
    bldg_area=float(c.execute(sql_area).fetchone()[0])
    print("Net Conditioned Building Area: %.2f"%(bldg_area))

    # Valid "Suite" zones
    objs_zones=filter_IDF_objs_raw(objs_all, 'Zone')
    #dont_use_lst =["washrm", "corridor", "stairs", "mech", "elec", "tower", "retail", "showers"]
    dont_use_lst =["washrm", "corridor", "stairs", "mech", "elec", "tower", "retail", "showers", "storage"]
    use_lst = [ "guestroom", "hotelroom", "apart" ]
    zone_nms = [get_obj_name(myobj) for myobj in objs_zones if not is_in(dont_use_lst, get_obj_name(myobj).lower())]
    #printc("Valid Zone Names: %s"%(str(zone_nms)), 'blue')

    # Valid zone floor area
    sql_sel_zonenm='select SUM(a.GrossArea) FROM Surfaces AS a, Zones AS b WHERE a.ClassName=="Floor" AND a.ZoneIndex==b.ZoneIndex AND b.ZoneName=="%s";'

    def _mycalc_area(zn):
        res = c.execute(sql_sel_zonenm%(zn.upper())).fetchone()
        #print("Raw Res: ", res)
        if len(res)>1 :
            printc("WARNING! More than one area returned for Zone %s"%(mkcolor(zn, "blue")), "yellow")
        a1=res[0]
        a1 = zeroIfNone(a1)
        return a1

    areas = list( map( _mycalc_area, zone_nms ))
    #printc("Valid Zone Areas: %s"%(str(areas)), 'blue')

    # Divide Suite area by Total Conditioned area
    printc("Buiding Area: %s"%(mkcolor("%.2f"%(bldg_area), "blue")), "yellow")
    printc("Suite Area: %s"%(mkcolor("%.2f"%(sum(areas)), "blue")), "yellow")
    printc("Frac Suite Area: %s"%(mkcolor("%.4f"%(sum(areas)/bldg_area), "blue")), "yellow")

    return [bldg_area, sum(areas)/bldg_area]

def setup_global_thermostat_ENVE4107_file(to_file=to_file):
    """Modified version of `setup_global_thermostat_ENVE4107` which creates an IDF output for testing purposes. File output uses suffix `_thermo4107.idf` by default."""
    return __abstract_add_objs2file(setup_global_thermostat_ENVE4107, to_file=to_file, suffix='thermo4107')

def setup_global_thermostat_ENVE4107(objs_all, args={'bldgtype': 'multi-residential'}):
    """
    Automation of tasks to showcase adding an mechancial system to IDF in class
    """

    new_objs=list(objs_all)

    if 'bldgtype' in args :
        bldg_type = args['bldgtype']
    else:
        printc("Building type not specfied, defaulting to residential", 'red')
        bldg_type = 'multi-res'

    if bldg_type == 'multi-residential':
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()
    else:
        txt_thermsch_global_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_comm()
        txt_thermsch_global_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_comm()

    # Heating/Cooling Setpoint Schedules
    thermo_nm="All Zones10"
    heatsp_nm="Htg-SetP-Sch10"
    coolsp_nm="Clg-SetP-Sch10"
    printc("Adding global HVACTemplate:Thermostat and Schedules", 'green')
    new_objs.insert(-1, idf_templater({"name": heatsp_nm}, txt_thermsch_global_heat, tempsch_def_heat) )
    new_objs.insert(-1, idf_templater({"name": coolsp_nm}, txt_thermsch_global_cool, tempsch_def_cool) )
    # Main thermostat
    d={
        "thermo_nm": thermo_nm,
        "hsp_sche": heatsp_nm,
        "csp_sche": coolsp_nm,
    }
    thermo_temp,thermo_defs=templ.HVACtemplate_thermostat()
    new_objs.insert(-1, idf_templater(d, thermo_temp, thermo_defs ) )

    return new_objs

# ********* START resilience features *********
def calc_prepostsim_days(bldg_area):
    """Return the recommended number of pre/post-simulation duration (days) for outage events (based on the buildings size- area used as a proxy for size). A linear interpolation is used based on two tested buildings (a tiny home and a 28 unit MURB)

    Used in resilience simulations


    Parameters:

    * `bldg_area`: building area

    Returns:

    * `presim_time_day`: Recommended pre-simulation duration (days)
    * `postsim_time_day`: Recommended post-simulation duration (days)
    """

    # NOMAD
    #_presim_time_day=14 # Buffer to presimulate (E+ recommends minimal 5 days, max 25 days)
    #_postsim_time_day=1 # Buffer to postsimulate (lets the building recover)
    # EVE PARK
    #_postsim_time_day=2 # Buffer to postsimulate (lets the building recover)
    #_presim_time_day=30 # Buffer to presimulate (E+ recommends minimal 5 days, max 25 days)

    # Presim period
    area_nomad=26.05# m2
    presim_nomad=14. # days
    area_evepark=3546.93
    presim_evepark=30. # days
    # Presim period
    postsim_nomad=1. # days
    postsim_evepark=2. # days

    m=(presim_evepark-presim_nomad)/(area_evepark-area_nomad)
    b=presim_nomad-m*area_nomad

    def f(x):
        value=m*x+b
        return round(value, 0)
    _presim_time_day=f(bldg_area)

    m2=(postsim_evepark-postsim_nomad)/(area_evepark-area_nomad)
    b2=postsim_nomad-m*area_nomad
    def f2(x):
        value=m2*x+b2
        return round(value, 0)
    _postsim_time_day=f2(bldg_area)
    return _presim_time_day,_postsim_time_day

def add_resiliency_battery_file(to_file=to_file):
    """Modified version of `add_resiliency_battery` which creates an IDF output for testing purposes. File output uses suffix `_resilbatt.idf` by default."""
    return __abstract_add_objs2file(add_resiliency_battery, to_file=to_file, suffix='resilbatt')

def add_resiliency_battery(objs_all, args={'zone_name': None}):
    """Add E+ `ElectricLoadCenter:Storage:Battery` and grid `Transformer` in specified `Zone` with a scheduled outage.
    Function enables the simulation of grid outages and subsequent comfort/power quality concerns to evaluate a building's resiliency.
    Battery used is a simple battery with user defined size (modelled using a `ElectricLoadCenter:Storage:Simple` object)
    Alternatively, any number of Telsa powerwalls (circa 2018) with 6kWh of storage per cell can be specified (modelled using a `ElectricLoadCenter:Storage:Battery` object).

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `zone_name`- Zone where batteries are stored (heat is gained), `num_batt`- Number of Tesla style batteries, `batt_size`- total battery size (only if `num_batt` not specified)

    Returns:

    * `new_objs`: genEPJ object list with Battery and Grid Transformer (Python `List`)
    """

    if 'file_name' in args:
        global c # used below by calc_area
        c=get_sql_database( myfile=args['file_name'] )
    else:
        c=guessdb_ifnot_found()
    sql_area="SELECT Value FROM TabularDataWithStrings WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND RowName='Total Building Area';"
    bldg_area=float(c.execute(sql_area).fetchone()[0])

    new_objs=list(objs_all)

    zone_name=args['zone_name']
    if not(zone_name):
            raise ValueError("User must specify `zone_name' for inverter/batteries to be located")

    if 'battery_type' in args:
        battery_type=args['battery_type']
    else:
        battery_type='Simple'

    # Battery sized using one of two approaches: Number of batteries in series (determines cells) OR total battery size (determines battery Amperage)
    d={}
    if 'num_batt' in args:
        d['num_batt']=args['num_batt']
    elif 'batt_size' in args:
        batt_size=float(args['batt_size'])
        d['capacity']=batt_size*1e3/350. # kWh*1000 -> Wh. Wh/V->Ah (units needed by E+)

    if ( 'num_batt' in args ) and ('batt_size' in args):
        raise ValueError("Function allows for defined number of batteries OR total battery size NOT BOTH.")


    pv_list=args['pv_list']
    inverter_name=args['inverter_name']
    if 'battavail_sche' in args :
        battavail_sche=args['battavail_sche']
    else:
        battavail_sche="ALWAYS ON PV 2"

    from datetime import datetime, timedelta
    def _get_month_day_from_hour(hr):
        "Return a datetime object from a given hour integer"
        if hr<0: hr=0 # Datetime will rewind clock to previous year. E+ doesn't consider start/end year by default
        _yr=datetime.now().year
        _jan1=datetime(_yr, 1, 1)
        _delta_hrs=timedelta(hours=hr)
        _dt=_jan1+_delta_hrs
        return _dt.month, _dt.day, _dt.hour
    #grid_trans_d={}

    flag_resil=False
    flag_outage=False
    if ( 't_resil_start' in args ) and ( 't_resil_stop' in args ):
        flag_resil=True
        # Test for minimal duration
        _t_outage=args['t_resil_stop']-args['t_resil_start']
        #TESTING<24hrs
        #if _t_outage<24 :
        #    raise ValueError("Minimal outage period must be greater then 24 hours. Presently set to %.1f"%(_t_outage))
        # Set RunPeriod
        _buffer_time_hr=12 # Buffer to oversimulate by (applied to start/end times)

        _presim_time_day,_postsim_time_day=calc_prepostsim_days(bldg_area)

        _st_mnth_sim, _st_day_sim, _st_hr_sim = _get_month_day_from_hour( int(args['t_resil_start'])-_buffer_time_hr - _presim_time_day*24 )
        _stp_mnth, _stp_day, stp_hr = _get_month_day_from_hour( int(args['t_resil_stop'])+_buffer_time_hr+_postsim_time_day*24 )
        print( {'end_mnth':_stp_mnth, 'end_day': _stp_day, 'start_mnth':_st_mnth_sim, 'start_day':_st_day_sim} )
        new_objs=change_run_period(new_objs, {'end_mnth':_stp_mnth, 'end_day': _stp_day, 'start_mnth':_st_mnth_sim, 'start_day':_st_day_sim})
        # Add Outage name to transformer dictionary
        #grid_trans_d['name']="Loss of Power Schedule"
    if 'outage_flag' in args:
        flag_outage=args['outage_flag']

    #else:
    #    grid_trans_d['name']=battavail_sche

    # SB- Need to remove existing: 'ElectricLoadCenter:Distribution' from PV generators
    new_objs= [obj for obj in new_objs if 'electricloadcenter:distribution' not in get_obj_type(obj).lower()]

    trans_dict={
       'zone_name': zone_name,
       'inverter_name': inverter_name,
       'pv_list': pv_list,
       'battavail_sche': battavail_sche,
       #'battery_name': "",
    }
    if ('sensor_elec' in args) and ('sensor_suffix' in args):
        trans_dict['sensor_elec']=args['sensor_elec']
        trans_dict['sensor_suffix']=args['sensor_suffix']
    if ('batt_type' in args) :
        trans_dict['batt_type']=args['batt_type']

    txt_trans_templ, trans_def = templ.Equipment_ONOFFGrid_Transformer()
    new_objs.insert(-1, idf_templater(trans_dict, txt_trans_templ, trans_def) )

    d['zone_location']= zone_name
    d['schedule']=battavail_sche

    if battery_type=='Detailed':
        # Detailed Battery
        txt_batt_templ, batt_def = templ.Equipment_ONOFFGrid_Battery()
        _obj=idf_templater( d, txt_batt_templ, batt_def)
    else:
        # Simple Battery
        d['capacity_joule']=batt_size*3.6e6 # kWh -> J (Needed by E+)
        d['init_charge_joule']=d['capacity_joule']
        txt_batt_templ, batt_def = templ.Equipment_ONOFFGrid_BatterySimple()
        _obj=idf_templater( d, txt_batt_templ, batt_def)

    if flag_resil: # Add in EMS programs to switch off loads
        _txt="""MyComputedLightsProg,
             MyComputedEquipProg,
             MyComputedDHWProg,
             MyComputedHVACAvailProg;
        """
        _obj.replace('MyComputedHVACAvailProg;', _txt)
        new_objs.insert(-1, _obj )
    else:
        new_objs.insert(-1, _obj )


    # Resil Event: Add Schedule for Outage
    if flag_resil:
        _st_mnth, _st_day, _st_hr   = _get_month_day_from_hour( int(args['t_resil_start']))
        _st_mnth_b4, _st_day_b4, _st_hr_b4   = _get_month_day_from_hour( int(args['t_resil_start']-24)) #day before
        _stp_mnth, _stp_day, _stp_hr = _get_month_day_from_hour( int(args['t_resil_stop']))
        _stp_mnth_b4, _stp_day_b4, stp_hr_b4 = _get_month_day_from_hour( int(args['t_resil_stop']-24))
        _d={}
        _d['date_start']="%d/%d"%(_st_mnth, _st_day)
        _d['time_start']="%d"%(_st_hr)+":00"
        _d['date_start_b4']="%d/%d"%(_st_mnth_b4, _st_day_b4)
        _d['date_end']="%d/%d"%(_stp_mnth, _stp_day)
        _d['date_end_b4']="%d/%d"%(_stp_mnth_b4, _stp_day_b4)
        _d['time_end']="%d"%(_stp_hr)+":00"

        # Filter out prev thermostat settings (override to constant)
        ## Need to join list (several IDF objects defined in prev templates)
        new_objs=get_IDF_objs_raw(new_objs)
        #print([_o for _o in new_objs if (get_obj_type(_o)=='Schedule:Compact') and (heatsp_nm in get_obj_name(_o))])
        #print([_o for _o in new_objs if (get_obj_type(_o)=='Schedule:Compact') and (coolsp_nm in get_obj_name(_o))])
        new_objs=[_o for _o in new_objs if not ((get_obj_type(_o)=='Schedule:Compact') and (heatsp_nm in get_obj_name(_o)))]
        new_objs=[_o for _o in new_objs if not ((get_obj_type(_o)=='Schedule:Compact') and (coolsp_nm in get_obj_name(_o)))]
        _d_thermo_heat={
           "name": heatsp_nm,
           "setback":  "20.0",
           "ramp":     "20.0",
           "setpoint": "20.0",
        }
        _d_thermo_cool={
           "name": coolsp_nm,
           "setback":  "25.0",
           "ramp":     "25.0",
           "setpoint": "25.0",
        }
        txt_thermsch_heat, tempsch_def_heat = templ.HVACtemplate_thermosche_heat_resi()
        txt_thermsch_cool, tempsch_def_cool = templ.HVACtemplate_thermosche_cool_resi()
        new_objs.insert(-1, idf_templater( _d_thermo_heat, txt_thermsch_heat, tempsch_def_heat) )
        new_objs.insert(-1, idf_templater( _d_thermo_cool, txt_thermsch_cool, tempsch_def_cool) )

        if 'sche_payload' in args:
            _sches=args['sche_payload']
        else:
            raise ValueError("User must specify all schedules to be turned OFF during power outage")

        def _get_schedule_type( sche_name ):
            _o = [o for o in new_objs if ( ('Schedule:' in get_obj_type(o)) and (get_obj_name(o) == sche_name) )]
            #print(_o)
            return get_obj_type(_o[0])
        # Is DHW Heater all Electric?
        _flag_DHWNG= any([True for o in new_objs if ((get_obj_type(o)=='WaterHeater:Mixed') and (get_obj_abstract(o,11).upper()=='NATURALGAS'))])

        _templ="     MyComputed%sProg"
        _progs=[]
        for _key in _sches.keys():
            _d_EMS=_sches[_key]

            # Add other details for EMS per Load
            _d_EMS['act_name']="my%s_Override"%(_key)
            _d_EMS['sens_name']="%s_sche"%(_key.lower())
            _d_EMS['prog_name']="MyComputed%sProg"%(_key)
            ## Extract Schedule type
            #print( "TEST",_sches[_key])
            #print( "TEST",_d_EMS['sche_name'])
            #print( "TEST",_get_schedule_type( _d_EMS['sche_name'] ))
            _d_EMS['sche_type']=_get_schedule_type( _d_EMS['sche_name'] )


            txt_EMSperload_templ, EMSperload_def = templ.EMS_SensorActuator_perLoad()
            if 'min_SoC_kWh' in args:
                _d_EMS['min_SoC']=args['min_SoC_kWh']

            if 'DHW' in _key and _flag_DHWNG: # DONT  ADD DHW if NaturalGas fuel type
                continue # No EMS overrides for NG DHW 
            elif not flag_outage: # outage NOT scheduled. Override user specified defaults with 'recovered' values
                # Get building to act as though there is a battery charge (NO OUTAGE). Keeps A/B comparison exact
                _d_EMS['act_outage']=_d_EMS['act_batt'] # Override '0' settings
            #else: # outage is scheduled. Keep user specified defaults
            new_objs.insert(-1, idf_templater( _d_EMS, txt_EMSperload_templ, EMSperload_def) )
            _progs.append(_templ%(_key))

        # Finally, add all EMS details to IDF
        ## Add EMS Program as a text blog
        _d['ems_progblob']= ",\n".join(_progs)
        #print("Prog:",_progs)
        print("CHECK dates and are NOT equal?",_d['date_start'], _d['date_end'], _d['date_start'] != _d['date_end'])
        if _d['date_start'] == _d['date_end_b4'] :
            txt_scheavail_templ, scheavail_def = templ.SchedulesOutagesOneDay()
        elif _d['date_start'] == _d['date_end'] :
            txt_scheavail_templ, scheavail_def = templ.SchedulesOutagesSameDay()
        else:
            txt_scheavail_templ, scheavail_def = templ.SchedulesOutagesMultiDay()
        new_objs.insert(-1, idf_templater( _d, txt_scheavail_templ, scheavail_def) )

        # EMS Verbose Output *.edd file
        #if options.debugelec:
        #    txt_emsverbose_templ, emsverbose_def = templ.EMS_VerboseOutputs()
        #    new_objs.insert(-1, idf_templater( {}, txt__emsverbose_templ, emsverbose_def) )
        txt_emsverbose_templ, emsverbose_def = templ.EMS_VerboseOutputs()
        new_objs.insert(-1, idf_templater( {}, txt_emsverbose_templ, emsverbose_def) )

    return new_objs


def mod_resiliency_thermostat(objs_all, args={}):

    # Reprocess objects in case there are some string blocks still present
    new_objs=get_IDF_objs_raw(objs_all)

    ## How we determine if heating or cooling is required
    #heating_end= 105    # April 15th; NOTE default in genEPJ is Jun1st
    #heating_start= 273 # Sept 15th; NOTE default in genEPJ is Oct 1st

    t_start=args['t_resil_start']
    # TODO- add override on Htg/Clg thermo stat if its a cooling event_type outside of Jun/01-Oct/1
    event_type=args['event_type']
    t_precond=args['t_precon'] # Time in hours to precondition b4 the outage
    temp_preheat=args['temp_preheat'] # Temperature to precondition to
    temp_precool=args['temp_precool'] # Temperature to precondition to
    year=args['year'] # Year of outage event (want to translated hr into correct MM/DD/HH)


    # Alternatively, get temperature setpoint from schedule
    from datetime import datetime, timedelta
    _jan1=datetime(year, 1, 1)

     # Exact start time of the outage (ie. when our preset should END)
    _delta_hrs=timedelta(hours=t_start)
    _dt_outage=_jan1+_delta_hrs
    _outage_hr= _dt_outage.hour
    _dt_yday=_dt_outage.timetuple().tm_yday # 1-365 days

     # Start time of preheat/cool (ie. when our preset should START)
    _delta_hrs_pre=timedelta(hours=(t_start-t_precond))
    _dt_preheat=_jan1+_delta_hrs_pre # Time that we start preheating at (which is hours prior to outage)
    _outage_preheat_hr = _dt_preheat.hour
    _dt_pre_yday=_dt_preheat.timetuple().tm_yday # 1-365 days

    #Schedule:Compact,
    #  Htg-SetP-Sch10,            !- Name
    #def _extract_setpoint(nm):
    #    objs = [obj for i,obj in enumerate(new_objs) if get_obj_type(obj)=='Schedule:Compact' and nm in obj]
    #    obj=objs[0]
    #if heating_end < _dt_yday < heating_start:
    if "cool" in event_type:
        # Hot weather outage
        temp="25" #degC
        temp_pre=temp_precool
        nm=coolsp_nm
    else:
        # Cold weather outage requiring heating
        temp="20" #degC
        temp_pre=temp_preheat
        nm=heatsp_nm

    _d_thermo_override={
       "name": nm,
       "modtemp": temp_pre,
       "temp":    temp, #degC of regular setpoint

       # Pre-condition start time
       "day_str":  str(_dt_pre_yday),  # Day that preset starts
       "time_str":  str(_outage_preheat_hr), # Time that preset starts

       # Pre-condition end time (outage has begun)
       "day_stp":  str(_dt_yday),  #  Day that preset stops
       "time_stp":  str(_outage_hr), # Time that preset stops
    }

    txt_thermsch_override, tempsch_def_override = templ.HVACtemplate_thermosche_preoutagemod()
    new_objs.insert(-1, idf_templater( _d_thermo_override, txt_thermsch_override, tempsch_def_override) )

    # Add new program to CallingManager
    obj_idxs = [i for i,obj in enumerate(new_objs) if get_obj_type(obj)=='EnergyManagementSystem:ProgramCallingManager' and "My Schedule Calculator Example" in obj]
    ems_idx=obj_idxs[0]
    ems_obj=new_objs[ems_idx]
    #print("FOUND IDX: %d"%(ems_idx))
    #print("FOUND obj %s"%(ems_obj))

    _txt="""MyComputedDHWProg,
     MyComputedOverrideSetpoint;
"""
    ems_obj=ems_obj.replace('MyComputedDHWProg;', _txt)
    new_objs[ems_idx]=ems_obj
    #print("MOD obj %s"%(ems_obj))

    return new_objs

# ********* END resilience features *********

def check_model_file(to_file=to_file):
    """Modified version of `check_model` which creates an IDF output for testing purposes. File output uses suffix `_checkModel` by default."""
    return __abstract_add_objs2file(check_model, to_file=to_file, suffix='checkModel')

def check_model(objs_all, args={"interactive": True, "epw": "CAN_ON_Ottawa.716280_CWEC.epw", "idf": None}):
    """Assess if the provided building has the minimal required information to run in genEPJ

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`:
        * `interactive:` Allow for end-user feedback if selected options are correct
        * `epw:` EPW weather file that will be used
        * `idf:` IDF to test genEPJ functions on

    Returns:

    * `new_objs`: genEPJ object list (identical to input to allow for function chaining in genEPJ)
    """

    if 'interactive' in args:
        interactive=args['interactive']
    else:
        interactive=False

    global myfail
    global mywarn
    myfail=False
    mywarn=False
    global tests_passed
    global tests_failed
    tests_passed=0
    tests_failed=0

    def _get_first(mylst):
        try:
            return mylst[0]
        except:
            #return "Failed2FindObject"
            return "FakeObj, Fake Name;"
    #print("Before Length: %d"%len(objs_all))
    #def try2filter(nm):
    #    try:
    #        _objs=[ o for o in objs_all if get_obj_type(o).lower()==nm.lower() ]
    #    except:
    #        print("No objects found for '%s'."%(nm))
    #        return [ "FakeObj, Fake Name;" ]
    #    return _objs

    try2filter=lambda x: [ o for o in objs_all if get_obj_type(o).lower()==x.lower()]
    _tabs=""
    def assert_len(nm,_len=0):
        _objs = try2filter(nm)
        assert_compare(nm, len(_objs) != _len)
        #print("Failed state: %s"%str( myfail))
        #try:
        #    _objs = try2filter(nm)
        #    assert len(_objs) != _len, "`%s' needs to be defined if modifying object"%(nm)
        #    printc("Y.... `%s'%s check model passed"%(nm,_tabs), 'green')

        #except AssertionError:
        #    printc("X.... `%s'%s check model FAILED"%(nm,_tabs), 'red')
        #    myfail=True

    def assert_compare(mytype, bool_exp):
        global myfail
        global tests_passed
        global tests_failed
        try:
            assert bool_exp, "`%s' needs to be defined if modifying object"%(type)
            printc("Y.... `%s'%s check model passed"%(mytype,_tabs), 'green')
            tests_passed+=1
        except AssertionError:
            printc("X.... `%s'%s check model FAILED"%(mytype,_tabs), 'red')
            myfail=True
            tests_failed+=1

    # Pass if regex matches. Fail if not
    def assert_regex(obj,line,myregex):
        global myfail
        global tests_passed
        global tests_failed
        _type= get_obj_type( obj )
        printc("..... `%s': REGEX `%s' applied to line `%s' "%(_type.upper(), myregex,line), 'yellow')
        try:
            result=myregex.findall(line)
            assert len(result) >= 0, "Regex `%s' needs to match"%(myregex)
            printc("Y.... `%s'%s check model passed"%(_type,_tabs), 'green')
            tests_passed+=1

        except AssertionError:
            printc("X.... `%s'%s check model FAILED"%(_type,_tabs), 'red')
            myfail=True
            tests_failed+=1

    def assert_check(nm):
        global myfail
        global mywarn
        global tests_passed
        global tests_failed
        #print("Failed state: %s"%str( myfail))
        try:
            if interactive:
                resp=input("y/Y/n/N:")
                assert (( resp != "n" ) and ( resp != "N" )),\
                  "`%s' needs to be defined by end-user"%(nm)
                printc("Y.... `%s'%s check model passed"%(nm,_tabs), 'green')
                tests_passed+=1
            else:
                printc("~.... `%s'%s check model SKIPPED"%(nm,_tabs), 'yellow')
                mywarn=True
        except AssertionError:
            printc("X.... `%s'%s check model FAILED"%(nm,_tabs), 'red')
            myfail=True
            tests_failed+=1

    def has_utf8(filepath):
        """Returns True if file contains non-ASCII UTF-8 characters"""
        with open(filepath, 'rb') as f:
            return any(b > 127 for b in f.read())

    # TODO- Check that runperiod has no Year and that simday starts on a Sunday
    # TODO-  Check that all comments have been removed  "!-   ======". OR strip comments in function?
    # TODO-  Check that resil.json has indices in order (1, 2, 3...)

    printc("Checks system variables", 'yellow')
    ep_dir=environ['ENERGYPLUS_DIR']
    wf_dir = environ['ENERGYPLUS_WEATHER']
    assert_compare("ENERGYPLUS_DIR set"     , len(ep_dir)>0)
    assert_compare("ENERGYPLUS_WEATHER set" , len(wf_dir)>0)

    printc("Checks for geometry", 'yellow')
    assert_len('BuildingSurface:Detailed')

    printc("Checks for `ZoneList'", 'yellow')
    assert_len('ZoneList')

    printc("Checks for Objects for common substitutions", 'yellow')
    assert_len('Lights') # LPD
    assert_len('ElectricEquipment') # Plug loads
    assert_len('ZoneInfiltration:DesignFlowRate') # Infiltration: L/s/m2 [m3/s/m2]

    printc("Checks for `BuildingSurface:Detailed'", 'yellow')
    # NOTE: Match order of container object
    cons_types=['Roof'    , 'Wall'    , 'Wall'   , 'Wall'    , 'Ceiling' , 'Floor'   , 'Floor'  , 'Floor',      'Window']
    cons_bound=['Outdoors', 'Outdoors', 'Ground' , 'Surface' , 'Surface' , 'Surface' , 'Ground' , 'Foundation']

    bldgsurfs_objs = try2filter('BuildingSurface:Detailed')
    for surf in bldgsurfs_objs:
        surf_nm=get_obj_name(surf)
        surf_type=get_obj_abstract(surf, 2)
        surf_BC=get_obj_abstract(surf, 6)

        # TEST- Type matches
        test_type=not is_in(cons_types, surf_type)
        # assert_compare if DOESNT match (ignore test if it does)
        if test_type: assert_compare(surf_nm+'>'+surf_type, False)

        # TEST- Boundary Condition
        test_BC=not is_in(cons_bound, surf_BC)
        # assert_compare if DOESNT match (ignore test if it does)
        if test_BC: assert_compare(surf_nm+'>'+surf_BC, False)

    printc("Checks for Sizing/Location", 'yellow')
    assert_len('SizingPeriod:DesignDay')
    assert_len('Site:Location')
    # Commonly not modified by an end-user. Confirm this is what they want
    _loc_nm= get_obj_name( _get_first(try2filter('SizingPeriod:DesignDay')) )
    _loc_nm= " ".join(_loc_nm.split(' ')[0:3])+ "..."
    printc("~... is `%s' your desired Location for DesignDay?"%(_loc_nm), 'blue')
    assert_check("SizingPeriod:DesignDay Location")

    printc("Checks for E+ Version", 'yellow')
    # TEST- IDF Version differ from $ENERGYPLUS_DIR?
    eplus_vers = environ['ENERGYPLUS_DIR']
    vers_ma=eplus_dir.split('-')[1]
    vers_mi=eplus_dir.split('-')[2]
    _vers_obj= _get_first(try2filter('Version')).replace(';','')
    printc("... VERSION: Comparing: `%s' to `%s'"%( get_obj_name(_vers_obj), vers_ma+'.'+vers_mi), 'yellow')
    assert_compare('VersionIDF_vs_VersionEnviro', get_obj_name(_vers_obj) == vers_ma+'.'+vers_mi)

    #printc("Check that EnergyPlus runs on file and creates output", 'yellow')
    #_fnm=mkstemp('_testEPLUS')[1]+'.idf'
    #fname=write_file(objs_all, _fnm)
    #maybe_call_eplus(fname, args['epw'], force_resim=True, run_eplus=True, convert=False)
    ## SB- Don't worry about cleaning up as genEPJ uses _prep.idf for simulation work. Chicago sim shouldn't negatively affect outcomes
    ## rmtree(join('data_temp', 'Output')

    printc("Checks EPW/DDY", 'yellow')
    print(args['epw'])
    try:
        args['epw']
        assert_compare("EPW specified in check_model", True)
    except:
        assert_compare("EPW specified in check_model", False)
    wf_dir = environ['ENERGYPLUS_WEATHER']
    _e=join(wf_dir, args['epw'])
    _d=_e.replace('epw','ddy')
    assert_compare("EPW exists", isfile(_e))
    assert_compare("DDY exists", isfile(_d))
    assert_compare("UTF8 in EPW", not has_utf8(_e))
    assert_compare("UTF8 in DDY", not has_utf8(_d))

    printc("Checks for HTML Reports", 'yellow')
    assert_len('OutputControl:Table:Style')
    _html_obj= _get_first(try2filter('OutputControl:Table:Style'))
    assert_regex(_html_obj, get_obj_name(_html_obj), re.compile(r'CommaAndHTML'))
    assert_regex(_html_obj, get_obj_type(_html_obj), re.compile(r'JtoKWH'))

    printc("Checks for HTML Reports", 'yellow')
    assert_len('OutputControl:Table:Style')
    _output_obj= _get_first(try2filter('Output:Table:SummaryReports'))
    assert_regex(_output_obj, get_obj_type(_output_obj), re.compile(r'AllSummary'))

    # TEST- SQL check for file
    printc("Checks for SQL db", 'yellow')
    assert_len('Output:SQLite')
    _sql_obj= _get_first(try2filter('Output:SQLite'))
    assert_regex(_sql_obj, get_obj_type(_sql_obj), re.compile(r'SimpleAndTabular'))
    # SB: Errors sometimes occur here if testing on source IDF before 'prep.idf' is created. prep needs to be created AND run to work. Hack to sub for SQL db if need be
    try:
        c=guessdb_ifnot_found()
    except:
        idfs=glob('*.idf')
        #print(idfs)
        _idf=sorted(idfs, key=len)[0]
        _sql=join('data_temp','Output', _idf.replace('.idf','.sql'))
        if isfile(_sql):
            # Copy over existing SQL file
            copyfile(_sql, _sql.replace('.sql','_prep.sql'))
            c=guessdb_ifnot_found()
        else:
            printc("X.... Database NOT found. Add SQL to Outputs", 'red')
    printc("Y.... Database Found", 'green')
    # SQL TEST- SQL file has geometry details
    sql_area="SELECT Value FROM TabularDataWithStrings WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND RowName='Total Building Area';"
    try:
        bldg_area=float(c.execute(sql_area).fetchone()[0])
    except:
        bldg_area=0.000000000
    printc("~... AREA: is `%.1f m2' the approximate area of the building?"%(bldg_area), 'blue')
    assert_check("SQL file")

    printc("Checks for `People/Ventilation/DOAS'", 'yellow')
    # People schedule is as expected for add_HVAC_DOAS
    printc("Checks for `People' objects", 'yellow')
    assert_len('People')

    # DOAS People Schedule
    printc("Checks for DOAS `Occupancy' objects", 'yellow')
    occ_plp=match_occupancy_schedule(objs_all)[0]
    plp_nm= get_obj_name(occ_plp)
    printc("~... is `%s' your desired 'People' occupancy schedule?"%(plp_nm) , 'blue')
    assert_check(plp_nm)

    # TEST- Need 'Apartment/Commercial' in People object name for DOAS to match building type
    _plp_obj= _get_first(try2filter('People'))
    _plp_nm= get_obj_name( _plp_obj )
    _regex=re.compile(r'Apartment|Commer')
    assert_regex(_plp_obj, _plp_nm, _regex)

    printc("Checks for `Resilency Events'", 'yellow')
    resil_fname="resiliency_events.json"
    if not isfile(resil_fname):
        resil_fname=join('resiliency', "resiliency_events.json")
    if not isfile(resil_fname):
        printc("Skipping 'resiliency_events.json' tests. File not found", 'yellow')

    if isfile(resil_fname):
        with open(resil_fname, 'r') as f:
            import json
            resil_json=json.loads(f.read())
            # TODO- get json keys
            #json_keys=[ "ice-storm", "heat-wave" ]
            json_keys=list( resil_json.keys() )
            for event_key in json_keys:
                #hvac_sche=resil_json[event_key]["sches_turnoff"]["HVACAvail"]["sche_name"]
                li_sche=resil_json[event_key]["sches_turnoff"]["Light"]["sche_name"]
                eq_sche=resil_json[event_key]["sches_turnoff"]["Equip"]["sche_name"]
                dhw_sche=resil_json[event_key]["sches_turnoff"]["DHW"]["sche_name"]
                idf_txt='\n'.join( objs_all )
                li_matches= len( re.findall(r'%s,'%(li_sche), idf_txt ) )
                eq_matches= len( re.findall(r'%s,'%(eq_sche), idf_txt ) )
                # TEST for prop only...
                #hvac_matches= len( re.findall(r'%s,'%(hvac_sche), idf_txt ) )
                #dhw_matches= len( re.findall(r'%s,'%(dhw_sche), idf_txt ) )

                assert_compare(event_key+":"+li_sche, li_matches>=1)
                assert_compare(event_key+":"+eq_sche, eq_matches>=1)

    printc("Checks for libraries/modules", 'yellow')
    try:
        import eppy
        assert_compare('EPPY Installed', True)
    except ModuleNotFoundError:
        assert_compare('EPPY NOT Installed', False)

    try:
        import pyenergyplus
        assert_compare('Python supported: pyenergyplus found', True)
    except ModuleNotFoundError:
        python_enabled=False
        assert_compare('Python NOT supported: pyenergyplus found', False)

    try:
        import torch
        assert_compare('PyTORCH Installed', True)
        printc("GPU Available?: %s"%(str(torch.cuda.is_available())), 'green')
        if torch.cuda.is_available(): print( "Device Name: ", torch.cuda.get_device_name() )
    except ModuleNotFoundError:
        assert_compare('PyTORCH NOT Installed', False)

    if which('modelkit'):
        assert_compare('ModelKit Installed', True)
    else:
        assert_compare('ModelKit NOT Installed/Found in PATH', False)

    if which('openstudio'):
        assert_compare('OpenStudio Installed', True)
    else:
        assert_compare('OpenStudio NOT Installed/Found in PATH', False)

    # Run all tests on this file from using genEPJ functions. Raise issue if <95% of functions pass
    printc("Checks for genEPJ function compatability", 'yellow')
    if not sys.platform.startswith('win'):
        myfile=args['idf']
        with open("/tmp/output.txt", "w") as g:
            run(["./genEPJ/standalone/run_genEPJ_functions.sh", myfile], stdout=g, stderr=g, check=True)
        # Define the results file path
        results_file = Path("tests/RESULTS.txt")

        # Check if the file exists
        assert_compare("run_genEPJ_functions.sh: Results file found", results_file.exists())

        # Read and parse the file
        with open(results_file, 'r') as f:
            content = f.read()
            print(content)
            try:
                num_tests = int(content.split("TOTAL TESTS:")[1].split()[0])
                pass_percent = float(content.split("% Passes:")[1].split()[0])
                tests_passed=tests_passed+pass_percent/100.*num_tests
                tests_failed=tests_failed+(1-pass_percent/100.)*num_tests
                assert_compare("run_genEPJ_functions.sh: Test number check (>50)", num_tests>50)
                assert_compare("run_genEPJ_functions.sh: Passed test check (>95%)", pass_percent>95)
            except:
                raise ValueError("Could not find '% Passes:' in `tests/RESULTS.txt'")
    else:
        printc("Unable to run tests on windows", 'yellow')

    # SB- Allows for option to make changes in to IDF from within check_model. Presently not used
    if 'modify' in args:
        objs_all=new_objs

    printc("\nCombined check_model and genEPJ tests:", 'yellow')
    #print("After Length: %d"%len(objs_all))
    #Overlay genEPJ tests with check_model tests
    printc(f"Total Test results: Checked: {tests_passed + tests_failed:.0f}, Passed: {100 * tests_passed / (tests_passed + tests_failed):.1f}%", "blue")
    if myfail:
        printc("***Some checks FALIED***", 'red')
    elif mywarn:
        printc("All checks passed (with WARNING)", 'yellow')
    else:
        printc("All checks passed", 'green')

    return objs_all
    #return new_objs



# Prev version of EnergyPlus
def get_prev_version(myma, mymi) :
    """Return the prior version of EnergyPlus. Used for executing IDFVersionUpdater"""
    myma=int(myma)
    mymi=int(mymi)
    if mymi==0 :
        prev_ma=myma-1
        prev_mi=9
    else:
        prev_ma=myma
        prev_mi=mymi-1
    return prev_ma, prev_mi

def add_comments_file(to_file=to_file):
    """Modified version of `add_comments` which creates an IDF output for testing purposes. File output uses suffix `_addComm.idf` by default."""
    return __abstract_add_objs2file(add_comments, to_file=to_file, suffix='addComm')

#def add_comments(objs_all, args={'delete': False}):
def add_comments(objs_all, args={'delete': True}):
    """Add EnergyPlus-style comments ('!-') back to IDF post JSON manipulations (which removes them)"""

    # Cleanup tempfiles after translation?
    cleanup=args['delete']

    ep_dir=getenv('ENERGYPLUS_DIR')

    temp_dir=mkdtemp("_addcomment")

    # Return E+ version, eg. [9, 5, 0] for input 'EnergyPlus-9-5-0'
    _get_eplus_version = lambda x: [int(y) for y in x.split('-')[1:4]]
    # E+ version information [major, minor, micro] versioning
    ma,mi,mc = _get_eplus_version( ep_dir )

    # Check for IDFVersionUpdater in $ENERGYPLUS_DIR.
    updater_dir= join( ep_dir, "PreProcess", "IDFVersionUpdater")
    if not isdir( updater_dir ) :
        raise OSError("AddComments: Can't find EnergyPlus IDFVersionUpdater")

    data=objs_all
    _isfile = not isinstance(data, list)
    # Accepts files, lists, etc
    objs=get_IDF_objs_raw(data)
    vers=get_eplus_version(objs)
    #vers_ma, vers_mi = ma, mi # Use $ENERGYPLUS_DIR
    vers_ma, vers_mi = vers.split('.')
    vers_ma, vers_mi = int( vers_ma ), int( vers_mi )
    print("IDF Specified EP version: %s"%(vers))

    # Update version number
    obj_idxs = [i for i,obj in enumerate(objs) if get_obj_type(obj)=='Version']
    vers_idx=obj_idxs[0]
    prev_ma, prev_mi = get_prev_version( vers_ma, vers_mi )
    objs[vers_idx]="Version, %d.%d;"%(prev_ma, prev_mi)
    #print("Version, %d.%d;"%(prev_ma, prev_mi))

    ## Copying files to temp_dir
    trans_script=glob( join( updater_dir, "Transition*to-*%s-%s*"%(vers_ma,vers_mi) ))[0]
    script=basename(trans_script)
    copy(trans_script, temp_dir)
    _idd="V%s-%s-0-Energy+.idd"
    copy(join( updater_dir, _idd%(vers_ma,vers_mi)), temp_dir)

    # SB- NOTE slight of hand: copying new IDD as an older version (trick E+ into replacing comments)
    #copy(join( updater_dir, _idd%(prev_ma,prev_mi)), temp_dir)
    copy(join( updater_dir, _idd%(vers_ma,vers_mi)), join(temp_dir, _idd%(prev_ma,prev_mi)))
    idf=join(temp_dir, "temp.idf")
    fname=write_file(objs, idf)

    # Clean up
    def _cleanup():
        if cleanup : rmtree(temp_dir)

    # Run translation
    _cwd=getcwd()
    chdir(updater_dir)
    _out= run([script, idf], capture_output=True)
    chdir(_cwd)

    #Read file back in (sub Version)
    objs=get_IDF_objs_raw(idf)
    # Swap new version
    obj_idxs = [i for i,obj in enumerate(objs) if get_obj_type(obj)=='Version']
    vers_idx=obj_idxs[0]
    objs[vers_idx]="Version, %d.%d;"%(vers_ma, vers_mi)

    # If file provided, bkup old, overwrite with new
    if _isfile :
        fname=write_file(objs, idf)
        copy(data, data.replace('.idf', '_bkup.idf'))
        copy(idf, data)
        print("File translated!")
        _cleanup()
        return data
    # If data provided, return data
    else:
        _cleanup()
        print("Objects translated!")
        return objs

def add_sizingdesignday_file(to_file=to_file):
    """Modified version of `add_sizingdesignday` which creates an IDF output for testing purposes. File output uses suffix `_sizingDay.idf` by default."""

    return __abstract_add_objs2file(add_comments, to_file=to_file, suffix='sizingDay')

def add_sizingdesignday(objs_all, args={'location': "CAN_ON_Ottawa.716280_CWEC.epw"}):
#    """Removes and then adds back `SizingPeriod:DesignDay' object for the specified location. The provided EPW must be accompanied by a DDY file in the 'ENERGYPLUS_WEATHER' system variable directory."""

    # TODO- Fixing edge cases in DDY files
    # - remove all leading !- objects (fixing %s/°//g issue)
    # - remove all ';' from !- comments

    wfile_dir = environ['ENERGYPLUS_WEATHER']
    loc=args['location']

    # Filter existing 'SizingPeriod:DesignDay' (if any)
    new_objs= [obj for obj in objs_all if 'sizingperiod:designday' not in get_obj_type(obj).lower()]

    ddy=join(wfile_dir, loc.replace('epw', 'ddy') )
    if not isfile(ddy):
        raise FileNotFoundError(f"Design day weather file (DDY) now found for not found for 'location={loc}")

    objs_ddy=get_IDF_objs_raw(ddy)
    #print(objs_ddy)
    #for o in objs_ddy:
    #    print(get_obj_name(o))

    # Want:
    # - Winter: 'Htg 99.6% Condns'
    # - Summer: 'Clg .4% Condns'
    wint_objs= [obj for obj in objs_ddy if 'htg 99' in get_obj_name(obj).lower()]
    summ_objs= [obj for obj in objs_ddy if 'clg .4'   in get_obj_name(obj).lower()]
    #print("TEST LENGTHS: winter:%d summer:%d"%(len(wint_objs), len(summ_objs)))

    new_objs.insert(-1, wint_objs[0])
    new_objs.insert(-1, summ_objs[0])

    return new_objs

if __name__ == '__main__':

    # Using file from command line
    #copy_IDF_files(from_file=fr_file, to_file=to_file, myfn=copy_IDF_geo)

    ## Testing of copying CONSTRUCTIONS/MATERIALS and swapping contrustion names in surfaces
    #from_file='templates/prop_constructions_materials.idf'
    #copy_IDF_files(from_file=from_file, to_file=to_file, myfn=copy_IDF_constr)

    # Rename from ZoneLists
    #rename_from_zonelist_file(to_file=to_file)

    # Testing modification of insulation levels
    #mod_insul_file(to_file=to_file)

    #add_HVAC_DOAS_file(to_file=to_file)

    # Add/Remove unwanted thermostats using ZoneLists
    #set_themostat_from_zonelist_file(to_file=to_file)

    # Add Suite/Common Metering
    #add_suite_metering_file(to_file=to_file)

    ## Testing area caculations
    #objs_all  = get_IDF_objs_raw(file=to_file)
    #objs_surf = filter_IDF_objs_raw(objs_all, 'BuildingSurface:Detailed')
    ### FLOORS
    ##surf_flr  = _filter_surf_obj_by_type('Floor', objs_surf)
    ##flr_areas     = _calc_areas(surf_flr)
    ## EXTERIOR WALLS
    #surf_ext = filter_surf_by_extBC(objs_surf)
    #wall_areas = _calc_areas(surf_ext,'Wall')
    ###print([get_surf_type(obj) for obj in objs_surf])

    #print("\nTesting: template (Separate JSON file)")
    ##HVAC_payload='JSON/directives/add_IdealHVACTemplate.json'
    #HVAC_payload='JSON/directives/add_VRF_HVACTemplate.json'
    #ep_json=get_JSON_objs_raw('data_temp/RefBldgSmallOfficeNew2004_Chicago.epJSON')
    ##ep_json={}
    #print("Template TEST len BEFORE Expanded template: ", len(ep_json) )
    #d=dispatch_JSON(ep_json, args={'payload': HVAC_payload} )
    #print("Template TEST AFTER: Expanded template: ", d )
    #print("Template TEST len AFTER: Expanded template: ", len(d) )

    pass
