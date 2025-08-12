#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"Wrapper to use ModelKit ([link](https://bigladdersoftware.com/projects/modelkit)) inside of genEPJ."


# Next steps:
# * call fn from within genEPJ
# * move EPSchematic and ModelKit into 'genEPJ' folder and add 'from genEPJ import *'
# * write root template within modelkit_wrapper
# * write several common templates you'd like to use within modelkit_wrapper (VAV, VRF, ...). Pass template to dispatch_ModelKit directly
# * Test: Ideal HVAC
# * Test: VRF with geothermal
# * Test: HP with radiant slab and DOAS
# * Test: Solar hot water

from subprocess import call, run, check_call, Popen, PIPE, DEVNULL
from os.path import isfile, isdir, join, getsize, basename, splitext, dirname
from shutil import which
from tempfile import mkstemp
from os import system, getcwd, environ
from sys import platform, path # win/linux?
import re

from string import Template # Allows for substitutions using {}

# TODO- get from PATH using "modelkit --version"
modelkit_version="0.8.0"

log_modelkit_txt="LOGS_Modelkit.txt"
ff=open(log_modelkit_txt, 'w')

def write_log(line):
    "Write details (`line`) to ModelKit log file (`log_modelkit_txt`)."
    #ff.write(line+"\n")
    # TODO- add fancy formatting/colour
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
# TODO- update so this can be ported to windows
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

#### REPLACE with genEPJ_lib import {{{
##**********************************
#def open_IDF_file(file):
#    mydata = open(file, 'r').read()
#    return mydata
#
#def dos2unix(mystr):
#    return mystr.replace('\r','')
#
## SB: REGEX doesnt match first line without a '\n'. Ex 'Version,8.1;\n\n'
#myre = re.compile(r'[\n]*[\w\t\s\d\/.{}\(\)\[\]+,\'\n%=><#*:!@-]+;[ \t\w\d\/.{}\[\]\(\)%=><#+,:\?!@-]*')
#
#rm_leading_comments = re.compile(r'^!.*$')
#
#def get_IDF_objs_raw(data):
#    if isinstance(data, list):
#        print("Data is of type List: Joining and converting to DOS")
#        mydata=dos2unix("\n\n".join(data))
#    elif isfile(data):
#        print("Data is a File: Opening and processing to type String")
#        mydata=open_IDF_file(data)
#    elif isinstance(data, str):
#        # Nothing to do
#        print("Data is of type String: Nothing to do")
#        mydata=data
#    else:
#        raise ValueError("get_IDF_objs_raw: Unknown data type or non-existant file :"+data)
#
#    # Issues with some E+ ExampleFiles. Above regex can't parse these without significant workaround. Preferences is to KISS
#    mydata = mydata.replace(" & ", " AND ")
#
#    # SB NOTE: mydata must be type string at this point
#    objs = myre.findall(mydata)
#    # Strip leading \n on objs
#    objs=[obj.strip('\n') for obj in objs]
#    return objs
#
#def combine_objects(objs_all):
#    # dos2unix: get rid of pesky '\r' objects
#    return dos2unix("\n\n".join(objs_all))
#
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
#
#def trim_comments(myobj): #Trim comments from an eplus object
#    # Strip off comments on a given line (occurs before e+ objects)
#    re_nocom=re.compile("^[ ]*!.*?\n")
#    myobj=recursive_strip(myobj)
#    myobj=re.sub(re_nocom, '', myobj)
#    myobj=recursive_strip(myobj)
#    obj_lst = [ln.split('!-')[0].strip(' ') for ln in myobj.split('\n')]
#    return '\n'.join(obj_lst)
#
#def get_obj_abstract(myobj, idx):
#    # Hack. Best to use trim_comments() first
#    no_com = trim_comments(myobj)
#    if (('BuildingSurface:Detailed' in myobj) or ('FenestrationSurface:Detailed' in myobj)): # the object uses coordinates
#        sp_ln=no_com.replace(';','').split(',\n')
#        myln=no_com.replace(';','').split(',\n')[idx]
#        return myln
#    else:
#        return no_com.split(',')[idx].strip(' ').strip('\r').strip('\n')
#
##********************************** }}}

def _mycall(command):
    ### Old way: doesnt work with modelkit exe
    #command = command.split(' ')
    #return str( Popen(command, stdout=PIPE).communicate()[0]).replace('\n','')

    #return run( command, shell=True)
    #return call( command, shell=True)
    #return check_call( command, shell=True )

    ## redirect modelkit error "/home/sb/.gem/ruby/2.6.0/gems/modelkit-0.8.0/lib/modelkit/units.rb:145: warning: constant ::Fixnum is deprecated" to DEVNULL
    #return check_call( command, shell=True, stderr=DEVNULL )

    #
    #return system( command ) # Modelkit doesn't run properly through Popen

    ## HACK: Linux/mac is a butterfly
    # https://docs.python.org/2/library/sys.html#sys.platform (returns: win32, linux(2), cygwin, darwin, etc
    if platform.startswith('win'):
        command = command.split(' ')
        return str( Popen(command, stdout=PIPE).communicate()[0]).replace('\n','')
    else: # linux/mac
        from pty import spawn # psuedo-tty
        # modelkit/cli requires a TTY to read in options. Open one using pty.spawn()
        g=open('modelkit_cmd.sh', 'w')
        g.write("#!/usr/bin/env bash\n")
        g.write(command+" &> modelkit_output.txt\n")
        g.close()

        #output=spawn(command)
        check_call( "chmod +x modelkit_cmd.sh", shell=True )
        output=spawn( "modelkit_cmd.sh" )

        #check_call( "chmod +x modelkit_cmd.sh", shell=True )
        #output=check_call( "modelkit_cmd.sh", shell=True )
        return output
        #return system( "bash ./modelkit_cmd.sh") # Modelkit doesn't run properly through Popen

        ##
        #g=open('modelkit_cmd.sh', 'w')
        #g.write(command+" &> modelkit_output.txt")
        #return check_call( "bash ./modelkit_cmd.sh", shell=True, stderr=DEVNULL )

def _count_lines(myfile): return sum(1 for line in open(myfile))

def run_modelkit(root):
    "Run ModelKit on the provided root file. Write steps to a logfile. Return the created ModelKit output (`outputfile`)."
    # Given a dictionary (epJSON) or list (genIDF), swap to the alternative format and return a list or dictionary
    outputfile=mkstemp('_tempModelkit'+'.idf')[1]
    print("Creating Modelkit temp output file: {}".format(outputfile))
    #write_file(data, tempfnm)

    cmd='{ruby} {modelkit} template-compose --output {output} --dirs {mktemp}  {root}'.format(ruby=ruby_cmd, modelkit=mk_bin, output=outputfile, mktemp=template_dirs, root=root )
    print('> '+cmd)
    write_log("**CMD**: `{}'".format(cmd))

    # Quality assurance
    write_log("**QA**: #lines in root template: {} ({})".format( _count_lines(root), root ))

    call_output=_mycall(cmd)
    #call_output=call(cmd, shell=True)
    #call_output=check_call(cmd, shell=True)
    write_log("**QA**: `modelkit' subprocess returned `{}'".format(call_output) )

    # QA continued... post cmd execution
    write_log("**QA**: #lines in Modelkit output (b4 dos2unix): {}".format( _count_lines(outputfile), outputfile ))

    if which('dos2unix'):
        print('>Converting modelkit output to Unix file extensions')
        #call('dos2unix {}'.format( outputfile ), shell=True)
        call( ['dos2unix', outputfile] )
        # QA continued... post unix2dos execution
        write_log("**QA**: `dos2unix' in PATH. #lines in Modelkit output (post dos2unix): {}".format( _count_lines(outputfile), outputfile ))
    else:
        write_log("**QA**: `dos2unix' in not found PATH")

    if isfile(outputfile) and _count_lines(outputfile)>0 :
        print(">Modelkit was successful")
        write_log("**QA**: `modelkit' was sucessful")
        return outputfile
    elif isfile(outputfile) and _count_lines(outputfile)==0 :
        print(">Modelkit was NOT successful. Output file created but with NO content.")
        write_log("**QA**: `modelkit' was NOT sucessful. ZERO lines created in `{}'".format(outputfile) )
        #system( cmd ) # Try again
        #write_log("**QA**: TRY AGAIN #lines in Modelkit output: {}".format( _count_lines(outputfile), outputfile ))
        return outputfile
    else:
        print(">Modelkit failed")
        write_log("**QA**: `modelkit' FAILED")
        #return None
        raise ValueError("Modelkit"+data)


    return False

temp_interface="""<%#INTERFACE

modelkit_version "~>${version}"

${parameters}
%>
"""

temp_wrapper="""
<%
require("modelkit/energyplus")
require("modelkit/envelope")
%>

<%
insert "${input_idf}"

${zones_info}

zone_names = []

${iterzones}

${imf_systems}
%>
"""

temp_overzones="""
for zone in zones
  zone_name = zone[0]
  zone_sys = zone[1]
  zone_names << zone_name

  ${imf_zones}

end
"""


def dispatch_Modelkit(objs_all, args={}):
    """"Apply provided Modelkit instruction set using Modelkit commandline to genEPJ style object list. Convert back into genEPJ format and return modified object list.

    Parameters:

    * `objs_all`: genEPJ object list (Python `List`)
    * `args`: `template`-  A Modelkit instruction set (either a iterable or non-iterable payload). Build root.imf file and apply instruction set to file

    Returns:

    * `new_objs`: Modified genEPJ object list (Python `List`) using provided Modelkit information.
    """
    "Workflow to merge genEPJ and ModelKit toolkits together."

    write_log("**Flow**: Entering `dispatch_Modelkit' function")
    #if 'peak_use' in args:
    #    base_DHW_use=float(args['peak_use'])*frac

    # Convert objs_all into genEPJ.pxt
    genEPJ_file=mkstemp('_genEPJ'+'.pxt')[1]
    print("> Writing objs_all to '{}'".format(genEPJ_file))
    genEPJ_data=combine_objects(objs_all)
    with open(genEPJ_file, 'w') as f:
        f.write(genEPJ_data)
    write_log("**Flow**: Created IDF input file: {}".format(genEPJ_file))

    payload=args['template']
    zone_payload=[ pl for pl in payload if 'iterable' in str(pl)]
    system_payload=[ pl for pl in payload if 'iterable' not in str(pl)]
    write_log("**Flow**: payload loads from genEPJ: `{}'".format( str(payload) ))
    #print(zone_payload)
    #print(system_payload)

    # TODO- add tests to ensure this name is reasonable and warn the end user that order is very important
    try:
        system_name=system_payload[0][1]['defaults']['system_name'].replace('"','') # Assume system info is in first entry
    except:
        system_name="Ideal"

    zonenames=[ get_obj_abstract(obj,1) for obj in objs_all if get_obj_abstract(obj,0) == 'Zone' ]
    print("TESTING- All Zone names: {}".format( str(zonenames) ))
    zones_exclude = [ pl[1]["iter_exclude"] for pl in zone_payload ]
    zones_exclude = [ nm for y in zones_exclude for nm in y ]
    write_log("**Flow**: zone names loaded from genEPJ: `{}'".format( str( [nm for nm in zonenames if nm not in zones_exclude] )) )

    zones_templ = [ [ nm, system_name ] for nm in zonenames if nm not in zones_exclude ] # Requires names to match exactly. Use is_in if you want partial matches

    #---------------------
    # Create root template
    #---------------------
    #parameter "building_name", :default=>"Example Building"

    root_template=mkstemp('_ModelkitROOT'+'.pxt')[1]
    write_log("**Flow**: Created name for ROOT template file: {}".format(root_template))

    # Sub into Interface (Parameters and genEPJ source)
    #_join_parameter= lambda x,y: 'parameter "{}", :default=>"{}"'.format(x,y)
    join_parameters="" # iterate and join parameters
    _data={ "version": modelkit_version,
            "parameters": join_parameters,
          }
    temp=Template(temp_interface)
    temp_top=temp.safe_substitute( _data )
    #print(temp_top)

    _join_insert= lambda x,y: 'insert "{}", {}'.format(x,y)
    #def _join_insert(imf_file, defaults):
    #    if len( defaults) >0 :
    #        return 'insert "{}", {}'.format(imf_file,defaults)
    #    else:
    #        return 'insert "{}"'.format(imf_file,defaults)
    _join_values=lambda x,y: ':{}=>{}'.format(x,y)
    def merge_defs_extras(mydict):
        mylist=[]
        dictdefs=mydict["defaults"]
        for k,v in dictdefs.items():
            mylist.append( _join_values(k,v) )

        #if mylist:
        #    defs_join= ", ".join(mylist)
        #else:
        #    defs_join= "".join(mylist)
        defs_join= ", ".join(mylist)

        # Add extra_instructions (if any)
        if 'extra_instructions' in mydict.keys():
            defs_join = defs_join + "\n" + "\n".join( mydict['extra_instructions'] )
        return defs_join

    # Join zone subs
    zone_defs = [ merge_defs_extras( pl[1] ) for pl in zone_payload ]  # iteration over each zone.imf defaults
    zone_templ = [ _join_insert(pl[0], zone_defs[i])   for i,pl in enumerate( zone_payload ) ]  # iteration over each zone.imf object, merge defaults
    zone_join="\n".join(zone_templ)  # Join zone.imf using newline
    _data={ "imf_zones": zone_join,
          }
    temp=Template(temp_overzones) # zone Template object
    temp_mid=temp.safe_substitute( _data )
    #print(temp_mid)

    # Join system subs
    systems_defs = [ merge_defs_extras( pl[1] ) for pl in system_payload ]  # iteration over each system.imf defaults
    systems_templ = [ _join_insert(pl[0], systems_defs[i]) for i,pl in enumerate( system_payload ) ]  # iteration over each system.imf object, merge defaults
    systems_join="\n".join(systems_templ)  # Join system.imf using newline


    # Sub into wrapper template
    _data={ "input_idf": genEPJ_file,
            "zones_info": "zones = "+str(zones_templ),
            "iterzones":  temp_mid,
            "imf_systems": systems_join,
          }
    temp=Template(temp_wrapper)
    temp_bottom=temp.safe_substitute( _data )
    #print(temp_bottom)

    # Join all above templates and save to root_template file
    with open(root_template, 'w') as f:
        f.write( temp_top + "\n\n" + temp_bottom )

    write_log("**QA**: #lines in input IDF: {} ({})".format( _count_lines(genEPJ_file), genEPJ_file ))
    write_log("**Flow**: Created content ROOT template file: {}".format(root_template))

    write_log("**Flow**: Running Modelkit now from directory: {}".format( getcwd() ))
    outputfile= run_modelkit(root=root_template)

    write_log("**Flow**: Reloading IDF objs post Modelkit from `{}'".format(outputfile) )
    new_objs=get_IDF_objs_raw(outputfile)

    write_log("**Flow**: `dispatch_Modelkit' ran successfully")
    return new_objs

# Data that is passed to this wrapper:
# * .imf list with default overrides and iterate flag set

# Steps:
## Save new_objs as IDF
## Create ModelKit root file (PXT)
### insert each supplied .imf either globally or in for loop over zones
## run ModelKit: Creating IDF
## run dos2unix (if necessary)
## Finally, reload back as new_objs and return

## Once it is working your can reverse engineering using extract_HVAC.py and have fresh JSON templates ready to go!

# Finally, close log file
#f.close()

if __name__ == '__main__':
    pass
    #run_modelkit(1)
    #dispatch_Modelkit([],{})
    print(template_dirs)
