#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Apply a user-supplied genEPJ function to an EnergyPlus IDF file.

Example:
    ./apply_function.py FUNCNAME MYBLDG.idf
"""

from os.path import isfile
from sys import argv, path

path.append("genEPJ")
path.append("../genEPJ")

import generate_EPJ as genEPJ


def _parse_args(arg_string):
    """Parse a simple command-line argument dictionary string."""
    cleaned = arg_string.replace("{", "").replace("}", "")
    parsed = {}
    for item in cleaned.split(","):
        key = item.split(":")[0].strip(" '\"")
        val = item.split(":")[1].strip(" '\"")
        parsed[key] = val
    return parsed


if __name__ == "__main__":
    usage_str = "\nUsage: apply_function.py genEPJFN_file FILENAME_prep.idf"
    objs = []

    if len(argv) == 1:
        print(usage_str)
    elif len(argv) == 3:
        _file = argv[2]
        _func_str = argv[1]
        _func = getattr(genEPJ, _func_str)

        if callable(_func) and isfile(_file):
            print("apply_function.py " + _func_str + ", args: " + str(argv))
            _func(_file)
        else:
            print("\nEither FN not defined or FILE doesn't exist")
            print(usage_str)
    elif len(argv) == 4:
        _file = argv[2]
        _func_str = argv[1]

        if "_file" in _func_str:
            raise ValueError(
                "Arguments cannot be passed to genEPJ via `*_file` function "
                "calls. Use the genEPJ function directly and modify the "
                "object to accommodate a file as well as genEPJ lists."
            )

        _func = getattr(genEPJ, _func_str)
        str_args = argv[3]
        _args = _parse_args(str_args)

        print(
            "Using the following arguments: '%s' (supplied with '%s')"
            % (str(_args), str_args)
        )
        print(
            "NOTE: genEPJ directly MUST be called directly and modified "
            "object referenced as `list(get_IDF_objs_raw(objs))`"
        )

        if callable(_func) and isfile(_file):
            objs = _func(_file, args=_args)
        else:
            print("\nEither FN not defined or FILE doesn't exist")
            print(usage_str)
    else:
        print("Need to supply FN and FILE")

    if len(argv) >= 3:
        suffix = _func_str.replace("_", "")
        newfile = _file.replace(".", "_%s." % suffix)
        genEPJ.write_file(objs, newfile)
