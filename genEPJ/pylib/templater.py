#!/usr/bin/env python3
"Template engine for genEPJ (IDF format only)."

import re
from string import Template # Allows for substitutions using {}

#=============================
## NOTEs on the implementation
#=============================
# * Assumes numbers are already formatted to strings
# * Will override templated defaults if a conflicting values is provided (intentional)

textColors = {
    'blue' : '\033[94m',
    'green' : '\033[92m',
    'black': '\033[95m',
    'yellow': '\033[93m',
    'red': '\033[91m',
    'default': '\033[0m',
    }

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


def ifprintc(s,color='default'):
    "Print substitution details if verbose flag is set."
    if verbose.verbose:
        print(textColors[color] + '  TEMPLATER:'+s + textColors['default'])

def template_dict(temp_dict, sub_dict):
    """Attempt to sub given values in sub_dict into temp_dict"""
    d=dict( temp_dict )
    for k in temp_dict.keys():
        d[k] = temp_dict[k]%sub_dict
        # TESTING statements
        #print("\nAttempted substitution of string: %s"%(temp_dict[k]) )
        #print("Resulting substitution: %s"%( d[k]) )
    return d

def templater(values, template, defaults={}, IGNORE_ERRORS=False):
    """Templater takes a {map} of values and applies them to a string template"""

    templ_values=template_var_re.findall( template.template )

    try:
        templ_name=template.template.split('\n')[1].strip(' ')
    except:
        templ_name="CLASSLESS"

    def sub_it(templ, mydict, default=""):
        #ifprintc( "Variables substituted: '%s' in Template: '%s'"%(mydict.keys()[0], templ_name ), 'blue' )
        ifprintc( "%s Variables substituted: '%s' with value: '%s' in Template: '%s'"%(default, list(mydict.keys())[0], list(mydict.values())[0], templ_name ), 'blue' )
        return Template(templ.safe_substitute( mydict )) # Safe: wont raise KeyError

    #=================================================
    # Values in template but not in vals. USE DEFAULTS
    #=================================================
    # defaults to substitute: Match template AND not provided
    temp_not_vals=[tv for tv in templ_values for k in defaults.keys() if ( (k==tv) and (k not in values.keys()) )]
    #print("TEMP NOT VALS: ", temp_not_vals)
    # Lack variable in the template, attempt to use defaults
    if temp_not_vals:
        ifprintc( "DEFAULTS WARNING: Values specified by defaults and not provided: %s"%(temp_not_vals), 'yellow' )
    for t in temp_not_vals:
        # Attempt to apply defaults
        try:
            if ( any( temp_not_vals ) and ( defaults[t]!=None ) ): # SB 'defaults[t]!=None' matches "" which we want
                d={t: defaults[t]}
                # Needs to be a Template object, can't iterate over a string
                template=sub_it(template, d, default="DEFAULT" )
        except:
            pass

    #=======================================
    # Main loop for checks and substitutions
    #=======================================
    for k,v in values.items():

        # dict used for substitutions
        d={k: v}

        # Check for missing variable in template
        # OK if missing, just throw a warning
        if "${%s}"%(k) not in template.template:
            ifprintc("PROVIDED WARNING: Var: '{0}' not found in template '{1}'".format(k, templ_name), 'red')
        elif "${%s}"%(k) in template.template:
            ifprintc("PROVIDED Var: '{0}' found in template '{1}'".format(k, templ_name), 'green')
            # Substitute variable
            # Needs to be a Template object, can't iterate over a string
            template=sub_it(template, d )


    #===========================
    # Were any variables missed?
    #===========================
    err_vars=template_var_re.findall( template.template )
    if any( err_vars ) and not IGNORE_ERRORS:
        raise KeyError("ERROR: Variables not substituted: '%s' in Template: '%s'"%(err_vars, templ_name ) )

    return template.template

if __name__ == '__main__':

    print("Testing")
    verbose.verbose_set(True)

    vals1={"one": 1, "two": 2}
    defs1={"three": 3}
    temp1=Template("Template1,\n  I will test: ${one},\n  till you fail: ${two};")
    #temp1=Template("Template1,\n  I will test: ${one},\n  till you fail: ${two},\n  or I go with you: ${three};")
    print( temp1.template +'\n')

    ifprintc( templater( vals1, temp1, defs1 ), 'blue')

