#!/usr/bin/env python3

"""Utilities for applying substitutions to epJSON templates.

This module loads an epJSON template schema, extracts default and
required fields for EnergyPlus objects, and applies user-provided
values to JSON-compatible templates.
"""

import json
import re
from os.path import isfile

try:
    from genEPJ.resources import epjson_template_path
except ImportError:  # pragma: no cover - legacy script execution
    epjson_template_path = None


def load_json_template(myfname):
    """Load a JSON template file and return a Python object."""
    with open(myfname) as f:
        objs = json.load(f)
    return objs


def _default_template_path():
    """Locate the default epJSON template without using fragile paths."""
    if epjson_template_path is not None:
        return epjson_template_path()

    candidates = (
        "genEPJ/templateGenerator_epJSON/templates_9.0.1.json",
        "templateGenerator_epJSON/templates_9.0.1.json",
        "templates_9.0.1.json",
    )
    for candidate in candidates:
        if isfile(candidate):
            return candidate
    raise FileNotFoundError(
        "Required epJSON template file was not found. Expected "
        "templates_9.0.1.json to be packaged under "
        "genEPJ/templateGenerator_epJSON/."
    )


json_temp_fname = str(_default_template_path())
json_temp = load_json_template(json_temp_fname)

textColors = {
    'blue': '\033[94m',
    'green': '\033[92m',
    'black': '\033[95m',
    'yellow': '\033[93m',
    'red': '\033[91m',
    'default': '\033[0m',
}


def get_template_defaults_required(eplus_key):
    """Extract template, defaults, and required fields for an epJSON key."""
    template = {}
    defaults = {}
    required = {}

    def _try2index(myjson, val):
        try:
            key = list(myjson.keys())[0]
            return myjson[key][val]
        except Exception:
            return ''

    if eplus_key not in list(json_temp.keys()) and isfile(eplus_key):
        json_obj = load_json_template(eplus_key)
        defaults = _try2index(json_obj, 'defaults')
        template = _try2index(json_obj, 'template')
        required = _try2index(json_obj, 'required')
    elif eplus_key not in list(json_temp.keys()) and not isfile(eplus_key):
        fake_root = eplus_key.split(':')[0]
        match_keys = [_k for _k in json_temp.keys() if fake_root + ":" in _k]
        fake_key = match_keys[0]
        msg = (
            "> Given a fallback key for multiple E+ object entries '%s'. "
            "Using root '%s' and matching to the epJSON schema. "
            "Matched: '%s'."
        ) % (eplus_key, fake_root, fake_key)
        printc(msg, 'yellow')
        printc("> Other possible matches: '%s'" % (match_keys), 'red')
        defaults = json_temp[fake_key]['defaults']
        template = json_temp[fake_key]['template']
        required = json_temp[fake_key]['required']
    else:
        defaults = json_temp[eplus_key]['defaults']
        template = json_temp[eplus_key]['template']
        required = json_temp[eplus_key]['required']

    return template, defaults, required


class Verbose(object):
    """Manage the verbose print state used by the templater."""

    def __init__(self):
        self.verbose = False

    def verbose_toggle(self):
        """Toggle the verbose flag."""
        self.verbose = not self.verbose

    def verbose_set(self, verb):
        """Set the verbose flag to ``verb``."""
        self.verbose = verb


verbose = Verbose()

template_var_re = re.compile(r'\${(\w+)}')


def printc(s, color='default'):
    """Print a string using the provided terminal color."""
    print(textColors[color] + '  TEMPLATER:' + str(s) + textColors['default'])


def ifprintc(s, color='default'):
    """Print substitution details when verbose mode is enabled."""
    if verbose.verbose:
        print(printc(s, color))


def template_dict(temp_dict, sub_dict):
    """Substitute values from ``sub_dict`` into ``temp_dict``."""
    new_dict = dict(temp_dict)
    for key in temp_dict.keys():
        new_dict[key] = temp_dict[key] % sub_dict
    return new_dict


# The templater is iterated twice over a template using different payloads:
# user values first, then default values.
def update_json(template, payload):
    """Update a JSON template using the supplied payload."""
    new_template = dict(template)
    templ_values_not_subbed = template_var_re.findall(str(template))
    is_schedule = "'data': [" in str(template)

    if not is_schedule:
        for key in payload.keys():
            if key in templ_values_not_subbed:
                new_template[key] = payload[key]
    else:
        take_first_key = lambda mydict: list(mydict.keys())[0]
        templ_key = take_first_key(template)
        i = 0
        for field_dict in template[templ_key]['data']:
            if template_var_re.match(field_dict['field']):
                sub_key = template_var_re.findall(field_dict['field'])[0]
                new_template[templ_key]['data'][i]['field'] = payload[sub_key]
            i = i + 1
    return new_template


def templater(
    values,
    template,
    defaults={},
    required={},
    templ_epkey='',
    IGNORE_ERRORS=True,
):
    """Apply user values and defaults to a JSON-compatible template."""
    if not templ_epkey:
        try:
            templ_epkey = [
                key for key in json_temp.keys()
                if (
                    json_temp[key]['template'] == template and
                    json_temp[key]['defaults'] == defaults
                )
            ]
            ifprintc(
                "Found compatible E+ template keys: '%s'" % (str(templ_epkey)),
                'green',
            )
        except Exception:
            templ_epkey = None

    def sub_it(templ, mydict, default=""):
        new_templ = dict(templ)
        if len(mydict) > 0:
            new_templ = update_json(templ, mydict)
        return new_templ

    template = sub_it(template, values, default="USER")
    template = sub_it(template, defaults, default="DEFAULT")

    try:
        templ_name = json_temp[templ_epkey]['name']
    except Exception:
        templ_name = None

    missing_vars = template_var_re.findall(str(template))
    req_vars = list(set().union(required, missing_vars))
    if not templ_epkey:
        templ_epkey = 'CustomUserTemplate'
    if any(req_vars) and not IGNORE_ERRORS:
        raise KeyError(
            "ERROR: E+ required variables not specfied '%s' in Template: "
            "'%s' with name '%s'" % (req_vars, templ_epkey, templ_name)
        )

    err_vars = template_var_re.findall(str(template))
    if any(err_vars) and not IGNORE_ERRORS:
        raise KeyError(
            "ERROR: Variables not substituted: '%s' in Template: '%s' "
            "with name '%s'" % (req_vars, templ_epkey, templ_name)
        )

    return template


if __name__ == '__main__':
    print("Testing: template1")

    values1 = {"key1": 1, "key2": 2}
    defaults1 = {"key3": 3}
    template1 = {"key1": '${key1}', "key2": '${key2}', "key3": '${key3}'}
    print(template1)
    new_template1 = templater(values1, template1, defaults1)
    ifprintc(new_template1, 'blue')
    print(new_template1)

    print("\nTesting: template2")
    template2, defaults2, required2 = get_template_defaults_required('Building')
    print(template2)
    values2 = {'name': 'GreatOne'}
    new_template2 = templater(values2, template2, defaults2)
    ifprintc(new_template2, 'blue')
    print(new_template2)

    print("\nTesting: template3")
    template3, defaults3, required3 = get_template_defaults_required(
        'Schedule:Compact'
    )
    print(template3)
    values3 = {
        'name': 'Bob Schedule',
        'schedule_type_limits_name': 'Temperature',
    }
    new_template3 = templater(values3, template3, defaults3)
    ifprintc(new_template3, 'blue')
    print(new_template3)
