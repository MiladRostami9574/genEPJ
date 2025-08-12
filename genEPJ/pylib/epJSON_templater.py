#!/usr/bin/env python2

# SB TODO- Fri Jan  4 20:00:36 EST 2019
# * still some confusion around variables with no defaults and not in 'required' list: Can I simply omit them from the template
# * If so, the template should be post-processed to drop unnecessary values. See marker '*****'

import re
from string import Template # Allows for substitutions using {}

import json
from collections import OrderedDict #Maintain order of modfied JSON to same as source JSON

from os.path import isfile, isdir, join, getsize, basename, splitext, dirname

## Testing of dispatch_JSON function with templates
#import sys
#print(sys.path)
#sys.path.append('../../eplus_epJSON/')
#print(isdir('../eplus_epJSON/'))
#print(sys.path)
#from generate_EPJ import *

# TODO- get_eplus_version. Load appropriate template.json. Create it if none exists and E+ installed
def load_json_template(myfname):
    "Load specified JSON template and return Python compatible JSON object."
    with open(myfname) as f:
        #objs = json.load(f, object_pairs_hook=OrderedDict) # Preserve order in original JSON (useful for later diffs)
        objs = json.load(f)
    return objs

from os.path import isfile
 #: SB: check for Schema under package directory
json_temp_fname="genEPJ/templateGenerator_epJSON/templates_9.0.1.json"
if not isfile(json_temp_fname): #: SB: Schema NOT FOUND. check for file under directory
    json_temp_fname="templateGenerator_epJSON/templates_9.0.1.json"
if not isfile(json_temp_fname): #: SB: Schema NOT FOUND. check in parent directory
    json_temp_fname="templates_9.0.1.json"
#json_temp_fname="templates_9.0.1.json"
json_temp = load_json_template(json_temp_fname)

textColors = {
    'blue' : '\033[94m',
    'green' : '\033[92m',
    'black': '\033[95m',
    'yellow': '\033[93m',
    'red': '\033[91m',
    'default': '\033[0m',
    }

def get_template_defaults_required(eplus_key):
    "Extract defaults for E+ key variable as per the JSON schema for the version of EnergyPlus in question."
    # TODO- tests for missing data
    #template=OrderedDict()
    #defaults=OrderedDict()
    #required=OrderedDict()
    template={}
    defaults={}
    required={}
    #print("Templ name/obj: %s"%( eplus_key))
    #print("TEST1 (ep_key NOT IN json keys... fname): %s"%( eplus_key not in list(json_temp.keys()) ))
    #print("TEST2 (ep_key is file): %s"%(isfile(eplus_key)))
    def _try2index(myjson,val):
        try:
            #_key=list( _json.keys() )[0]
            _key=list( myjson.keys() )[0]
            return myjson[_key][val]
        except:
            return ''
    if ( ( eplus_key not in list(json_temp.keys()) ) and isfile(eplus_key) ): #Filename, load json directly (personal template)
        _json=load_json_template(eplus_key)
        defaults=_try2index(_json, 'defaults')
        template=_try2index(_json, 'template')
        required=_try2index(_json, 'required')
    elif ( ( eplus_key not in list(json_temp.keys()) ) and not isfile(eplus_key) ): #Fake key, go one level deeper and try and index
        _fake_key= eplus_key.split(':')[0]
        match_keys= [_k for _k in json_temp.keys() if _fake_key+":" in _k]
        fake_key= match_keys[0]
        printc("> HACK: Given a fake key for multiple E+ object entries '%s'. Using root '%s' and matching to epJSON schema. Matched: '%s'. Fix this hack some day!"%(eplus_key, _fake_key, fake_key), 'yellow')
        printc("> HACK: Other possible matches: '%s'"%(match_keys), 'red')
        defaults=json_temp[fake_key]['defaults']
        template=json_temp[fake_key]['template']
        required=json_temp[fake_key]['required']
    else:
        defaults=json_temp[eplus_key]['defaults']
        template=json_temp[eplus_key]['template']
        required=json_temp[eplus_key]['required']
        #try: # SB: Added to allow for FakeTemplateNames in directives
        #    defaults=json_temp[eplus_key]['defaults']
        #    template=json_temp[eplus_key]['template']
        #    required=json_temp[eplus_key]['required']
        #except Exception:
        #    pass
    return template,defaults,required

# Class enables verbose print toggling outside of module
# OOP needed since we are dealing with state
class Verbose:
    "Class enables verbose print toggling outside of module. Manages the verbose print state flag."
    def __init__(self):
        self.verbose = False
    def verbose_toggle(self):
        "Toggle verbose flag"
        self.verbose = not self.verbose
    def verbose_set(self, verb):
        "Set verbose to `verb`"
        self.verbose = verb

verbose = Verbose()

template_var_re=re.compile(r'\${(\w+)}')


def printc(s,color='default'):
    "Print string `s` using `color`"
    print(textColors[color] + '  TEMPLATER:'+ str(s) + textColors['default'])

def ifprintc(s,color='default'):
    "Print substitution details if verbose flag is set."
    if verbose.verbose:
        print( printc(s, color) )

# SB: refactor ifprintc using lambda?
#print_OK = lambda x:      cprint (x, 'green', attrs=['bold'])  if show_OKs else None

# SB: used in genIDF2
def template_dict(temp_dict, sub_dict):
    """Attempt to sub given values in sub_dict into temp_dict"""
    d=dict( temp_dict )
    for k in temp_dict.keys():
        d[k] = temp_dict[k]%sub_dict
        # TESTING statements
        #print("\nAttempted substitution of string: %s"%(temp_dict[k]) )
        #print("Resulting substitution: %s"%( d[k]) )
    return d

# FN is iterated twice over template using different payloads:
# 1. USER VALUES:    using provided dict values
# 2. DEFAULT VALUES: using template defaults
def update_json(template,payload):
    "Update JSON `template` using dictionary `payload`."
    _template=dict(template) # make template immutable
    templ_values_not_subbed=template_var_re.findall( str(template) )
    is_schedule="'data': [" in str(template) # use 'field' keys for sub instead

    #iterate over payload, sub values only if not previously subbed
    if not is_schedule:
        for _k in payload.keys():
             if _k in templ_values_not_subbed:
                # Works for everything except Schedules
                _template[_k]=payload[_k]
    elif is_schedule:  # It's a schedule use 'field' keys instead
        _take_first_key=lambda mydict : list(mydict.keys())[0]
        templ_key=  _take_first_key(template)
        #print(templ_key)
        i=0
        for _fld_dict in template[templ_key]['data']:
             #print(_fld_dict)
             # sub if matches
             if template_var_re.match( _fld_dict['field'] ):
                sub_key=template_var_re.findall( _fld_dict['field'] )[0]
                _template[templ_key]['data'][i]['field']= payload[sub_key]
             i=i+1
    return _template

def templater(values, template, defaults={}, required={}, templ_epkey='', IGNORE_ERRORS=True):
    """Templater takes a {map} of values and applies them to a dictionary template"""

    templ_values=template.values()
    templ_keys  =template.keys()
    if not templ_epkey:
        try:
            templ_epkey = [_key  for _key in json_temp.keys() if ( (json_temp[_key]['template']==template) and (json_temp[_key]['defaults']==defaults) ) ]
            ifprintc("Found compatible E+ template keys: '%s'"%(str(templ_epkey)), 'green')
        except:
            templ_epkey = None

    def sub_it(templ, mydict, default=""):
        new_templ= dict(templ)
        if len(mydict)>0:
            #ifprintc( "E+ Template: '%s': %s Variables substituted: '%s' with value '%s'"%(templ_epkey, default, list(mydict.keys())[0], list(mydict.values())[0]), 'blue' )
            new_templ= update_json(templ,mydict)
        return new_templ

    template=sub_it(template, values, default="USER" )
    template=sub_it(template, defaults, default="DEFAULT" )

    # Get name of template (if any)
    try:
        templ_name = json_temp[templ_epkey]['name']
    except:
        templ_name = None

    #=======================================
    # Were ALL required variables specified?
    #=======================================
    missing_vars=template_var_re.findall( str(template) )
    req_vars=list(set().union(required, missing_vars ))
    if not templ_epkey: templ_epkey='CustomUserTemplate'
    if any( req_vars ) and not IGNORE_ERRORS:
        raise KeyError("ERROR: E+ required variables not specfied '%s' in Template: '%s' with name '%s'"%(req_vars, templ_epkey, templ_name ) )

    #=====================================================
    # Drop non-default, unspecified, unrequired parameters
    #=====================================================
    # SB- todo Fri Jan  4 20:02:41 EST 2019

    #===========================
    # Were any variables missed?
    #===========================
    err_vars=template_var_re.findall( str(template) )
    #if any( err_vars ):
    if any( err_vars ) and not IGNORE_ERRORS:
        raise KeyError("ERROR: Variables not substituted: '%s' in Template: '%s' with name '%s'"%(req_vars, templ_epkey, templ_name ) )

    #=============================================
    # Names provided but not used (not in template)
    #=============================================
    #TODO- Warning

    return template

if __name__ == '__main__':

    print("Testing: template1")
    #verbose.verbose_set(True)

    values1={"key1": 1, "key2": 2}
    defaults1={"key3": 3}
    template1={"key1": '${key1}', "key2": '${key2}', "key3": '${key3}'}
    print(template1)
    new_template1=templater( values1, template1, defaults1 )
    ifprintc( new_template1, 'blue')
    print(new_template1)

    ## SB: NOTE how I use to do templating in genIDF2
    #output_temp,output_defs=templ.template_output_control()
    #output_formatted=templater({}, output_temp, output_defs)

    print("\nTesting: template2")
    ## Real example of 'Building' object from E+. SHOULD fail as no 'name' is provided
    template2,defaults2,required2=get_template_defaults_required('Building')
    print(template2)
    values2={'name': 'GreatOne'}
    #values2={}
    new_template2=templater( values2, template2, defaults2 )
    ifprintc( new_template2, 'blue')
    print(new_template2)

    print("\nTesting: template3")
    template3,defaults3,required3=get_template_defaults_required('Schedule:Compact')
    print(template3)
    values3={'name': 'Bob Schedule', 'schedule_type_limits_name': 'Temperature'}
    new_template3=templater( values3, template3, defaults3 )
    ifprintc( new_template3, 'blue')
    print(new_template3)




