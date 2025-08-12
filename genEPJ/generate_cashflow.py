"""
**Feature shown as an example analysis. NOT universally applicable to any building study.**

Conduct a Monte Carlo simulation (sampling of costing related parameters with distributions defined in local `costing.json` and `resiliency_events.json` files)

Example simple `costing.json` file:
```
{
    "use_fin": {
        "value": 0,
        "percent_vary": 20,
        "distribution": "normal",
        "description": "Use financing in life-cycle analysis",
        "units": "bool"
    },
    "fin_rate": {
        "value": 2.5,
        "percent_vary": 20,
        "distribution": "normal",
        "description": "Financing rate",
        "units": "\\%"
    },
    "lev_ratio": {
        "value": 0.4,
        "percent_vary": 20,
        "distribution": "normal",
        "description": "Leveraging ratio (fraction down)",
        "units": "--"
    },
    "prime": {
        "value": 3.0,
        "percent_vary": 20,
        "distribution": "normal",
        "description": "Prime rate",
        "units": "\\%"
    },
    "t_lcc": {
        "value": 25,
        "percent_vary": 20,
        "distribution": "normal",
        "description": "Life-Cycle period",
        "units": "yr"
    }
}
```

"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# How to use (from sim-BLDG folder)
#> python3 genEPJ/generate_cashflow.py && ./scripts/extract_results_MCAresil.sh && Rscript stats_tests.R results_costMCA_nosummary.csv

# TODO-
# Copy/Run for multiple RESILIENCY events (presently only one)

# Next steps:
# 1. JSON for costing.csv, add distributions. Add distributions to resiliency.json
# 2. Sample distributions for each variable with a distribution assigned to it
# 3. zip samples into indiv
# 4. batch process
#    - update value in JSON file: Done in tmp-runCF (for cash_flow). Done LOCALLY
# 5. post-process results (+-)
# 6. clean-up

# START WITH COSTING, then move to RESILIENCY

from numpy.random import uniform, normal
import json
from sys import exit
#from glob import glob

# Costing/Resil data (which is later copied into tmpdir and overridden)
# COSTING
try:
    cost_fname='costing.json'
    with open(cost_fname) as f:
        costing=f.read()
    costing_json=json.loads( costing )
except:
    costing_json={}
iter_varkeys= [ k for k in costing_json.keys() if 'distribution' in costing_json[k].keys()]
print(iter_varkeys)
print("Length: ", len(iter_varkeys) )

try:
    # RESILIENCY
    resil_fname='resiliency_events.json'
    with open(resil_fname) as f:
        resil=f.read()
    resil_json=json.loads( resil )
except:
    resil_json={}

def single_sample_costing():
    "Sample values using distributions specified in costing.json. Return a list of sampled values."
    # Costing/Resil data (which is later copied into tmpdir and overridden)

    samples=[]
    # TODO- add variable ONLY if distribution is assigned to it. Default perc_vary?

    for v in iter_varkeys:
        #val=10 # json[v]['value']
        val=costing_json[v]['value']
        distri=costing_json[v]['distribution']
        perc_vary=costing_json[v]['percent_vary']
        #points=
        if distri=="normal":
            # TODO SB- confirm this is how you want to handle std
            #print("Scale: ",(1-perc_vary/100.)*val)
            #print("")
            #print("Scale: ",(perc_vary/100.)*val)
            #print("SCALE: (%vary,key,val)",[perc_vary,v,val])
            #points=normal(loc=val, scale=(1-perc_vary/100.)*val)
            points=normal(loc=val, scale=(perc_vary/100.)*val)
        elif distri=="uniform":
            points=uniform(low=(1-perc_vary/100.)*val, high=(1+perc_vary/100.)*val)
        elif distri=="high-uniform":
            points=uniform(low=val, high=(1+perc_vary/100.)*val)
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

# TODO- convert costing.csv to JSON. Rewrite access in cash_flow.py

# STEPS:
# * MCA executed (on a per individual basis) [script called from makefile]
# * N samples are created (and batch processed)
# * FOREACH process:
#   - create tmp-cf directory
#   - copy required result files, cash_flow.py, costing.csv (JSON now), GHGS, ...
#     + fn: startcf_sim
#   - overwrite costing parameters with sample
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
from os import environ, system, getcwd, getenv, chdir, getcwd, mkdir

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
    """Create a temporary directory for simulation results with format `tmp-runCF-??????????` where `?` is in the set [ascii_letters + digits]."""
    # cash_flow won't write optiNPV.csv locally if dir not set to 'tmp-run'
    mydir=generate_tmprun_dir(keep_dir=True, nm="tmp-runCF", num=10)
    return mydir

def _get_sql_database_name(myfile):
    ext=Path(myfile).suffix
    _bn=basename(myfile)
    _sn=_bn.replace(ext,'.sql')

    _path=join('data_temp','Output')
    sql_file= join(_path,  _sn)
    #print(sql_file)
    #print( isfile(sql_file) )

    _path2='Output'
    sql_file2= join(_path2,  _sn)
    #print(sql_file2)
    #print( isfile(sql_file2) )

    if isfile(sql_file2): return sql_file2
    elif isfile(sql_file): return sql_file
    else: raise NameError("No SQL File Found!")

def _get_CSVs(myidf):
    csv=join( 'Output', myidf.replace('.idf', '.csv') )
    csv_mtr=join( 'Output', myidf.replace('.idf', 'Meter.csv') )
    return csv,csv_mtr

def startsim(tmpdir, idfs=[]):
    """Start a LCC simulation using pre-existing EnergyPlus results (copying over essential files and results into temporary directory)"""

    mkdir(tmpdir)
    mkdir( join(tmpdir, 'Output'))
    mkdir( join(tmpdir, 'templates'))
    mkdir( join(tmpdir, 'diagnostics'))
    print(tmpdir)

    ref,prop=idfs
    ref_sql=_get_sql_database_name(ref)
    prop_sql=_get_sql_database_name(prop)


    # Copy files to tmpdir
    files=['costing.csv', 'cash_flow.py', 'ref_cf.py', 'features.csv']
    files.extend(idfs) # ref/prop files
    for f in files:
        copy(f, tmpdir)
    # SQL/CSV
    output_files=[ref_sql, prop_sql]
    output_files.extend( _get_CSVs(ref) )
    output_files.extend( _get_CSVs(prop) )
    for f in output_files:
        copy(f, join(tmpdir, 'Output'))
    copy( join('templates', 'GHG_Max_hourly_emissions_8760SB.csv'),\
          join(tmpdir, 'templates'))
    # Resil results (rerun VoLL calcs)
    diag_script=join('diagnostics', 'diagnostic_VoLL.py')
    resil_files=['02_diff_outage.csv', 'raw_resil.csv', 'resiliency_events.json']
    for f in resil_files:
        copy(f, tmpdir)
    copy(diag_script, join(tmpdir, 'diagnostics'))

    _cwd=getcwd()
    chdir(tmpdir)

    # SB- Needs to be here or you just keep overwritting values during each sample
    # RESILIENCY
    resil_fname='resiliency_events.json'
    with open(resil_fname) as f:
        resil=f.read()
    resil_json=json.loads( resil )

    def myround(v, n): return int(round(v,0))
    # Write costing.json variations
    sample=single_sample_costing() # array of values by default
    for i,k in enumerate(iter_varkeys):
        if ( 't_' in k ) or ( 'repl' in k):
            costing_json[k]['value']= myround(sample[i], 0)
        else:
            #costing_json[k]['value']= sample[i]
            costing_json[k]['value']= round(sample[i], 3)
    with open('costing.json', "w") as write_file:
        json.dump(costing_json, write_file, indent=4)

    # Convert json back to CSV (for cash_flow.py- to keep it backwards compatible)
    json2csv_script=join('..', 'scripts', 'json2csv.py')
    _out= run(["python3", json2csv_script], capture_output=True)

    # Update resiliency_events.json
    VoLL_multi= costing_json['resil_VoLL_multi']['value']
    Nfreq_multi=costing_json['resil_Nfreq_multi']['value']
    tstop_multi=costing_json['resil_tstop_multi']['value']
    prev_Nfreq=resil_json['ice-storm']['Nfreq']
    prev_VoLL=resil_json['ice-storm']['VoLL_Ccold_exp']
    prev_tstop=resil_json['ice-storm']['t_stop']
    #print("Nfreq: [prev,new, multi]", [prev_Nfreq, prev_Nfreq*Nfreq_multi, Nfreq_multi])
    #print("Expon: [prev,new, multi]", [prev_VoLL, prev_VoLL*VoLL_multi, VoLL_multi])
    resil_json['ice-storm']['Nfreq'] = myround(prev_Nfreq * Nfreq_multi, 0)
    resil_json['ice-storm']['VoLL_Ccold_exp'] = prev_VoLL * VoLL_multi
    resil_json['ice-storm']['t_stop'] = myround(prev_tstop * tstop_multi, 0)
    with open('resiliency_events.json', "w") as write_file:
        json.dump(resil_json, write_file, indent=4)

    copy( 'raw_resil.csv', 'raw_resil_prop.csv')
    copy( '02_diff_outage.csv', '02_diff_outage_prop.csv')

    # Run cashflow: create reference results
    # run several times to ensure convergence
    #for _i in range(3):
    for _i in range(2):
        # Need to copy prev resilency_events to get correct VoLL_cost
        # TODO- find a way not to hard-code this. How to create during an opti run? Create 'resiliency_events_ref.json' in prop-tmp-run?
        copy( join('..', 'raw_resil_ref.csv'), 'raw_resil.csv')
        copy( join('..', '02_diff_outage_ref.csv'), '02_diff_outage.csv')
        _out= run(["python3", diag_script, "resultVoLL_resil1.csv"], capture_output=True)
        copy('resiliency_events.json', 'resiliency_events_ref.json')
        ref_out=run_cashflow(ref)
        with open( "REFCF.txt", 'w' ) as f:
            f.write( str(ref_out) )
        ref_res=glob("*_refNPV.csv")[0]
        copy(ref_res, "ref_cf.py")
        ref_out=run_cashflow(ref)
    ref_res=glob("*_refNPV.csv")[0]
    with open( ref_res ) as f:
        ref_res=f.read()
    assert 'npv=0.00' in ref_res, "%s: NPV NOT zero for reference bldg"%(tmpdir)

    # Copy back prev 'prop' resiliency_events. Need VoLL_cost to represent 'prop' not 'ref'
    copy( 'raw_resil_prop.csv', 'raw_resil.csv')
    copy( '02_diff_outage_prop.csv', '02_diff_outage.csv')

    # Run VoLL calcs
    # TODO- do this for multiple events
    _out= run(["python3", diag_script, "resultVoLL_resil1.csv"], capture_output=True)

    # Run cashflow: create proposed results
    prop_out=run_cashflow(prop)
    prop_res=glob("*optiNPV.csv")

    chdir(_cwd)

def run_cashflow(myidf, byPeak=True):
    """Run LCC using pre-existing EnergyPlus results (CSV/SQL)"""

    _idf= basename(myidf)
    #print(_idf)

    #python3 cash_flow.py -i *opti.idf --byPeak  # Mech Costs by Peak load
    _out= run(["python3", "cash_flow.py", "-i", "%s"%(_idf), "--byPeak"], capture_output=True)
    return _out


# TODO- which MCA lib to use? Write your own?
def generate_MCA(N, bldgs):
    """"Generate and conduct `N` Monte Carlo samples on specified building `bldg`

    Parameters:

    * `N`: Number of samples
    * `bldgs`: IDF filename (String) to conduct simulation on.

    Returns:

    * None
    """
    for n in range(N):
        d=tmpcf_dir()
        startsim(d, bldgs)

if __name__ == '__main__':

    #ref_bldg='tinyv2_01v9_prep_ref.idf'
    #prop_bldg='tinyv2_01v9_prep_opti.idf'
    #d=tmpcf_dir()
    #startsim(d, [ref_bldg,prop_bldg])

    #indivs=sample_costing(2)
    #print("Keys")
    #print(iter_varkeys)
    #print("Indiv")
    #print(indivs)

    # TODO- get PROP BLDG from commandline?
    ref_bldg='tinyv2_01v9_prep_ref.idf'
    prop_bldg='tinyv2_01v9_prep_opti.idf'
    #generate_MCA(500, [ref_bldg,prop_bldg])
    generate_MCA(300, [ref_bldg,prop_bldg])
    #generate_MCA(100, [ref_bldg,prop_bldg])
    #generate_MCA(10, [ref_bldg,prop_bldg])
    #generate_MCA(1, [ref_bldg,prop_bldg])
