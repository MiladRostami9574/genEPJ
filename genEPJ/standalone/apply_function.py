#!/usr/bin/env python
# -*- coding: utf-8 -*-
"Apply a user-supplied genEPJ function to the provided E+ IDF: `./apply_function.py FUNCNAME MYBLDG.idf`"

from sys import platform, path, argv# win/linux?
from os.path import isfile, isdir, join
import os.path

path.append('genEPJ')
path.append('../genEPJ')
#from generate_EPJ import *
import generate_EPJ as genEPJ

# Set to nothing for now
objs=[]

# TODO- take args as third command line option
if __name__ == '__main__':

    usage_str="\nUsage: apply_function.py genEPJFN_file FILENAME_prep.idf"
    if len(argv)==1 :
            print(usage_str)
    elif len(argv)==3 :
        _file=argv[2]
        _func_str=argv[1]
        _func = getattr(genEPJ, _func_str)
        if callable(_func) and isfile(_file):
            print("apply_function.py "+ _func_str + ", args: " + str(argv))
            _func(_file)
        else:
            print("\nEither FN not defined or FILE doesn't exist")
            print(usage_str)
    elif len(argv)==4 :
        _file=argv[2]
        _func_str=argv[1]
        if '_file' in _func_str: raise ValueError("Arguements cannot be passed to genEPJ via `*_file' function calls. Use genEPJ function directly and modify object to accomodate a file as well as genEPJ lists.")
        _func = getattr(genEPJ, _func_str)
        str_args=argv[3]
        str_args=str_args.replace('{','').replace('}','')
        _args={}
        for _arg in str_args.split(',') :
            key=_arg.split(':')[0].strip(" '\"") #strip removes all supplied characters from string
            val=_arg.split(':')[1].strip(" '\"")
            _args[key]=val
        print("Using the following arguements: '%s' (supplied with '%s')"%(str(_args), str_args))
        print("NOTE: genEPJ directly MUST be called directly and modified object referenced as `list(get_IDF_objs_raw(objs))'")
        if callable(_func) and isfile(_file):
            objs=_func(_file, args=_args)
        else:
            print("\nEither FN not defined or FILE doesn't exist")
            print(usage_str)
    else:
        print("Need to supply FN and FILE")
    suffix=_func_str.replace("_","")
    newfile=_file.replace(".","_%s."%( suffix ))
    fname=genEPJ.write_file(objs, newfile)
