#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilities for connecting genEPJ workflows to optimization studies.

This module provides helper functions for preparing optimization inputs,
running simulations, storing results, and translating between genEPJ
representations and optimization-library solution objects. It is primarily
used to connect genEPJ-based workflows with Platypus.
"""

import json

import pandas as pd
import numpy as np

from copy import deepcopy

#from matplotlib import pyplot as plt

from os.path import isfile, isdir, join, getsize, basename, splitext, dirname
from os import environ, mkdir, unlink

# Libs for running simulations
from string import ascii_letters, punctuation, digits
from random import choice, seed, randint
from shutil import copyfile, move, rmtree
#from subprocess import call, Popen, PIPE
from subprocess import Popen, PIPE

#: default number of CPUs to use
num_cpus = 2

from time import time, sleep
import sqlite3

sql_file = join('db', 'data.db3')

def sqlite_insert_indiv(data, i=0):
    """Insert an individual into the optimization SQLite database.

    Only minimal information is stored here: the simplified individual
    representation, the full key-variable representation, and the time
    required to conduct the fitness evaluation. The function retries when
    the database is temporarily locked.
    """
    data= list( map(str, data) )
    sql_cmd=''' INSERT into indiv (indiv, keyvar, simtime) VALUES(?,?,?) '''
    if i<5:
        try:
            conn = sqlite3.connect(sql_file)
            c = conn.cursor()
            c.execute(sql_cmd, data)
            conn.commit()
            conn.close()
            return c.lastrowid
        except: # sqlite3.OperationalError: database is locked, try again
            # May not be needed
            sleep( randint(2,10)  ) # wait random time from 2->10 seconds
            sqlite_insert_indiv(data,i+1)
    else: return False

def sqlite_delete_indiv(data, i=0, pkey=None):
    """Delete an individual from the optimization SQLite database.

    The function retries when the database is temporarily locked.
    """
    if isinstance(data, list):
        #print("DELETE: List provided")
        _indiv=data
    else:
        #print("DELETE: Solution provided")
        _indiv=data
        dict_indiv=solution2dict( data )
        _indiv=list( dict_indiv.values() )
    #print("Indiv, pkey:",(_indiv,pkey))

    if pkey:
        #sql_cmd=''' DELETE from indiv WHERE pkey=?'''
        sql_cmd=''' DELETE from indiv WHERE pkey=%d'''%(pkey)
        _indiv=pkey
    else:
        #sql_cmd=''' DELETE from indiv WHERE indiv="?"'''
        sql_cmd=''' DELETE from indiv WHERE indiv="%s"'''%(data)
    #print(sql_cmd)

    if i<5:
        try:
            #print("DELETE in try")
            conn = sqlite3.connect(sql_file)
            c = conn.cursor()
            conn.set_trace_callback(print)
            #c.execute(sql_cmd, str(_indiv))
            c.execute(sql_cmd)
            conn.commit()
            conn.close()
            return True
        except Exception as e: # sqlite3.OperationalError: database is locked, try again
            #print("DELETE in except:", e)
            # May not be needed
            sleep( randint(2,10)  ) # wait random time from 2->10 seconds
            sqlite_delete_indiv(data,pkey=pkey, i=i+1)

    else: return False

def call(command):
    """Execute a shell command used in a simulation workflow."""
    command = command.split(' ')
    #return Popen(command, stdout=PIPE).communicate()[0].replace('\n','')
    return str( Popen(command, stdout=PIPE).communicate()[0]).replace('\n','')

def generate_tmprun_dir(keep_dir=True, nm="tmp-run-", num=10):
    """Create the temporary directory required for a unique simulation.

    Parameters:

    * `keep_dir`: flag to keep directory of simulation
    * `num`: number of random alpha-numerial characters to append to file directory `tmp-run-`. Default of 10 digits.

    Returns:

    * `String`: generated file directory name to later create and conduct simulation in
    """
    # override RNG (Processing.Pool() lacked resetting RNG for some reason in genEPJ/generate_weather.py)
    #seed( randint(1, 1e6) )

    string_format = ascii_letters + digits
    _generated_string = nm + "".join(choice(string_format) for x in range(num))
    #print("Your String is: {0}".format(generated_string))
    return _generated_string

def get_input_file(json_file=None):
    """Return the JSON file used to define optimization parameters."""
    if json_file: params_file = json_file
    else: params_file = 'opti_inputs.json'

    f=open( join('sim', params_file), "r")
    json_params = json.loads( f.read() )
    f.close()
    return json_params

def write_simvars_json(run_dir, x):
    """Write optimization-variable values to the simulation JSON input."""

    params_file = 'opti_inputs.json'

    json_params=get_input_file()
    templ_fname= join('sim', params_file)
    json_file=join(run_dir, params_file)
    copyfile(templ_fname, json_file)

    for i,key in enumerate(json_params.keys()):
        json_params[key]['value']=x[i]

    #print("Wrote keys",json_params)

    with open(json_file, "w") as write_file:
        json.dump(json_params, write_file, indent=4)

def get_fit_abstract(indiv, dbkey):
    """Return a pre-calculated fitness value from the SQLite database."""
    sql_fit="SELECT %s FROM indiv WHERE indiv = '%s' LIMIT 1"
    conn = sqlite3.connect(sql_file)
    c = conn.cursor()
    #query=c.execute(sql_fit, (dbkey, indiv))
    #c.execute(sql_fit, (dbkey, indiv))
    c.execute( sql_fit%(dbkey,indiv) )
    #print(sql_fit%(dbkey,indiv))
    query=c.fetchone()
    conn.close()
    return query[0]

from platypus import RandomGenerator
from platypus.types import bin2int, int2bin, bin2gray, gray2bin

# Pass a solution object and return a sorted dict

def decode_solution(solution):
    """Decode a binary representation of the solution to a human readable format"""
    prob=solution.problem
    solution.variables[:] = [prob.types[i].decode(solution.variables[i]) for i in range(prob.nvars)]
    return solution

def encode_solution(solution):
    """Encode a human readable format to binary representation of the solution"""
    prob=solution.problem
    solution.variables[:] = [prob.types[i].encode(solution.variables[i]) for i in range(prob.nvars)]
    return solution

def solution2dict(solution):
    """Convert a Platypus `Solution` object to a Python dictionary"""
    mysoln=deepcopy(solution)
    json_params=get_input_file()
    keys=json_params.keys()
    _plat_var=mysoln.variables

    vals=json_params.values()

    _d={}
    #print(keys, vals)
    for i,k in enumerate(keys):
        if isinstance(_plat_var[i], list):
            _idx=bin2int(gray2bin( _plat_var[i]  ))
            _start=json_params[k]['start']
            _stop=json_params[k]['stop']
            _v=range(_start,_stop+1)
            #print("TEST: idx, _v: ",_idx,list(_v) )
            _d[str(k)]=_v[_idx]
        else: _d[str(k)]=_plat_var[i]
    return _d

def dict2solution(mydict, solution):
    """Convert a Python dictionary to a Platypus `Solution` object"""
    mysoln=deepcopy(solution)
    prob=mysoln.problem
    _plat_var=mysoln.variables
    i=0
    for k,v in mydict.items():
        mysoln.variables[i]=v
        i+=1
    return encode_solution(mysoln)

def n_rand_indiv(problem, N):
    "Return `N` random building/community configurations. Allows for interative testing before running optimization studies"
    return [rand_indiv(problem) for i in range(N)]

def rand_indiv(problem):
    "Return a random building/community configuration."
    #try:
    gen=RandomGenerator()
    _plat_solution=gen.generate(problem)
    _repre = _plat_solution.variables

    #print(solution2dict(_plat_solution) )

    return(_plat_solution)

def fit_eval(indiv, delete=True, sql_keys=['eui']):
    "Conduct a fitness evaluation of a building/community configuration and keep results for diagnostics"
    #return indiv.evaluate()
    dict_indiv=solution2dict( indiv )
    _indiv=list( dict_indiv.values() )
    res=objective_function( _indiv, fits=sql_keys, delete=delete)

    # Update data in the Platypus individual. Set evaluated flag=True
    indiv.evaluate()

    #return res.pop()
    return res

def _fit(_d):
    "Function outside scope of map_eval required to run pickling in multiprocessing.pool"
    return fit_eval(indiv=_d[0], delete= _d[1], sql_keys=_d[2])

import multiprocessing
#from functools import partial
def map_eval(population, delete=True, sql_keys=['eui']):
    """Evaluate a population of configurations in parallel."""
    pool=multiprocessing.Pool()
    data_pairs=[ [p, delete, sql_keys] for p in population ]
    #print(data_pairs)
    # Processing.pool needs to pickle objects into function (hence the nested list)
    output= pool.map( _fit, data_pairs )
    # Don't use this version as 'delete' flag can't be passed
    #output= pool.map( fit_eval, population )
    return output

def objective_function(x, fits=['eui'], i=0, delete=True):
    """Instantiate, simulate, and query fitness values for an individual."""

    try:
        objs=[ get_fit_abstract(x, key) for key in fits ]
        return list(objs)
    except:
        pass

    # start timer
    start_t=time()

    rand_dir=generate_tmprun_dir()
    temp_dir= join('sim', rand_dir)
    mkdir(temp_dir)

    # drop indiv in directory. Need for SQL entries in makefile
    indiv_fname= join(temp_dir, 'indiv.txt')
    with open(indiv_fname, "w") as f:
        f.write( str(x) +'\n' ) # don't need to f.close(). With handles that

    # Write sim_variables form template and get filename
    #simvar_fname=write_simvars(temp_dir, x)
    write_simvars_json(temp_dir, x)

    startsim_cmd= join('sim', 'startsim.sh') + " " + temp_dir
    call(startsim_cmd)

    # get err name: (apply str (filter #(.endsWith (.getName %) "_opti.err") (file-seq (io/file mydir)))))
    #  (get-errname (str sim-dir "/Output")
    # get res name: (apply str (filter #(.endsWith (.getName %) "_optiNPV.csv") (file-seq (io/file mydir)))))

    # ITERATE: write data to SQLITE 5 times
    #    DATA: '( :indiv :keyvar  :simtime)

    # If results don't exist, recall the entire simulation process

    # STORE metered files to DB (if they exist). Community optimization ONLY
    #   (sh "./code/csvMeter2dbBlob.csv" (str db-indiv) (format "%s/meters_total.csv" sim-dir)))]
    # IF (if (file-exists? (format "%s/meters_total.csv" sim-dir))

    # end timer
    stop_t=time()
    simtime=(stop_t-start_t)/60.
    #print('E+ call took %0.1f min' %(simtime) )

    # write optimizer only variables to database
    #print("Writing to DB")
    pkey=sqlite_insert_indiv( (x, x, simtime) )
    #print("PKEY: ",pkey)

    # sim_results.txt: created by write2db.sh. Need indiv written to DB first
    writedb_cmd= join('sim', 'scripts', 'write2db.sh') + " " + temp_dir
    call(writedb_cmd)
    #print(writedb_cmd)

    objs=[ get_fit_abstract(x, key) for key in fits ]
    #print( "SQL OBJS:", str(objs) )
    #print( objs )

    # Check that stored value for 'eui' is a number
    try:
        #_res= get_fit_abstract(x, 'eui')
        #int( float(_res) )

        # Check that objective fns are numerical and not type None
        [int( float(_r) ) for _r in objs]
    except:
        # Have we exceeded the number of objective_function calls?
        if i>5 :
            # Debug why the indiv won't compute
            raise Error("Simulation of indiv failed after 5 trys: %s (%s)"%(x, temp_dir))

        # Call E+ again, fit did not calculate properly
        rmtree(temp_dir)
        sqlite_delete_indiv(x, pkey=pkey)
        return objective_function(x, fits, i=i+1 )


    if delete:
        #print("IF DELETE flag: ",delete)
        rmtree(temp_dir)
    else:
        print(temp_dir)

    print("Indiv: ", (x, temp_dir))
    return list(objs)


def build_parameters(json_data):
    """Build Platypus parameter objects from the optimization JSON input."""

    from platypus import Real, Integer

    if isinstance(json_data, dict): # JSON dict
        json_params=json_data
    else:
        raise TypeError("Need to supply JSON dictionary")

    def _set_parameter_type(inp):
        if    'real' in inp.lower():
            return Real
        elif 'integer' in inp.lower():
            return Integer
        else: raise TypeError("Type not supported")
    params=[]
    # For
    for key in json_params.keys():
        _start=json_params[key]['start']
        _stop=json_params[key]['stop']
        _set_type=json_params[key]['type']
        _param_type=_set_parameter_type( _set_type )
        params.append( _param_type( _start, _stop ) )
    return params

def _get_bldg_dict(json_params, json_key):
    bldg_dict={}
    for i,key in enumerate(json_params.keys()):
        bldg_dict[key]=json_params[key][json_key]

    return bldg_dict

def get_ref_bldg(problem, json_params):
    """Return a reference building configuration using a `Platypus` solution object"""

    # Update parameters using JSON dict
    rand_soln=rand_indiv(problem)

    # Get dict for 'ref-values'
    ref_dict=_get_bldg_dict(json_params, 'ref-value')
    return dict2solution(ref_dict, rand_soln)

def get_prop_bldg(problem, json_params):
    """Return a proposed building configuration using a `Platypus` solution object"""

    # Update parameters using JSON dict
    rand_soln=rand_indiv(problem)

    # Get dict for 'prop-values'
    prop_dict=_get_bldg_dict(json_params, 'prop-value')
    return dict2solution(prop_dict, rand_soln)

def search_pathway_sequential(ref_solution, prop_solution, sql_key='eui'):
    """Return a sequential gradient pathway from reference to proposed."""
    ref_dict=solution2dict(ref_solution)
    prop_dict=solution2dict(prop_solution)

    new_ref=deepcopy(ref_dict)
    delta_keys=[]
    delta_fits=[]

    for k,v in prop_dict.items():
        if ref_dict[k]!=v :
            delta_keys.append(k)

    res=[]
    ref=deepcopy(ref_solution)
    prop=deepcopy(prop_solution)
    for k in delta_keys:

        _res=search_pathway_OAT( ref, prop, sql_key=sql_key)
        try:
            _key,_dfit=_res[0] # Sorted by highest
            res.append( (_key, _dfit) )
        except:
            _key,_dfit=None,None # issue only with 3RV KPIs
        #print("INCREMENTAL RES (%s)- %s"%(sql_key, res))

        #update ref with prop value (key now ignored by search_pathway_OAT)
        #  EDGECASE: if 3RV (resil/lofmax/etc), move batt and PV at same time
        if _key: # Skip key if None
            if "+" in _key:
                splt_keys=_key.split('+')
                for _myk in splt_keys:
                    indx=[i for i,k in enumerate(prop_dict.keys()) if k==_myk][0]
                    ref.variables[indx]=prop.variables[indx]
            else:
                indx=[i for i,k in enumerate(prop_dict.keys()) if k==_key][0]
                ref.variables[indx]=prop.variables[indx]

    return res

# One at a time/aka superposition
def search_pathway_OAT(ref_solution, prop_solution, sql_key='eui'):
    """Return a one-at-a-time gradient pathway for waterfall analyses."""

    ref_dict=solution2dict(ref_solution)
    prop_dict=solution2dict(prop_solution)

    ref_fit=fit_eval( ref_solution, sql_keys=[sql_key] )
    #prev_fit=ref_fit[0]

    new_ref=deepcopy(ref_dict)
    incremental_ref=[]
    delta_keys=[]
    for k,v in prop_dict.items():
        if ref_dict[k]!=v :
            #print("Key: %s, ref v: %s, prop v: %s"%(k, new_ref[k], v))
            new_ref[k]=v

            # EDGECASE: if 3RV (resil/lofmax/etc), move batt and PV at same time
            new_k=str(k)
            threeRV=['lofmax', 'vulner', 'resil', 'relia', 'robust', 't_decay', 't_recov', 't_outage', 'VoLL_cost', 'VoLL_kWh']
            for _i in range(1,20): # Code can handle up to 20 outage events
                iter_threeRV=[ v+"%d"%(_i) for v in threeRV ]
                threeRV.extend(iter_threeRV)
            # Add blended KPIs
            iter_threeRV=[ v+"_%s"%("blend") for v in threeRV ]
            threeRV.extend(iter_threeRV)

            def _is_in2(myarray, val):
                "Return `True` if part/whole of `val` is found in any value recorded in `myarray`. Else, return `False`."
                for myval in myarray:
                    if val in myval: return True
                return False

            if ( _is_in2(threeRV, sql_key) and ( ('pv' in k) or ('batt' in k))) :
                # Add batt/pv (if a change has been made to either)
                pv_key=  [ _myk for _myk in prop_dict.keys() if 'pv' in _myk ][0]
                batt_key=[ _myk for _myk in prop_dict.keys() if 'batt' in _myk ][0]
                new_ref[pv_key]=prop_dict[pv_key]
                new_ref[batt_key]=prop_dict[batt_key]
                new_k=pv_key + '+' + batt_key

            incremental_ref.append( dict2solution(new_ref, ref_solution) )
            delta_keys.append(new_k)
            # Reset to find next OAT change
            new_ref=deepcopy(ref_dict)
    #print("incremental ref")
    #print("\n".join( list(map(lambda x: str( x.variables ),incremental_ref)) ))

    # Start simulation
    fits=map_eval( incremental_ref, sql_keys=[sql_key])
    #print("FITS Test (%s):"%(sql_key),fits)
    iter_incremental_ref=deepcopy(incremental_ref)
    for i,_soln in enumerate(iter_incremental_ref):
        try:
            if not fits[i][0]:
                incremental_ref.pop(i)
                fits.pop(i)
        except: pass

    def filter_zero_diff(mykeys,mydeltas):
        # Filter zeros if only some values are zeros (keep the same if all zeros)
        is_zero=[ _val==0 for _val in mydeltas ]
        if all(is_zero):
            _k,_v=mykeys,mydeltas
        else:
            keep_keyvals=[ [mykeys[myi],myv] for myi,myv in enumerate(mydeltas) if myv!=0 ]
            _k=[ myk for myk,myv in keep_keyvals ]
            _v=[ myv for myk,myv in keep_keyvals ]
        return _k,_v

    ## Before: Works for EUI/LoFmax NOT Payback
    #if ref_fit[0]==0: # payback, lof_max, etc
    #    delta_fits=[ float(float(f[0]-ref_fit[0])) for f in fits if f[0]] # ie. f!=None
    #else:
    #    delta_fits=[ float(ref_fit[0])-float(f[0]) for f in fits if f[0]] # ie. f!=None

    delta_fits=[ float(ref_fit[0])-float(f[0]) for f in fits if f[0]] # ie. f!=None

    new_delta_keys,new_delta_fits=filter_zero_diff(delta_keys, delta_fits)
    if len(new_delta_keys)==0 :
        return list(zip(delta_keys, delta_fits))

    #print("TEST deltas vs point of reference: refpt: %.1f, deltas: %s, fits: %s"%(float(ref_fit[0]), str(delta_fits), str(fits)))
    res=list(zip(new_delta_keys, new_delta_fits))
    res.sort(key=lambda y: y[1])
    res.reverse()
    if sql_key=='payback':
        raw_fits=[ -float(f[0]) for f in fits if f[0]]
        new_dkeys,new_fits=filter_zero_diff(delta_keys, raw_fits)
        if len(new_dkeys)==0 :
            return list(zip(delta_keys, raw_fits))
        res=list(zip(new_dkeys, new_fits))
        res.sort(key=lambda y: y[1])
        res.reverse()
        print("PAYBACK DEBUG: ", res)
    return res
