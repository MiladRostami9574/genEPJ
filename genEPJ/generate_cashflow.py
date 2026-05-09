"""Monte Carlo support utilities for cash-flow sensitivity studies.

This module samples parameters defined in local ``costing.json`` and
``resiliency_events.json`` files, prepares temporary run directories,
and executes cash-flow analyses using pre-existing EnergyPlus results.

The workflow shown here is an example analysis pathway and is not
intended to be universally applicable to all building studies.
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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

    for v in iter_varkeys:
        #val=10 # json[v]['value']
        val=costing_json[v]['value']
        distri=costing_json[v]['distribution']
        perc_vary=costing_json[v]['percent_vary']
        #points=
        if distri=="normal":
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

#

from sys import path
from shutil import copyfile, move, rmtree, copy
from os.path import basename, join, dirname
from os import chdir, environ, getcwd, getenv, mkdir, system

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
    """Start an LCC simulation using pre-existing EnergyPlus results."""

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
    _out= run(["python3", diag_script, "resultVoLL_resil1.csv"], capture_output=True)

    # Run cashflow: create proposed results
    prop_out=run_cashflow(prop)
    prop_res=glob("*optiNPV.csv")

    chdir(_cwd)

def run_cashflow(myidf, byPeak=True):
    """Run LCC using pre-existing EnergyPlus results."""

    _idf= basename(myidf)
    #print(_idf)

    #python3 cash_flow.py -i *opti.idf --byPeak  # Mech Costs by Peak load
    _out= run(["python3", "cash_flow.py", "-i", "%s"%(_idf), "--byPeak"], capture_output=True)
    return _out


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

    ref_bldg='tinyv2_01v9_prep_ref.idf'
    prop_bldg='tinyv2_01v9_prep_opti.idf'
    #generate_MCA(500, [ref_bldg,prop_bldg])
    generate_MCA(300, [ref_bldg,prop_bldg])
    #generate_MCA(100, [ref_bldg,prop_bldg])
    #generate_MCA(10, [ref_bldg,prop_bldg])
    #generate_MCA(1, [ref_bldg,prop_bldg])
