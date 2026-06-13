#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from numpy.random import uniform, normal, seed, randint
import json
import re

from os.path import isfile, isdir, join, getsize, basename, splitext, dirname

# weather/Resil data (which is later copied into tmpdir and overridden)
# weather
try:
    weather_fname='weather.json'
    with open(weather_fname) as f:
        weather=f.read()
    weather_json=json.loads( weather )
except:
    weather_json={}

iter_varkeys= [ k for k in weather_json.keys() if 'distribution' in weather_json[k].keys()]
print(iter_varkeys)
print("Sample Length: ", len(iter_varkeys) )

# RESILIENCY
try:
    resil_fname='resiliency_events.json'
    with open(resil_fname) as f:
        resil=f.read()
    resil_json=json.loads( resil )
except:
    resil_json={}

def single_sample():
    """Sample values using the distributions defined in `weather.json`."""
    # weather/Resil data (which is later copied into tmpdir and overridden)

    samples=[]

    def setOrNone(myv, nm):
        try: return weather_json[myv][nm]
        except: return None

    # SB- Processing.map was giving same RNG for all samples. Override
    seed( randint(1, 1e6) )
    for v in iter_varkeys:
        #val=10 # json[v]['value']
        val=weather_json[v]['value']
        distri=weather_json[v]['distribution']
        #perc_vary=weather_json[v]['percent_vary']
        #abs_vary=weather_json[v]['abs_vary']
        perc_vary=setOrNone(v, 'percent_vary')
        abs_vary=setOrNone(v, 'abs_vary')
        #points=
        if distri=="normal":
            #print("Scale: ",(1-perc_vary/100.)*val)
            #print("")
            #print("Scale: ",(perc_vary/100.)*val)
            #print("SCALE: (%vary,key,val)",[perc_vary,v,val])
            #points=normal(loc=val, scale=(1-perc_vary/100.)*val)
            if perc_vary:
                points=normal(loc=val, scale=(perc_vary/100.)*val)
            elif abs_vary:
                points=normal(loc=val, scale=abs_vary)
        elif distri=="uniform":
            if perc_vary:
                points=uniform(low=(1-perc_vary/100.)*val, high=(1+perc_vary/100.)*val)
            elif abs_vary:
                points=uniform(low=val-abs_vary, high=val+abs_vary)
        elif distri=="high-uniform":
            if perc_vary:
                points=uniform(low=val, high=(1+perc_vary/100.)*val)
            elif abs_vary:
                points=uniform(low=val, high=val+abs_vary)
        else:
            raise TypeError("Distribution not supported")
        samples.append(points)

    #print("Samples")
    #print(iter_varkeys)
    #print(samples)
    return samples

# Distributions:
#random.normal(loc=mu, scale=sigma, size=N) # mu=mean, scale=std
#random.uniform(low=0.0, high=1.0, size=None)

# How is this library executed? OPTIONS:
# * makefile
#   - run_cfMCA.py tmp-run-123456 --by-peak
#     + from genEPJ import cashflowMCA as cfmca
#     + run instead of cash_flow.py in makefile
#   - wrapper that calls cash_flow.py
#   - ADV- can run E+ separately. No issues in simlink of data_temp/Output
# * genEPJ file
#   - could be nice as you add cf fns as needed (but it would have LOTS of conditions-eg. HVAC)
#   - calls this library
#   - start MCA via generate(). Have an option for MCA_cost
#   - ISSUE- need to run E+ from genEPJ, not from makefile
# * genEPJ standalone script
#   - lives in 'gen' library
# * separate genCF file
# CHALLENGE: CPU core poor. CANT send max cores to opti. Need to leave some for cash_flow
# CHALLENGE: structure such that cash_flow can be run once or in MCA
# CHALLENGE: keeping write2db structure (extracting 100s of cashflow results. NOT one to sim_results)
# - Add a ± to each key parameter? Overwrite optiNPV.csv file
# - Let write2db extract and store ± as separate parameter?

# Start by calling cash_flow.py, not redesigning it

# STEPS:
# * MCA executed (on a per individual basis) [script called from makefile]
# * N samples are created (and batch processed)
# * FOREACH process:
#   - create tmp-cf directory
#   - copy required result files, cash_flow.py, weather.csv (JSON now), GHGS, ...
#     + fn: startcf_sim
#   - overwrite weather parameters with sample
#   - run prep_ref.idf, copy optiNPV.csv ref_cf.py
#   - run prep_opti.idf
#   - KEEP RESULTS directory OR write to DB table (separate from indiv)
# * extract results, average and make available for database. Delete all tmp-cf*
#   - grep RESULTS >> output.csv
#   - OR post-process masterscript that accumulates all sim_results
#   - add ± to each optiNPV.csv variable?

# Structure:
# python script in sim calls this library
# - specifies JSON input
# - specifies MCA samples
# - OPTIONALLY specifies functions. DEFAULT to cash_flow.py
#   + args: fn, condition, categorization
#   + SQL statements for peak selection. use guessdb fn
# Library
# - fn for output (*optiNPV.csv)
# - MCA support fns
#

from sys import path
from shutil import copyfile, move, rmtree, copy
from os.path import basename, join, dirname
from os import environ, system, getenv, chdir, getcwd, mkdir

from subprocess import call, Popen, PIPE, run

from glob import glob

from pathlib import Path

path.append('genEPJ')
path.append('../genEPJ')
# add_comments: overwrites provided file (saves previous to _bkup.idf)
# add_comments_file: creates a new file
from generate_EPJ import *
from opti_EPJ import generate_tmprun_dir

def tmpcf_dir():
    """Create a temporary directory name for a weather simulation run."""
    # cash_flow won't write optiNPV.csv locally if dir not set to 'tmp-run'
    mydir=generate_tmprun_dir(keep_dir=True, nm="tmp-runEPW-", num=10)
    return mydir

#def get_sql_database_name(myfile):
#    ext=Path(myfile).suffix
#    _bn=basename(myfile)
#    _sn=_bn.replace(ext,'.sql')
#
#    _path=join('data_temp','Output')
#    sql_file= join(_path,  _sn)
#    #print(sql_file)
#    #print( isfile(sql_file) )
#
#    _path2='Output'
#    sql_file2= join(_path2,  _sn)
#    #print(sql_file2)
#    #print( isfile(sql_file2) )
#
#    if isfile(sql_file2): return sql_file2
#    elif isfile(sql_file): return sql_file
#    else: raise NameError("No SQL File Found!")
#
#def get_CSVs(myidf):
#    csv=join( 'Output', myidf.replace('.idf', '.csv') )
#    csv_mtr=join( 'Output', myidf.replace('.idf', 'Meter.csv') )
#    return csv,csv_mtr

def run_resil():
    """Run the resilience workflow with the local `make` target."""
    _out= run(["make","clean"], capture_output=False)
    _out= run(["make"], capture_output=True)
    return _out
def cleanup():
    """Run `make clean` to remove simulation by-products."""
    _out= run(["make","clean"], capture_output=False)
    return _out

def run_epw_vary(epw, tmp, sun, wnd):
    """Apply weather perturbations to an EPW using `scripts/epw_vary.py`."""
    _nm=join('scripts','epw_vary.py')
    _out= run(["python3", _nm, "-i", "%s"%(epw), '--sun_abs', "%s"%(sun), '--wind_abs', "%s"%(wnd), '--temp_abs', "%s"%(tmp)], capture_output=True)
    return _out

def _myround(v, n): return int(round(v,0))

def startsim(tmpdir, idf):
    """Start a resilience simulation in a temporary working directory."""

    mkdir(tmpdir)
    #mkdir( join(tmpdir, 'Output'))
    #print(tmpdir)
    old_cwd=getcwd()

    prop=idf
    #ref_sql=get_sql_database_name(ref)
    #prop_sql=get_sql_database_name(prop)

    genEPJ_file=glob("*_genEPJ.py")[0]
    #  - use look ahead? '(?![_]*)' as per: find_base_IDF= lambda x: re.findall(r'(?![_]*)[\w\d]+.idf', x)
    from sys import exit
    def find_base_IDF(mystr):
        match= re.findall(r'^[a-zA-Z0-9]+.idf', mystr)
        if match: return match[0]
    idf_files=list( map( find_base_IDF, glob('*idf') ))
    try:
        idf_file=[f for f in idf_files if f][0]
    except:
        print("IDF File not found")
        exit(1)
    print("Found IDF File: %s"%(idf_file))
    #idf_file='EvePark.idf'

    # Copy files to tmpdir
    files=[genEPJ_file, idf_file, 'resiliency_events.json', 'weather.json', 'features.csv', 'opti_inputs.json', 'makefile', 'outage_risks.json']

    from os import environ
    eplus_wdir = environ['ENERGYPLUS_WEATHER']

    for f in files:
        copy(f, tmpdir)

    from shutil import copytree

    copytree('scripts', join(tmpdir, 'scripts'))
    copytree('diagnostics', join(tmpdir, 'diagnostics'))
    copytree('templates', join(tmpdir, 'templates'))
    copytree('genEPJ', join(tmpdir, 'genEPJ'))
    #copy(diag_script, join(tmpdir, 'diagnostics'))

    # Change into tmpdir and get to work!
    chdir(tmpdir)
    # Get weather files
    #weather_files=['London_2013Icestorm_2003NABlackout.epw', 'London_2013Icestorm_2003NABlackout.epw']
    weather_files= [ resil_json[k]['EPW'] for k in resil_json.keys() if 'EPW' in resil_json[k].keys()]
    if len(weather_files)> len(list(set(weather_files))):
        print("Identical EPWs not allowed in 'resiliency_events.json'")
        exit(1)

    # Extract risk values from CSV
    def extract_CSV_risk(myfile):
        with open(myfile, 'r') as f:
            lns=f.readlines()
            return float(lns[-1].split(',')[1].strip())

    _cwd=getcwd()
    iter_resilkeys= [ k for k in resil_json.keys() ]
#['resil_temp_vary'    , 'resil_solar_vary' , 'resil_wind_vary'  , 'resil_tstop_multi' , 'resil_Nfreq_multi']
#[-0.29390054312430697 , 308.85300083439654 , -4.391163655256182 , 0.9924614417666966  , 1.000810057328093]
    for indx,epw in enumerate(weather_files):
        # Copy EPW into directory
        abs_epw=join(eplus_wdir, epw)
        copy(abs_epw, _cwd)

        # Apply sampling to Event 1 AND 2 (sampled separately)
        samples=single_sample() # DONT sample per outage event. Want consistant assumptions (Would need to dual report for each outage event)
        temp_abs=samples[0]
        solr_abs=samples[1]
        wind_abs=samples[2]
        run_epw_vary(epw, tmp=temp_abs, sun=solr_abs, wnd=wind_abs)

        # Apply sampling to resiliency_events.json
        tstop_multi=samples[3]
        Nfreq_multi=samples[4]
        prev_Nfreq=resil_json[ iter_resilkeys[indx] ]['Nfreq']
        prev_tstop=resil_json[ iter_resilkeys[indx] ]['t_stop']
        prev_tstart=resil_json[ iter_resilkeys[indx] ]['t_start']
        print("Nfreq: [prev,new, multi]", [prev_Nfreq, prev_Nfreq*Nfreq_multi, Nfreq_multi])
        print("Tstop: [prev,new, multi]", [prev_tstop, prev_tstop*tstop_multi, tstop_multi])

        resil_json[ iter_resilkeys[indx] ]['Nfreq'] = _myround(prev_Nfreq * Nfreq_multi, 0)

        #new_tstop= int(prev_tstart)+20
        new_tstop= _myround(prev_tstop * tstop_multi, 0)
        # Override if t_outage<24hrs (not allowed by genEPJ)
        if ( (int(new_tstop)-int(prev_tstart))<24 ) : new_tstop= int(prev_tstart)+24

        resil_json[ iter_resilkeys[indx] ]['t_stop'] = new_tstop
        with open('resiliency_events.json', "w") as write_file:
            json.dump(resil_json, write_file, indent=4)

    print("CWD: %s"%(_cwd))
    res=run_resil()
    print(res)

    # Reporting (SB- can't do above as 'run_resil()' need to be executed first)
    # Ref OR Prop?
    bldg_type=None
    with open(glob('*_genEPJ.py')[0]) as f:
        lns=f.read()
        match=re.findall(r'[\s]+bldg_key=[\w\'"-]+', lns)[0]
        if 'ref' in match: bldg_type="ref"
        elif 'prop' in match: bldg_type="prop"
        else: bldg_type="ufo"
    # END Ref OR Prop?
    csv_risk=[]
    csv_lines=[]
    # CSV Header
    csv_lines.append( "resil_index, bldg_type, epw_temp, epw_solar, epw_wind, tstop_multi, nfreq_multi, risk" )
    for indx,epw in enumerate(weather_files):
        # SB- csv format
        # Get risk(s) from TXT/CSVs
        # ice/heat, ref/prop, epw samples, resil sample, risk_ice, risk_heat, risk_sum
        _risk=extract_CSV_risk( 'resultVoLL_resil%d.csv'%(indx+1))
        csv_risk.append(_risk)
        csv_lines.append( "%d,%s,%1f,%.1f,%.1f, %.4f,%.4f, %.2f"%(indx+1,bldg_type, temp_abs,solr_abs,wind_abs, tstop_multi,Nfreq_multi, _risk) )

    with open("resultRisk_MCA.csv",'w') as g:
        for ln in csv_lines: g.write(ln+"\n")

    print("CWD: %s"%(_cwd))

    # Reduce dir size from ~250MB to ~20MB
    cleanup()
    chdir(old_cwd)

    # 'for pa in "$WEA_P" "$ENERGYPLUS_WEATHER" "."; do'

#def run_cashflow(myidf, byPeak=True):
#
#    _idf= basename(myidf)
#    #print(_idf)
#
#    #python3 cash_flow.py -i *opti.idf --byPeak  # Mech Costs by Peak load
#    _out= run(["python3", "cash_flow.py", "-i", "%s"%(_idf), "--byPeak"], capture_output=True)
#    return _out

def _fit(_d):
    "Function outside scope of map_eval required to run pickling in multiprocessing.pool"
    return startsim(tmpdir=_d[0], idf= _d[1])

import multiprocessing
threads=3
#threads=4
def generate_MCA(N, bldgs):
    """Generate and run `N` Monte Carlo samples for the specified IDF."""
    pool=multiprocessing.Pool(threads)
    tmpdirs=[tmpcf_dir() for n in range(N)]
    data_pairs=[ [tmpdirs[n], bldgs] for n in range(N) ]
    #SB- same x4 directories created over and over...
    #data_pairs=[ [tempcf_dir(), bldgs] for n in range(N) ]
    output= pool.map( _fit, data_pairs )

# SB- Test code to ensure parallelism works
## || test of sampling. What are they identical!?
#def _fit2(_d):
#    "Function outside scope of map_eval required to run pickling in multiprocessing.pool"
#    return single_sample()
#def test_samples(N):
#    pool=multiprocessing.Pool(threads)
#    data_pairs=[ [] for n in range(N) ]
#    output= pool.map( _fit2, data_pairs )
#    print(output)
#
#def _fit3(_d):
#    "Function outside scope of map_eval required to run pickling in multiprocessing.pool"
#    return tmpcf_dir()
#def test_tmpdir(N):
#    pool=multiprocessing.Pool(threads)
#    data_pairs=[ [] for n in range(N) ]
#    output= pool.map( _fit3, data_pairs )
#    print(output)
#
#    #for n in range(N):
#    #    d=tmpcf_dir()
#    #    print(d)
#    #    startsim(d, bldgs)

if __name__ == '__main__':

    #ref_bldg='tinyv2_01v9_prep_ref.idf'
    #prop_bldg='tinyv2_01v9_prep_opti.idf'
    #d=tmpcf_dir()
    #startsim(d, [ref_bldg,prop_bldg])

    #indivs=sample_weather(2)
    #print("Keys")
    #print(iter_varkeys)
    #print("Indiv")
    #print(indivs)

    #ref_bldg='EvePark_prep_ref.idf'
    prop_bldg='EvePark_prep_opti.idf'
    generate_MCA(110, prop_bldg)
    #generate_MCA(100, prop_bldg)
    #generate_MCA(10, prop_bldg)
    #generate_MCA(100, prop_bldg)
    #generate_MCA(5, prop_bldg)

    #test_samples(2)
    #test_tmpdir(10)